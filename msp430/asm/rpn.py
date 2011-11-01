#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Simple, extensible RPN calculator.
"""

from __future__ import division

import sys
import pprint
import codecs
import re
import logging

m_comment = re.compile('(#.*$)', re.UNICODE)    # regexp to remove line comments

class Word(unicode):
    """\
    Like a string but annotated with the position in the source file it was read from.
    """
    def __new__(cls, word, filename, lineno, text):
        self = unicode.__new__(cls, word)
        self.filename = filename
        self.lineno = lineno
        self.text = text
        return self

    #~ def __repr__(self):
        #~ return "%s(%s, %s, %s)" % (
                #~ self.__class__.__name__,
                #~ unicode.__repr__(self),
                #~ self.filename,
                #~ self.lineno)


def annotated_words(sequence, filename=None, lineno=None, offset=None, text=None):
    """Wrap words and annotate them with given filename etc."""
    for word in sequence:
        if isinstance(word, Word):
            yield word
        else:
            yield Word(word, filename, lineno, text)


def words_in_string(data, name='<string>', include_newline=False):
    """\
    Yield word for word of a string, with comments removed. Words are annotated
    with position in source string.
    """
    for n, line in enumerate(data.splitlines()):
        for word in m_comment.sub('', line).split():
            yield Word(word, name, n+1, line)
        if include_newline:
            yield Word('\n', name, n+1, line)

def words_in_file(filename, fileobj=None, include_newline=False):
    """\
    Yield word for word of a file, with comments removed. Words are annotated
    with position in source file.
    """
    if fileobj is None:
        fileobj = codecs.open(filename, 'r', 'utf-8')
    for n, line in enumerate(fileobj):
        for word in m_comment.sub('', line).split():
            yield Word(word, filename, n+1, line)
        if include_newline:
            yield Word('\n', filename, n+1, line)


class RPNError(Exception):
    """interpreter error"""
    def __init__(self, message, filename=None, lineno=None, column=None, offset=None, text=None):
        Exception.__init__(self, message)
        self.filename = filename or '<unknown>'
        self.lineno = lineno
        self.column = column
        self.offset = offset
        self.text = text

    #~ def __str__(self):
        #~ return '%s:%s: %s' % (self.filename, self.lineno, self.message)


def rpn_function(code):
    """wrapper command generator, used to inject RPN functions into the namespace"""
    def wrapper(stack):
        stack.interpret(code)
    return wrapper


def word(name):
    """\
    Function decorator used to tag methods that will be visible in the RPN
    builtin namespace.
    """
    def decorate_word(function):
        function.rpn_name = name.lower()
        return function
    return decorate_word


class RPNBase(list):
    """\
    Simple, extensible RPN calculator.
    It inherits from list which is used as stack.
    """
    def __init__(self, namespace=None):
        list.__init__(self)
        self.clear()
        self.namespace = namespace if namespace is not None else {}
        self._iterator = None
        self.builtins = {}
        # extend built-ins name space with all methods that were marked with
        # the @word decorator
        for name in dir(self):
            function = getattr(self, name)
            if hasattr(function, 'rpn_name'):
                self.builtins[function.rpn_name] = function

    def interpret_sequence(self, sequence, filename=None):
        """interpret a sequence of words"""
        self.interpret(annotated_words(sequence, filename))

    def interpret(self, iterator):
        """\
        Interpret a sequence of words given a 'next' function that get the
        next word from the sequence.
        """
        # keep old reference in case of nested calls
        old_iterator = self._iterator
        # store function to make it available to called functions
        self._iterator = iterator
        word = None # in case next_word raises an exception
        try:
            while True:
                word = iterator.next()
                self.interpret_word(word)
        except StopIteration:
            pass
        except RPNError:
            raise
        except Exception as e:
            filename = getattr(word, 'filename', '<unknown>')
            lineno = getattr(word, 'lineno', None)
            column = getattr(word, 'column', None)
            offset = getattr(word, 'offset', None)
            text = getattr(word, 'text', None)
            logging.getLogger('rpn').exception('%s:%s: Error in word "%s": %s' % (filename, lineno, word, e))
            raise RPNError('Error in word "%s": %s' % (word, e), filename, lineno, column, offset, text)
            # XXX consider showing the full traceback of the original exception
        finally:
            # restore state
            self._iterator = old_iterator

    def look_up(self, word):
        """Find the word in one of the namespaces and return the value"""
        lowercased_word = word.lower() # case insensitive
        for namespace in (self.namespace, self.builtins):
            try:
                element = namespace[lowercased_word]
            except KeyError:
                pass
            else:
                return element
        raise KeyError('%r not in any namespace' % (word,))

    def next_word(self):
        return self._iterator.next()

    def interpret_word(self, word):
        """\
        Interpret a single word. It may call self.next_word, so this has to
        be set up.
        """
        try:
            element = self.look_up(word)
        except KeyError:
            pass
        else:
            if callable(element):
                element(self)
            else:
                self.push(element)
            return
        # if it's not a symbol it might be a number
        try:
            try:
                self.push(int(word, 0))
            except ValueError:
                self.push(float(word))
        except ValueError:
            filename = getattr(word, 'filename', '<unknown>')
            lineno = getattr(word, 'lineno', None)
            column = getattr(word, 'column', None)
            offset = getattr(word, 'offset', None)
            text = getattr(word, 'text', None)
            raise RPNError("neither known symbol nor number: %r" % (word,), filename, lineno, column, offset, text)

    def push(self, obj):
        """Push an element on the stack"""
        self.append(obj)

    def pop(self):
        """Get an element from the stack"""
        try:
            return list.pop(self)
        except IndexError:
            raise IndexError("pop called on empty stack")

    def pop2(self):
        """Get two elements from the stack"""
        return self.pop(), self.pop()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def prettyprint(self, stack):
        pprint.pprint(self.pop())

    def __str__(self):
        """return a string describing the topmost elements from the stack"""
        if self:
            N = min(4, len(self))
            tops = ["%s:%s" % ("xyzt"[i], self.printer(self[-i-1])) for i in range(N)]
            if len(self) > 4:
                tops.append(' (%d more)' % (len(self)-4,))
            return ' '.join(tops)
        return "stack empty"

    def printer(self, obj):
        """convert object to string, for floating point numbers, use engineering format"""
        t = type(obj)
        if type(t) == float:
            e = int(math.log10(abs(obj)))
            e = int(e/3)*3
            if e:
                return "%ge%s" % ((obj/10**e), e)
            else:
                return "%g" % (obj)
        else:
            return repr(obj)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class RPNStackOps(object):
    """Mix-in class with words for stack operations"""

    @word("CLEAR")
    def clear(self, stack=None):
        """Clear stack."""
        del self[:]

    @word("DUP")
    def dup(self, stack):
        """Duplicate the topmost element on the stack."""
        self.push(self[-1])

    @word("DROP")
    def drop(self, stack):
        """Remove and forget about topmost element on the stack."""
        self.pop()

    @word("SWAP")
    def swap(self, stack):
        """Exchange the two topmost elements on the stack."""
        self[-1], self[-2] = self[-2], self[-1]

    @word("OVER")
    def over(self, stack):
        """Push a copy of the second element on the stack."""
        self.push(self[-2])

    @word("PICK")
    def pick(self, stack):
        """Push a copy of the N'th element on the stack."""
        self.push(self[-self.pop()])

