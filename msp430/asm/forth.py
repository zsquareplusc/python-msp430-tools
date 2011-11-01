#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Minimalistic Forth like language interpreter.

This module extends rpn.py with Forth like language features.

Its purpose is to process files in Forth syntax, provide an environment to
execute its functions.  Forth functions are stored in a way that allows to
cross compile them to MSP430 assembler code.  Native code functions are also
supported with "CODE ... END-CODE" but they are not executable on the host.

Cross compiling includes selection of only the used functions. The program on
the target does not provide a (interactive) Forth system (unless the user
program creates it).

XXX Currently under development - not all useful words are yet defined!
"""

import sys
import os
import codecs
import pkgutil
import logging
from msp430.asm import rpn


class DocumentTree(object):
    """\
    Maintain a list of chapters where each contains a list of sections.
    Track current section to write to. Data is buffered and sorted
    alphabetically when output.
    """

    def __init__(self):
        self._state = []
        # output is buffered in memory first. this allows to group commands and
        # to output in alphabetical order
        self.chapter_name = None
        self.chapters = {}
        self.current_chapter = None
        self.current_section = None
        self.chapter()    # create default chapter

    def chapter(self, name=' DEFAULT '):
        """Select chapter to put text sections in"""
        self.chapter_name = name
        self.current_chapter = self.chapters.setdefault(name, {})
        self.section(' TOPLEVEL ')

    def section(self, name):
        """Select name of text section to append output"""
        self.current_section = self.current_chapter.setdefault(name, [])

    def write(self, text):
        self.current_section.append(text)

    def push_state(self):
        self._state.append((self.chapter_name, self.current_chapter, self.current_section))

    def pop_state(self):
        self.chapter_name, self.current_chapter, self.current_section = self._state.pop()

    def render(self, output):
        """Write sorted list of text sections"""
        #~ # XXX document tree as info
        #~ for chapter_name, sections in sorted(self.chapters.items()):
            #~ print '"%s"' % chapter_name
            #~ for section_name, text in sorted(sections.items()):
                #~ print '    "%s"' % section_name
        for chapter_name, sections in sorted(self.chapters.items()):
            heder_not_yet_done = True
            for name, text in sorted(sections.items()):
                if text and heder_not_yet_done:
                    if chapter_name != ' DEFAULT ':
                        output.write(u'; %s\n' % ('='*75))
                        output.write(u'; == %s\n' % chapter_name)
                        output.write(u'; %s\n' % ('='*75))
                    heder_not_yet_done = False
                output.write(u''.join(text))


class ForthError(rpn.RPNError):
    pass


class SeekableIterator(object):
    """\
    An iterator with the additional functionality to adjust the read pointer
    while it is running. This is needed to implement jumps in
    Frame/NativeFrame.
    """
    def __init__(self, some_list):
        self.some_list = some_list
        self.position = 0

    def next(self):
        if self.position < len(self.some_list):
            item = self.some_list[self.position]
            self.position += 1
            return item
        raise StopIteration()

    def seek(self, difference):
        new_position = self.position + difference
        # allow positioning to size, one behind the last element
        # this is used if a branch/seek instruction wants to jump to the end of
        # the sequence
        if not 0 <= new_position <= len(self.some_list):
            raise ValueError('position not within size of sequence')
        self.position = new_position


class Frame(list):
    """Storage for function definitions"""

    def __init__(self, name):
        list.__init__(self)
        self.name = name
        self.use_ram = False

    def __call__(self, stack):
        """Execute code in frame"""
        iterable = SeekableIterator(self)
        old_iterator = stack._frame_iterator
        stack._frame_iterator = iterable
        try:
            while True:
                instruction = iterable.next()
                instruction(stack)
        except StopIteration:
            pass
        finally:
            stack._frame_iterator = old_iterator

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, self.name,)

class InterruptFrame(Frame):
    """\
    Interrupt frames are like normal Frames in most aspects but need different
    entry/exit code.
    """
    def __init__(self, name, vector):
        Frame.__init__(self, name)
        self.vector = vector


class NativeFrame(Frame):
    """\
    Storage for native function definitions. It is a separate class so that
    the objects can be identified.
    """


class Variable(object):
    """This emulates what on a target would be an address."""
    # typical variable usage: "HERE @". so the variable name would put the
    # address of the variable on the stack. The value of HERE is then also used
    # to write to (e.g. in the implementation of IF/ENDIF. As we don't not have
    # linear address space but frames for each dictionary entry that start
    # counting at zero, the value needs to remember the frame it belongs to.

    def __init__(self, frame, offset):
        self.frame = frame
        self.offset = offset

    def __add__(self, other):
        if isinstance(other, Variable):
            if self.frame is not other.frame: raise ValueError('Variables point to different frames')
            return Variable(self.frame, self.offset + other.offset)
        else:
            return Variable(self.frame, self.offset + other)

    def __sub__(self, other):
        if isinstance(other, Variable):
            if self.frame is not other.frame: raise ValueError('Variables point to different frames')
            return Variable(self.frame, self.offset - other.offset)
        else:
            return Variable(self.frame, self.offset - other)

    def set(self, value):
        self.frame[self.offset] = value

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.frame, self.offset)


def immediate(function):
    """\
    Function decorator used to tag Forth methods that will be executed
    immediately even when in compile mode.
    """
    function.forth_immediate = True
    return function



def immediate(function):
    """\
    Function decorator used to tag Forth methods that will be executed
    immediately even when in compile mode.
    """
    function.forth_immediate = True
    return function


class ForthBitOps(object):
    """Forth specific words for bit operations"""

    @rpn.word("OR")
    def bitor(self, stack):
        x, y = self.pop2()
        self.push(y | x)

    @rpn.word("AND")
    def bitand(self, stack):
        x, y = self.pop2()
        self.push(y & x)

    @rpn.word("XOR")
    def bitxor(self, stack):
        x, y = self.pop2()
        self.push(y ^ x)

    @rpn.word("LSHIFT")
    def bit_shift_left(self, stack):
        x, y = self.pop2()
        self.push(y << x)

    @rpn.word("RSHIFT")
    def bit_shift_right(self, stack):
        x, y = self.pop2()
        self.push(y >> x)

    @rpn.word("INVERT")
    def bitnot(self, stack):
        self.push(~self.pop())

    @rpn.word("2*")
    def arithmetic_shift_left(self, stack):
        self[-1] = self[-1]*2

    @rpn.word("2/")
    def arithmetic_shift_right(self, stack):
        self[-1] = self[-1]/2


class ForthMiscOps(object):
    """more Forth specific words"""

    @rpn.word("NOT")
    def word_NOT(self, stack):
        self.push(not self.pop())

    @rpn.word("1+")
    def plus_1(self, stack):
        self[-1] = self[-1] + 1

    @rpn.word("2+")
    def plus_2(self, stack):
        self[-1] = self[-1] + 2

    @rpn.word("4+")
    def plus_2(self, stack):
        self[-1] = self[-1] + 4

    @rpn.word("1-")
    def minus_1(self, stack):
        self[-1] = self[-1] - 1

    @rpn.word("2-")
    def minus_2(self, stack):
        self[-1] = self[-1] - 2

    @rpn.word("4-")
    def minus_2(self, stack):
        self[-1] = self[-1] - 4


    @rpn.word('/MOD')
    def word_divmod(self, stack):
        """Put quotient and reminder on stack."""
        a = stack.pop()
        b = stack.pop()
        d, m = divmod(a, b)
        stack.push(d)
        stack.push(m)

    @rpn.word('=')
    def word_equals1(self, stack):
        """Compare two numbers for equality"""
        a = stack.pop()
        b = stack.pop()
        stack.push(a == b)

    @rpn.word('0=')
    def word_is_zero(self, stack):
        """Check if number is not zero"""
        a = stack.pop()
        stack.push(a == 0)

    @rpn.word('0>')
    def word_is_positive(self, stack):
        """Check if number is positive"""
        a = stack.pop()
        stack.push(a > 0)

    @rpn.word('?DUP')
    def word_Qdup(self, stack):
        """DUP top of stack but only if not zero."""
        if stack[-1]:
            stack.push(stack[-1])

    @rpn.word('ROT')
    def word_is_rot(self, stack):
        """Rotate 3 items on the stack. 3rd gets 1st."""
        a = stack.pop()
        b = stack.pop()
        c = stack.pop()
        stack.push(b)
        stack.push(a)
        stack.push(c)

    @rpn.word('-ROT')
    def word_is_nrot(self, stack):
        """Rotate 3 items on the stack. 1st gets 3rd."""
        a = stack.pop()
        b = stack.pop()
        c = stack.pop()
        stack.push(a)
        stack.push(c)
        stack.push(b)


class Forth(rpn.RPNBase, rpn.RPNStackOps, rpn.RPNSimpleMathOps,
            rpn.RPNCompareOps, ForthBitOps, ForthMiscOps):
    """\
    Extension of the RPN calculator with Forth like language features.
    """
    def __init__(self, namespace=None):
        rpn.RPNBase.__init__(self, namespace)
        self.target_namespace = {}  # an other name space for target only objects
        self.compiling = False
        self.frame = None
        self.variables = {}
        self.include_path = []
        self.included_files = []
        self.compiled_words = set()
        self.not_yet_compiled_words = set()
        self._frame_iterator = None
        self.use_ram = False
        self.label_id = 0
        self.logger = logging.getLogger('forth')
        self.doctree = DocumentTree()

    def init(self):
        # load core language definitions from a forth file
        self._include('__init__.forth')


    def look_up(self, word):
        """Find the word in one of the name spaces for the host and return the value"""
        # target words are included w/ least priority. they must be available
        # so that compiling words on the host works
        lowercased_word = word.lower() # case insensitive
        for namespace in (self.namespace, self.builtins, self.target_namespace):
            try:
                element = namespace[lowercased_word]
            except KeyError:
                pass
            else:
                return element
        raise KeyError('%r not in any namespace (host)' % (word,))

    def look_up_target(self, word):
        """Find the word in one of the namespaces for the target and return the value"""
        # builtin namespace is not searched as it only includes words
        # implemented in python. target name space has priority over normal
        # space.
        lowercased_word = word.lower() # case insensitive
        for namespace in (self.target_namespace, self.namespace):
            try:
                element = namespace[lowercased_word]
            except KeyError:
                pass
            else:
                return element
        raise KeyError('%r not in any namespace (target)' % (word,))

    def create_label(self):
        """Create a new assembler label"""
        self.label_id += 1
        return '__lbl%s' % (self.label_id,)

    def create_asm_label(self, name):
        """\
        There are a number of symbols that are not allowed in assembler
        labels, translate to printable strings.
        """
        for t_in, t_out in (
                ('.', '_dot_'),
                ('-', '_dash_'),
                ('+', '_plus_'),
                ('*', '_star_'),
                ('?', '_qmark_'),
                ('/', '_slash_'),
                ('\\', '_backslash_'),
                ('|', '_or_'),
                ('&', '_and_'),
                ('@', '_fetch_'),
                ('[', '_open_bracket_'),
                (']', '_close_bracket_'),
                ('!', '_store_'),
                ('<', '_less_'),
                ('>', '_bigger_'),
                ('=', '_eq_'),
                ('NOT', '_NOT_'),
                ("'", '_tick_'),
        ):
            name = name.replace(t_in, t_out)
        return '_' + name

    def interpret_word(self, word):
        """Depending on mode a word is executed or compiled"""
        #~ print "XXX", word
        # newlines are in the steam to support \ comments, they are otherwise ignored
        if word == '\n':
            return
        try:
            element = self.look_up(word)
        except KeyError:
            pass
        else:
            if self.compiling and not hasattr(element, 'forth_immediate'):
                if callable(element):
                    self.frame.append(element)
                else:
                    self.frame.append(self.instruction_literal)
                    self.frame.append(element)
                return
            else:
                if callable(element):
                    element(self)
                else:
                    self.push(element)
                return
        # if it's not a symbol it might be a number
        try:
            number = int(word, 0)
        except ValueError:
            try:
                number = float(word)
            except ValueError:
                filename = getattr(word, 'filename', '<unknown>')
                lineno = getattr(word, 'lineno', None)
                column = getattr(word, 'column', None)
                offset = getattr(word, 'offset', None)
                text = getattr(word, 'text', None)
                raise ForthError("neither known symbol nor number: %r" % (word,), filename, lineno, column, offset, text)
        if self.compiling:
            self.frame.append(self.instruction_literal)
            self.frame.append(number)
        else:
            self.push(number)


    @rpn.word('@')
    def word_at(self, stack):
        reference = stack.pop()
        if isinstance(reference, Variable):
            stack.push(reference)
        else:
            raise ValueError('limited support for @: no compatible object on stack: %r' % (reference,))

    @rpn.word('!')
    def word_store(self, stack):
        reference = stack.pop()
        value = stack.pop()
        if isinstance(reference, Variable):
            if reference.frame != self.frame:
                raise ValueError('!: Frame mismatch for variable %r != %r' % (reference.frame, self.frame))
            if isinstance(value, Variable):
                reference.set(value.offset)
            else:
                reference.set(value)
        else:
            raise ValueError('limited support for !: no compatible object on stack %r' % (reference,))

    @rpn.word('HERE')
    def word_here(self, stack):
        """Put position [within frame] on stack"""
        stack.push(Variable(self.frame, len(self.frame)))



    @immediate
    @rpn.word("'")
    def word_tick(self, stack):
        """Push reference to next word on stack."""
        if self.frame is None: raise ValueError('not in colon definition')
        name = stack.next_word()
        self.frame.append(self.instruction_literal)
        self.frame.append(self.look_up(name))

    @immediate
    @rpn.word('CHAR')
    def word_char(self, stack):
        """Push ASCII code of next character."""
        name = stack.next_word()
        value = ord(name[0])
        stack.push(value)

    @immediate
    @rpn.word('[CHAR]')
    def word_compile_char(self, stack):
        """Compile ASCII code of next character."""
        name = stack.next_word()
        value = ord(name[0])
        if self.compiling:
            if self.frame is None: raise ValueError('not in colon definition')
            self.frame.append(self.instruction_literal)
            self.frame.append(value)
        else:
            raise ValueError('interpretation semantics undefined')

    @rpn.word(',')
    def word_coma(self, stack):
        """Append value from stack to current definition."""
        if self.frame is None: raise ValueError('not in colon definition')
        value = stack.pop()
        if isinstance(value, Variable):
            # XXX special case for calculations with HERE
            value = value.offset
        self.frame.append(value)

    @immediate
    @rpn.word(':')
    def word_colon(self, stack):
        """Begin defining a function. Example: ``: ADD-ONE 1 + ;``"""
        name = self.next_word()
        self.frame = Frame(name)
        self.frame.chapter = self.doctree.chapter_name
        self.compiling = True

    @immediate
    @rpn.word(';')
    def word_semicolon(self, stack):
        """End definition of function. See `:`_"""
        if self.frame is None: raise ValueError('not in colon definition')
        #~ print "defined", self.frame.name, self.frame     # XXX DEBUG
        self.namespace[self.frame.name.lower()] = self.frame
        self.frame = None
        self.compiling = False


    @immediate
    @rpn.word('CODE')
    def word_code(self, stack):
        """\
        Begin defining a native code function. CODE words are executed on the
        host to get cross compiled. Therefore they have to output assembler
        code for the target. Example::

            ( > Increment value on stack by one. )
            CODE 1+ ( n -- n )
                ." \\t inc 0(SP) \\n "
                ASM-NEXT
            END-CODE

        There is a number of supporting functions for outputting assembler.
        E.g. `ASM-NEXT`_, `ASM-DROP`_, `ASM-TOS->R15`_, `ASM-R15->TOS`_,
        `ASM-TOS->W`_, `ASM-W->TOS`_

        Note that the NEXT instruction is not automatically inserted and must be
        added manually (see `ASM-NEXT`_ in example above).
        """
        name = self.next_word()
        self.frame = NativeFrame(name)
        self.frame.chapter = self.doctree.chapter_name
        self.compiling = True

    @immediate
    @rpn.word('END-CODE')
    def word_end_code(self, stack):
        """End definition of a native code function. See CODE_."""
        if self.frame is None: raise ValueError('not in colon definition')
        #~ print "defined code", self.frame.name, self.frame     # XXX DEBUG
        self.target_namespace[self.frame.name.lower()] = self.frame
        self.frame = None
        self.compiling = False


    @immediate
    @rpn.word('INTERRUPT')
    def word_interrupt(self, stack):
        """\
        Begin defining an interrupt function. Example::

            PORT1_VECTOR INTERRUPT handler_name
                WAKEUP
                0 P1IFG C!
            END-INTERRUPT

        Words defined with ``INTERRUPT`` must not be called from user code.
        """
        name = self.next_word()
        vector = self.pop()
        self.frame = InterruptFrame(name, vector)
        self.compiling = True

    @immediate
    @rpn.word('END-INTERRUPT')
    def word_end_interrupt(self, stack):
        """End definition of a native code function. See INTERRUPT_ for example."""
        if self.frame is None: raise ValueError('not in colon definition')
        #~ print "defined code", self.frame.name, self.frame     # XXX DEBUG
        self.target_namespace[self.frame.name.lower()] = self.frame
        self.frame = None
        self.compiling = False



    @immediate
    @rpn.word('IMMEDIATE')
    def word_immediate(self, stack):
        """\
        Tag current function definition as immediate. This means that it is
        executed even during compilation.
        """
        if self.frame is None: raise ValueError('not in colon definition')
        self.frame.forth_immediate = True

    @immediate
    @rpn.word('[COMPILE]')
    def word_BcompileB(self, stack):
        """\
        Get next word, look it up and add it to the current frame (not
        executing immediate functions).
        """
        if self.frame is None: raise ValueError('not in colon definition')
        item = self.look_up(stack.next_word())
        self.frame.append(item)


    @immediate
    @rpn.word('[')
    def word_interpret(self, stack):
        """Change to interpretation mode."""
        self.compiling = False

    @immediate
    @rpn.word(']')
    def word_compile(self, stack):
        """Change to compilation mode."""
        self.compiling = True


    @rpn.word('LIT')
    def instruction_literal(self, stack):
        """Low level instruction to get a literal and push it on the stack."""
        stack.push(stack._frame_iterator.next())

    @rpn.word('BRANCH')
    def instruction_seek(self, stack):
        """Get offset from sequence and jump to this position."""
        difference = stack._frame_iterator.next()
        stack._frame_iterator.seek(difference - 1)

    @rpn.word('BRANCH0')
    def instruction_branch_if_false(self, stack):
        """\
        Get offset from sequence and a boolean from stack. Jump if boolean was
        false.
        """
        difference = stack._frame_iterator.next()
        if not stack.pop():
            stack._frame_iterator.seek(difference - 1)

    @immediate
    @rpn.word('RECURSE')
    def word_recurse(self, stack):
        """\
        Call currently defined word. This is used to write recursive functions.
        """
        if not self.compiling: raise ValueError('not allowed in immediate mode')
        if self.frame is None: raise ValueError('not in colon definition')
        # put conditional branch operation in sequence, remember position of offset on stack
        self.frame.append(self.instruction_branch_if_false)
        self.push(len(self.frame))
        self.frame.append(0)


    @rpn.word('WORD')
    def word_word(self, stack):
        """Read next word from the source and put it on the stack."""
        stack.push(stack.next_word())

    @rpn.word('.')
    def word_dot(self, stack):
        """Output element on stack."""
        self.doctree.write(unicode(stack.pop()))

    @rpn.word('EMIT')
    def word_emit(self, stack):
        """Output number on stack as Unicode character."""
        self.doctree.write(unichr(stack.pop()))

    @rpn.word('VARIABLE')
    def word_variable(self, stack):
        """\
        Allocate a variable. Creates space in RAM and an address getter
        function.
        """
        name = stack.next_word()
        # allocate separate memory for the variable
        # (cross compiled to RAM)
        self.variables[name] = Frame('var'+name)
        self.variables[name].append(0)
        # create a function that pushes the variables address
        frame = Frame(name)
        frame.chapter = self.doctree.chapter_name
        frame.append(self.instruction_literal)
        frame.append(self.variables[name])
        self.namespace[name.lower()] = frame
        # XXX could also do a native impl with "push #adr;NEXT"

    @rpn.word('VALUE')
    def word_value(self, stack):
        """\
        Allocate a variable. Creates space in RAM and a value getter
        function.

        Example::

            0 VALUE X
            X       \ -> puts 0 on stack
            5 X TO
            X       \ -> puts 5 on stack
        """
        value = stack.pop()
        name = stack.next_word()
        # allocate separate memory for the variable
        # (cross compiled to RAM)
        self.variables[name] = Frame('val'+name)
        self.variables[name].append(value)
        # create a function that pushes the variables address
        frame = Frame(name)
        frame.chapter = self.doctree.chapter_name
        frame.append(self.instruction_literal)
        frame.append(self.variables[name])
        frame.append(self.look_up('@'))
        self.namespace[name.lower()] = frame

    @immediate
    @rpn.word('TO')
    def word_to(self, stack):
        """Write to a VALUE_. Example: ``123 SOMEVALUE TO``"""
        name = stack.next_word()
        if self.compiling:
            self.frame.append(self.instruction_literal)
            self.frame.append(self.variables[name])
            self.frame.append(self.look_up('!'))
        else:
            value = stack.pop()
            self.variables[name][0] = value # XXX

    @rpn.word('RAM')
    def word_ram(self, stack):
        """Select RAM as target for following CREATE_ calls."""
        self.use_ram = True

    @rpn.word('ROM')
    def word_rom(self, stack):
        """Select ROM/Flash as target for following CREATE_ calls."""
        self.use_ram = False

    @rpn.word('CREATE')
    def word_create(self, stack):
        """Create a frame, typically used for variables."""
        name = stack.next_word()
        # allocate separate memory
        # (cross compiled to RAM)
        self.variables[name] = Frame('cre'+name)
        self.variables[name].use_ram = self.use_ram
        self.frame = self.variables[name]
        # create a function that pushes the variables address
        frame = Frame(name)
        frame.chapter = self.doctree.chapter_name
        frame.append(self.instruction_literal)
        frame.append(self.variables[name])
        self.namespace[name.lower()] = frame
        # XXX could also do a native impl with "push #adr;NEXT"

    @rpn.word('ALLOT')
    def word_allot(self, stack):
        """Allocate memory in RAM or ROM."""
        count = stack.pop()
        if count > 0:
            if count & 1: raise ValueError('odd sizes currently not supported')
            self.frame.extend([0]*(count/2))
        else:
            raise ValueError('negative ALLOT not supported')

    @rpn.word('CONSTANT')
    def word_constant(self, stack):
        """\
        Declare a constant. Assign next word to value from stack.
        Example: ``0 CONSTANT NULL``
        """
        value = stack.pop()
        name = stack.next_word()
        stack.namespace[name.lower()] = value

    @immediate
    @rpn.word('\\')
    def word_line_comment_start(self, stack):
        """Start a line comment and read to its end."""
        while True:
            word = self.next_word()
            if '\n' in word:
                break
        if not word.endswith('\n'):
            raise ValueError('limitation, line comment end "\\n" followed by data: %r' % (word,))

    @immediate
    @rpn.word('(')
    def word_comment_start(self, stack):
        """\
        Start a comment and read to its end (``)``).

        There is a special comment ``( > text... )`` which is recognized by the
        documentation tool. All these type of comments are collected and
        assigned to the next declaration.
        """
        while True:
            word = self.next_word()
            if ')' in word:
                break
        if not word.endswith(')'):
            raise ValueError('limitation, comment end ")" followed by data: %r' % (word,))


    def instruction_output_text(self, stack):
        words = stack._frame_iterator.next()
        self.doctree.write(words)

    @immediate
    @rpn.word('"')
    def word_string_literal(self, stack):
        """Put a string on the stack."""
        words = []
        while True:
            word = self.next_word()
            if word.endswith('"'):
                # emulate character wise reading
                if word != '"':
                    words.append(word[:-1])
                break
            words.append(word)
        text = codecs.escape_decode(u' '.join(words))[0]
        if self.compiling:
            self.frame.append(self.instruction_literal)
            self.frame.append(text)
        else:
            self.push(text)

    @immediate
    @rpn.word('."')
    def word_copy_words(self, stack):
        """Output a string."""
        words = []
        while True:
            word = self.next_word()
            if word.endswith('"'):
                # emulate character wise reading
                if word != '"':
                    words.append(word[:-1])
                break
            words.append(word)
        text = codecs.escape_decode(u' '.join(words))[0]
        if self.compiling:
            self.frame.append(self.instruction_output_text)
            self.frame.append(text)
        else:
            self.doctree.write(text)

    @immediate
    @rpn.word('DEPENDS-ON')
    def word_depends_on(self, stack):
        """\
        Mark word as used so that it is included in cross compilation. Useful
        when using other words within CODE_ definitions.
        """
        if self.compiling:
            word = self.next_word()
            self.frame.append(self.word_depends_on)
            self.frame.append(word)
        else:
            word = stack._frame_iterator.next()
            self._compile_remember(word)

    def _compile_remember(self, word):
        """\
        Remember that a word used. This ensures that it is included in the list
        of cross compiled words.
        """
        # track what is not yet done
        word = word.lower()
        if word not in self.compiled_words:
            self.not_yet_compiled_words.add(word)

    def _compile_frame(self, frame):
        """\
        Compilation of forth functions. Words referenced by this function are
        remembered and can be output later, either manually with `CROSS-COMPILE`_
        or automatically with `CROSS-COMPILE-MISSING`_.
        """
        self.doctree.chapter(frame.chapter)
        self.doctree.section(frame.name)
        self.doctree.write(u'.text\n.even\n')
        self.doctree.write(u';%s\n' % ('-'*76))
        self.doctree.write(u'; compilation of word %s\n' % frame.name)
        self.doctree.write(u';%s\n' % ('-'*76))
        self.doctree.write(u'%s:\n' % self.create_asm_label(frame.name))
        # compilation of the thread
        self.doctree.write('\tbr #%s\n' % self.create_asm_label('DOCOL'))
        #~ self.doctree.write('\tjmp %s\n' % self.create_asm_label('DOCOL'))
        self._compile_thread(frame)
        self.doctree.write('\t.word %s\n\n' % self.create_asm_label('EXIT'))

    def _compile_thread(self, frame):
        next = iter(frame).next
        try:
            while True:
                entry = next()
                if callable(entry):
                    if entry == self.instruction_output_text:
                        label = self.create_label()
                        self.doctree.write('\t.word %s, %s\n' % (
                                self.create_asm_label('__write_text'),
                                self.create_asm_label(label)))
                        self._compile_remember('__write_text')
                        # output the text separately
                        frame = NativeFrame(label)
                        frame.chapter = self.doctree.chapter_name
                        self.target_namespace[label] = frame
                        self._compile_remember(label)
                        text = next()
                        frame.append(self.instruction_output_text)
                        frame.append('\t.asciiz "%s"\n' % (codecs.escape_encode(text)[0],))
                    elif entry == self.instruction_literal:
                        value = next()
                        if isinstance(value, Frame):
                            self.doctree.write('\t.word %s, %s\n' % (
                                    self.create_asm_label('LIT'),
                                    self.create_asm_label(value.name),))
                        else:
                            self.doctree.write('\t.word %s, %-6s ; 0x%04x\n' % (
                                    self.create_asm_label('LIT'),
                                    value,
                                    value & 0xffff))
                        self._compile_remember('LIT')
                    elif entry == self.instruction_seek:
                        # branch needs special case as offset needs to be recalculated
                        offset = next()
                        self.doctree.write('\t.word %s, %s\n' % (self.create_asm_label('BRANCH'), offset*2))
                        self._compile_remember('BRANCH')
                    elif entry == self.instruction_branch_if_false:
                        # branch needs special case as offset needs to be recalculated
                        offset = next()
                        self.doctree.write('\t.word %s, %s\n' % (self.create_asm_label('BRANCH0'), offset*2))
                        self._compile_remember('BRANCH0')
                    elif hasattr(entry, 'rpn_name'):
                        # for built-ins just take the name of the function
                        self.doctree.write('\t.word %s\n' % self.create_asm_label(entry.rpn_name.upper()))
                        self._compile_remember(entry.rpn_name)
                    elif isinstance(entry, Frame):
                        self.doctree.write('\t.word %s\n' % self.create_asm_label(entry.name))
                        self._compile_remember(entry.name)
                    else:
                        raise ValueError('Cross compilation undefined for %r' % entry)
                else:
                    self.doctree.write('\t.word %r\n' % (entry,))
                    #~ raise ValueError('Cross compilation undefined for %r' % entry)
        except StopIteration:
            pass

    def _compile_native_frame(self, frame):
        """Compilation of native code function"""
        self.doctree.chapter(frame.chapter)
        self.doctree.section(frame.name)
        self.doctree.write(u'.text\n.even\n')
        self.doctree.write(u';%s\n' % ('-'*76))
        self.doctree.write(u'; compilation of native word %s\n' % frame.name)
        self.doctree.write(u';%s\n' % ('-'*76))
        self.doctree.write(u'%s:\n' % self.create_asm_label(frame.name))
        # native code blocks are executed. They are expected to print out
        # assembler code
        frame(self)
        self.doctree.write('\n') # get some space between this and next word

    def _compile_interrupt_frame(self, frame):
        """Compilation of interrupt function"""
        self.doctree.section(frame.name)
        self.doctree.write(u'.text\n.even\n')
        self.doctree.write(u';%s\n' % ('-'*76))
        self.doctree.write(u'; compilation of interrupt %s\n' % frame.name)
        self.doctree.write(u';%s\n' % ('-'*76))

        # interrupt entry code
        self.doctree.write(u'__vector_%s:\n' % (frame.vector))
        self.doctree.write(u'\tsub #4, RTOS     ; prepare to push 2 values on return stack\n')
        self.doctree.write(u'\tmov IP, 2(RTOS)  ; save IP on return stack\n')
        self.doctree.write(u'\tmov SP, 0(RTOS)  ; save SP pointer on return stack it points to SR on stack\n')
        self.doctree.write(u'\tmov #%s, IP      ; Move address of thread of interrupt handler in IP\n' % self.create_asm_label(frame.name))
        self.doctree.write('\tbr  #%s\n' % self.create_asm_label('DO-INTERRUPT'))
        # the thread for the interrupt handler
        self.doctree.write(u'%s:\n' % self.create_asm_label(frame.name))
        self._compile_thread(frame)
        self.doctree.write('\t.word %s\n\n' % self.create_asm_label('EXIT-INTERRUPT'))
        self._compile_remember('DO-INTERRUPT')
        self._compile_remember('EXIT-INTERRUPT')


    def instruction_cross_compile(self, stack, word=None):
        """\
        Cross compile word. This function can be called directly (w/ word
        parameter) or be part of a Frame.
        """
        if word is None:
            word = self._frame_iterator.next()
        # when interpreting, execute the actual functionality
        # track what is done
        self.compiled_words.add(word)
        if word in self.not_yet_compiled_words:
            self.not_yet_compiled_words.remove(word)
        # get the frame and compile it - prefer target_namespace
        try:
            item = self.look_up_target(word)
        except KeyError:
            raise ValueError('word %r is not available on the target' % (word,))
        # translate, depending on type
        if isinstance(item, NativeFrame):
            self._compile_native_frame(item)
        elif isinstance(item, InterruptFrame):
            self._compile_interrupt_frame(item)
        elif isinstance(item, Frame):
            self._compile_frame(item)
        else:
            raise ValueError('don\'t know how to compile word %r' % (word,))

    @immediate
    @rpn.word('CROSS-COMPILE')
    def word_cross_compile(self, stack):
        """Output cross compiled version of function. Example:: ``CROSS-COMPILE DROP``"""
        word = self.next_word()
        if self.compiling:
            # when compiling add call to self and the word to the Frame
            self.frame.append(self.instruction_cross_compile)
            self.frame.append(word)
        else:
            # in interpretation mode, compile it now
            self.instruction_cross_compile(stack, word)

    @rpn.word('CROSS-COMPILE-MISSING')
    def word_cross_compile_missing(self, stack):
        """\
        Compile all the words that are used by other compiled words but are not
        yet translated. While compiling words, new words can be found which are
        then also compiled.
        """
        while self.not_yet_compiled_words:
            self.instruction_cross_compile(self, word=self.not_yet_compiled_words.pop())

    @rpn.word('CROSS-COMPILE-VARIABLES')
    def word_cross_compile_variables(self, stack):
        """\
        Output section with variables (values in RAM).
        """
        self.doctree.push_state()
        self.doctree.chapter('__VARIABLES__')
        #~ self.doctree.write(u';%s\n' % ('-'*76))
        #~ self.doctree.write(u'; Variables\n')
        #~ self.doctree.write(u';%s\n' % ('-'*76))
        self.doctree.write(u'.bss\n')
        # XXX check .use_ram attribute
        for name, variable in sorted(self.variables.items()):
            variable.name
            self.doctree.write(u'%s:  .skip %d \n' % (
                    self.create_asm_label(variable.name),
                    2*len(variable)))
            self.doctree.write('\n')
        self.doctree.pop_state()


    @rpn.word('INCLUDE')
    def word_INCLUDE(self, stack):
        """\
        Include and execute definitions from an other file. Example:
        ``INCLUDE helper.forth``
        """
        name = self.next_word()
        self._include(name)

    def _include(self, name):
        """Include given filename. The Forth code is directly executed."""
        # put all data from include in one chapter. remember previous chapter
        # at restore it at the end
        self.doctree.push_state()
        self.doctree.chapter(name)
        if name not in self.included_files:
            for prefix in self.include_path:
                path = os.path.join(prefix, name)
                if os.path.exists(path):
                    self.logger.info('processing include %s' % (name,))
                    self.interpret(rpn.words_in_file(name))
                    self.logger.info('done include %s' % (name,))
                    self.included_files.append(name)
                    break
            else:
                # as fallback, check internal library too
                try:
                    data = pkgutil.get_data('msp430.asm', 'forth/%s' % (name,))
                except IOError:
                    raise ValueError('file not found: %s' % (name,))
                else:
                    self.logger.info('processing include %s' % (name,))
                    self.interpret(rpn.words_in_string(data, name='forth/%s' % (name,), include_newline=True))
                    self.logger.info('done include %s' % (name,))
                    self.included_files.append(name)
        self.doctree.pop_state() # restore previous chapter and section

    @rpn.word('SHOW')
    def word_SHOW(self, stack):
        """Show internals of given word. Used to debug."""
        name = self.next_word()
        sys.stderr.write('SHOW %r\n' % name)
        try:
            value = self.look_up(name)
        except KeyError:
            sys.stderr.write('    value -> <undefined>\n')
        else:
            sys.stderr.write('    value -> %r\n' % (value,))
            if isinstance(value, Frame):
                sys.stderr.write('    contents -> \n')
                for item in value:
                    sys.stderr.write('        %r\n' % item)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main():
    from optparse import OptionParser
    logging.basicConfig(level=logging.ERROR)

    parser = OptionParser(usage="""\