class RPNSimpleMathOps(object):
    """Mix-in class with words for simple math operations"""

    @word("+")
    def add(self, stack):
        """Add two numbers on the stack."""
        x, y = self.pop2()
        self.push(y + x)

    @word("-")
    def sub(self, stack):
        """Subtract two numbers on the stack."""
        x, y = self.pop2()
        self.push(y - x)

    @word("*")
    def mul(self, stack):
        """Multiply two numbers on the stack."""
        x, y = self.pop2()
        self.push(y * x)

    @word("/")
    def div(self, stack):
        """Divide two numbers on the stack."""
        x, y = self.pop2()
        self.push(y / x)


class RPNMoreMathOps(object):
    """Mix-in class with words for more math operations"""

    @word("MIN")
    def minimum(self, stack):
        """Leave the smaller of two values on the stack."""
        x, y = self.pop2()
        self.push(min(y, x))

    @word("MAX")
    def maximum(self, stack):
        """Leave the larger of two values on the stack."""
        x, y = self.pop2()
        self.push(max(y, x))


    @word("INT")
    def word_INT(self, stack):
        """Convert TOS to an integer."""
        self.push(int(self.pop()))

    @word("FLOAT")
    def word_FLOAT(self, stack):
        """Convert TOS to a floating point number."""
        self.push(float(self.pop()))

    @word("NEG")
    def negate(self, stack):
        """Negate number on stack."""
        self.push(-self.pop())