%prog [options] [FILE...]|-]

If no input files are specified data is read from stdin."""
            )
    parser.add_option(
            "-o", "--outfile",
            dest="outfile",
            help="write outputs to given file",
            metavar="FILE",
            default=None)

    parser.add_option(
            "-v", "--verbose",
            action="store_true",
            dest="verbose",
            default=False,
            help="print status messages")

    parser.add_option(
            "--debug",
            action="store_true",
            dest="debug",
            default=False,
            help="print debug messages")

    parser.add_option(
            "-i", "--interactive",
            action="store_true",
            dest="interactive",
            default=False,
            help="interactive mode is started")

    parser.add_option("-D", "--define",
                      action = "append",
                      dest = "defines",
                      metavar = "SYM[=VALUE]",
                      default = [],
                      help="define symbol")

    parser.add_option("-I", "--include-path",
                      action = "append",
                      dest = "include_paths",
                      metavar = "PATH",
                      default = [],
                      help="Add directory to the search path list for includes")

    (options, args) = parser.parse_args()

    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif options.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARN)

    # prepare output
    if options.outfile is not None:
        out = codecs.open(options.outfile, 'w', 'utf-8')
    else:
        out = codecs.getwriter("utf-8")(sys.stdout)

    # XXX make stderr unicode capable
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr)

    instructions = []
    include_paths = []
    for filename in args:
        if filename == '-':
            if options.verbose:
                sys.stderr.write(u'reading stdin...\n')
            instructions.extend(rpn.words_in_file('<stdin>', fileobj=sys.stdin, include_newline=True))
            include_paths.append('.')
        else:
            if options.verbose:
                sys.stderr.write(u'reading file "%s"...\n'% filename)
            try:
                instructions.extend(rpn.words_in_file(filename, include_newline=True))
            except IOError as e:
                sys.stderr.write('forth: %s: File not found\n' % (filename,))
                sys.exit(1)
            include_paths.append(os.path.dirname(os.path.abspath(filename)))

    try:
        forth = Forth()
        forth.init()
        # default to source directory as include path
        forth.include_path = include_paths
        # extend include search path
        forth.include_path.extend(options.include_paths)

        # insert defined symbols
        for definition in options.defines:
            if '=' in definition:
                symbol, value = definition.split('=', 1)
            else:
                symbol, value = definition, '1'
            forth.namespace[symbol.lower()] = value # XXX inserted as string only

        #~ forth.doctree.chapter(filename)
        forth.interpret(iter(instructions))
        forth.doctree.render(out)
    except rpn.RPNError as e:
        sys.stderr.write(u"%s:%s: %s\n" % (e.filename, e.lineno, e))
        if options.debug and e.text:
            sys.stderr.write(u"%s:%s: input line was: %r\n" % (e.filename, e.lineno, e.text))
        #~ if options.debug: raise
        sys.exit(1)
    finally:
        # enter interactive loop when desired
        if options.interactive:
            rpn.interpreter_loop(debug = options.debug, rpn_instance=forth)

if __name__ == '__main__':
    main()