class RPNBitOps(object):
    """Mix-in class with words for bit operations."""

    @word("|")
    def bitor(self, stack):
        """Bitwise OR of two numbers on the stack."""
        x, y = self.pop2()
        self.push(y | x)

    @word("&")
    def bitand(self, stack):
        """Bitwise AND of two numbers on the stack."""
        x, y = self.pop2()
        self.push(y & x)

    @word("^")
    def bitxor(self, stack):
        """Bitwise XOR of two numbers on the stack."""
        x, y = self.pop2()
        self.push(y ^ x)

    @word("<<")
    def bit_shift_left(self, stack):
        """Bitwise shift left."""
        x, y = self.pop2()
        self.push(y << x)

    @word(">>")
    def bit_shift_right(self, stack):
        """Bitwise shift right."""
        x, y = self.pop2()
        self.push(y >> x)

    @word("~")
    def bitnot(self, stack):
        """Bitwise invert of number on stack."""
        self.push(~self.pop())

class RPNLogicOps(object):
    """Mix-in class with words for Logic operations"""

    @word("NOT")
    def word_NOT(self, stack):
        """Logical NOT of number on stack"""
        self.push(not self.pop())

    @word("AND")
    def word_AND(self, stack):
        """Logical AND of two numbers on the stack"""
        x, y = self.pop2()
        self.push(bool(y and x))

    @word("OR")
    def word_OR(self, stack):
        """Logical OR of two numbers on the stack"""
        x, y = self.pop2()
        self.push(bool(y or x))

    @word("IFTE")
    def word_IFTE(self, stack):
        """\
        If then else for 3 values on the stack: predicate, value_true,
        value_false.
        """
        x, y = self.pop2()
        z = self.pop()
        if z:
            self.push(y)
        else:
            self.push(x)

    @word("LIST")
    def word_LIST(self, stack):
        """testing only: print all knwon words to stdout"""
        for namespace in (self.namespace, self.builtins):
            pprint.pprint(namespace)

class RPNCompareOps(object):
    """Mix-in class with words for comarisons"""

    @word("<")
    def smaller(self, stack):
        """Compare two numbers on the stack."""
        x, y = self.pop2()
        self.push(bool(y < x))

    @word("<=")
    def smaller_equal(self, stack):
        """Compare two numbers on the stack."""
        x, y = self.pop2()
        self.push(bool(y <= x))

    @word(">")
    def larger(self, stack):
        """Compare two numbers on the stack."""
        x, y = self.pop2()
        self.push(bool(y > x))

    @word(">=")
    def larger_equal(self, stack):
        """Compare two numbers on the stack."""
        x, y = self.pop2()
        self.push(bool(y >= x))

    @word("==")
    def equal(self, stack):
        """Compare two numbers on the stack."""
        x, y = self.pop2()
        self.push(bool(y == x))

    @word("!=")
    def not_equal(self, stack):
        """Compare two numbers on the stack."""
        x, y = self.pop2()
        self.push(bool(y != x))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# create a class with a typical set of operations
class RPN(RPNBase, RPNStackOps, RPNSimpleMathOps, RPNMoreMathOps,
          RPNBitOps, RPNLogicOps, RPNCompareOps):
    pass

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def eval(words, stack=[], namespace={}):
    """evaluate code with given stack and return the topmost object from the stack"""
    rpn = RPN(namespace)
    if stack is not None:
        for element in stack:
            rpn.push(element)
    rpn.interpret(iter(words))
    return rpn.pop()


def python_function(code, namespace={}):
    """wrapper command generator, used to wrap RPN and make it callable from python"""
    def wrapper(*args):
        return eval(code, args, namespace)
    return wrapper


def interpreter_loop(namespace={}, debug=False, rpn_class=RPN, rpn_instance=None):
    """run an interactive session"""
    if rpn_instance is None:
        rpn_instance = rpn_class(namespace)
    while True:
        try:
            print
            print rpn_instance
            words = raw_input('> ')
            rpn_instance.interpret_sequence(words.split(), filename='<stdin>')
        except KeyboardInterrupt:
            print
            break
        except SystemExit:
            raise
        except Exception, msg:
            if debug: raise
            print "ERROR:", msg


if __name__ == '__main__':
    import sys
    interpreter_loop(debug = '-d' in sys.argv)

