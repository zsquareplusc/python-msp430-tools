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

class ForthError(rpn.RPNError):
    pass


class SeekableIterator(object):
    """An iterator with the additional functionality to seek back"""
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


class NativeFrame(list):
    """Storage for native function definitions"""
    def __init__(self, name):
        list.__init__(self)
        self.name = name

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


class Variable(object):
    """This emulates what on a target would be an address"""
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


class Forth(rpn.RPN):
    """\
    Extension of the RPN calculator with Forth like language features.
    """
    def __init__(self, namespace=None):
        rpn.RPN.__init__(self, namespace)
        self.target_namespace = {}  # an other namespace for target only objects
        self.compiling = False
        self.output = sys.stdout
        self.frame = None
        self.variables = {}
        self.include_path = []
        self.included_files = []
        self.compiled_words = set()
        self.not_yet_compiled_words = set()
        self._frame_iterator = None
        self.logger = logging.getLogger('forth')

    def init(self):
        # load core language definitions from a forth file
        self._include('__init__.forth')

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
                ('/', '_slash_'),
                ('\\', '_backslash_'),
                ('|', '_or_'),
                ('&', '_and_'),
                ('@', '_at_'),
                ('[', '_open_bracket_'),
                (']', '_close_bracket_'),
                ('!', '_excl_'),
                ('<', '_less_'),
                ('>', '_bigger_'),
                ('=', '_eq_'),
                ('NOT', '_NOT_'),
                #~ ('AND', '_AND_'),
                #~ ('OR', '_OR_'),
        ):
            name = name.replace(t_in, t_out)
        return name

    def interpret_word(self, word):
        """Depending on mode a word is executed or compiled"""
        #~ print "XXX", word
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
                raise ValueError('!: Frame mismatch for variable %r != %r' % (reference.frmae, self.frame))
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


    @rpn.word('/MOD')
    def word_divmod(self, stack):
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
            stack.push[-1]

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

    @immediate
    @rpn.word("'")
    def word_tick(self, stack):
        """Push reference to next word on stack"""
        if self.frame is None: raise ValueError('not in colon definition')
        name = stack.next_word()
        self.frame.append(self.instruction_literal)
        self.frame.append(self.look_up(name))

    @immediate
    @rpn.word('CHAR')
    def word_char(self, stack):
        """Push ASCII code of next character"""
        name = stack.next_word()
        value = ord(name[0])
        if self.compiling:
            if self.frame is None: raise ValueError('not in colon definition')
            self.frame.append(self.instruction_literal)
            self.frame.append(value)
        else:
            stack.push(value)

    @rpn.word(',')
    def word_coma(self, stack):
        """Append value from stack to current definition"""
        if self.frame is None: raise ValueError('not in colon definition')
        value = stack.pop()
        if isinstance(value, Variable):
            # XXX special case for calculations with HERE
            value = value.offset
        self.frame.append(value)

    @immediate
    @rpn.word(':')
    def word_colon(self, stack):
        """Begin defining a function"""
        if self.frame is not None: raise ValueError('already in colon definition')
        name = self.next_word()
        self.frame = Frame(name)
        self.compiling = True

    @immediate
    @rpn.word(';')
    def word_semicolon(self, stack):
        """End definition of function"""
        if self.frame is None: raise ValueError('not in colon definition')
        #~ print "defined", self.frame.name, self.frame     # XXX DEBUG
        self.namespace[self.frame.name.lower()] = self.frame
        self.frame = None
        self.compiling = False


    @immediate
    @rpn.word('CODE')
    def word_code(self, stack):
        """Begin defining a native code function"""
        if self.frame is not None: raise ValueError('already in colon definition')
        name = self.next_word()
        self.frame = NativeFrame(name)
        self.compiling = True

    @immediate
    @rpn.word('END-CODE')
    def word_end_code(self, stack):
        """End definition of a native code function"""
        if self.frame is None: raise ValueError('not in colon definition')
        #~ print "defined code", self.frame.name, self.frame     # XXX DEBUG
        self.namespace[self.frame.name.lower()] = self.frame
        self.frame = None
        self.compiling = False

    @immediate
    @rpn.word('END-CODE-INTERNAL')
    def word_end_code_internal(self, stack):
        """\
        End definition of a native code function. The name is stored in an
        internal name space. This is used to implement words that are built-in /
        native code on the host, which can not be cross compiled and which
        should not be shadowed be definitions that only work for the target.
        """
        if self.frame is None: raise ValueError('not in colon definition')
        #~ print "defined code internal", self.frame.name, self.frame     # XXX DEBUG
        self.target_namespace[self.frame.name.lower()] = self.frame
        self.frame = None
        self.compiling = False


    @immediate
    @rpn.word('IMMEDIATE')
    def word_immediate(self, stack):
        """Tag current function definition as immediate"""
        if self.frame is None: raise ValueError('not in colon definition')
        self.frame.forth_immediate = True

    @immediate
    @rpn.word('[COMPILE]')
    def word_BcompileB(self, stack):
        """Get next word, look it up and add it to the current frame (not executing immediate functions)"""
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
        """low level instruction to get a literal and push it on the stack"""
        stack.push(stack._frame_iterator.next())

    @rpn.word('BRANCH')
    def instruction_seek(self, stack):
        """Get offset from sequence and jump to this position."""
        difference = stack._frame_iterator.next()
        stack._frame_iterator.seek(difference - 1)

    @rpn.word('0BRANCH')
    def instruction_branch_if_false(self, stack):
        """Get offset from sequence and a boolean from stack. Jump if boolean was false."""
        difference = stack._frame_iterator.next()
        if not stack.pop():
            stack._frame_iterator.seek(difference - 1)

    @immediate
    @rpn.word('RECURSE')
    def word_recurse(self, stack):
        if not self.compiling: raise ValueError('not allowed in immediate mode')
        if self.frame is None: raise ValueError('not in colon definition')
        # put conditional branch operation in sequence, remember position of offset on stack
        self.frame.append(self.instruction_branch_if_false)
        self.push(len(self.frame))
        self.frame.append(0)


    @rpn.word('WORD')
    def word_word(self, stack):
        stack.push(stack.next_word())

    @rpn.word('.')
    def word_dot(self, stack):
        self.output.write(unicode(stack.pop()))

    @rpn.word('EMIT')
    def word_emit(self, stack):
        self.output.write(unichr(stack.pop()))

    @rpn.word('VARIABLE')
    def word_variable(self, stack):
        """Allocate a variable. Creates space in RAM and a address getter function."""
        name = stack.next_word()
        # allocate separate memory for the variable
        # (cross compiled to RAM)
        self.variables[name] = Frame()
        self.variables[name].append(0)
        # create a function that pushes the variables address
        self.namespace[name] = frame
        frame = Frame()
        frame.append(self.instruction_literal)
        frame.append(self.look_up(name))

    @rpn.word('VALUE')
    def word_value(self, stack):
        """Allocate a variable. Creates space in RAM and a value getter function."""
        name = stack.next_word()
        # allocate separate memory for the variable
        # (cross compiled to RAM)
        self.variables[name] = Frame()
        self.variables[name].append(0)
        # create a function that pushes the variables address
        self.namespace[name] = frame
        frame = Frame()
        frame.append(self.instruction_literal)
        frame.append(self.look_up(name))
        frame.append(self.look_up('@'))

    @rpn.word('TO')
    def word_to(self, stack):
        """Write to a VALUE"""
        name = stack.next_word()
        value = stack.pop()
        self.variables[name][0] = value

    @rpn.word('CONSTANT')
    def word_constant(self, stack):
        value = stack.pop()
        name = stack.next_word()
        stack.namespace[name.lower()] = value

    @immediate
    @rpn.word('(')
    def word_comment_start(self, stack):
        """Start a comment and read to its end."""
        while self.next_word() != ')':
            pass

    def instruction_output_text(self, stack):
        words = stack._frame_iterator.next()
        stack.output.write(words)

    @immediate
    @rpn.word('"')
    def word_string_literal(self, stack):
        """Put a string on the stack"""
        words = []
        while True:
            word = self.next_word()
            if word == '"': break
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
        """Output a string"""
        words = []
        while True:
            word = self.next_word()
            if word == '"': break
            words.append(word)
        text = codecs.escape_decode(u' '.join(words))[0]
        if self.compiling:
            self.frame.append(self.instruction_output_text)
            self.frame.append(text)
        else:
            self.output.write(text)

    @immediate
    @rpn.word('DEPENDS-ON')
    def word_depends_on(self, stack):
        """Mark word as used so that it is included in cross compilation."""
        if self.compiling:
            word = self.next_word()
            self.frame.append(self.word_depends_on)
            self.frame.append(word)
        else:
            word = stack._frame_iterator.next()
            self._compile_remember(word)

    def _compile_remember(self, word):
        """Remember words used but yet compiled"""
        # track what is not yet done
        word = word.lower()
        if word not in self.compiled_words:
            self.not_yet_compiled_words.add(word)

    def _compile_frame(self, frame):
        """\
        Compilation of forth functions. Words referenced by this function are
        remembered and can be output later, either manually with CROSS-COMPILE
        or automatically with CROSS-COMPILE-MISSING.
        """
        self.output.write(u';%s\n' % ('-'*76))
        self.output.write(u'; compilation of word %s\n' % frame.name)
        self.output.write(u';%s\n' % ('-'*76))
        next = iter(frame).next
        try:
            self.output.write(u'%s:\n' % self.create_asm_label(frame.name))
            self.output.write('\tjmp DOCOL\n')
            while True:
                entry = next()
                if callable(entry):
                    if entry == self.instruction_output_text:
                        text = next()
                        self.output.write(text)
                        self.output.write('\n')
                    elif entry == self.instruction_literal:
                        value = next()
                        self.output.write('\t.word LIT, %s\n' % value)
                        self._compile_remember('LIT')
                    elif entry == self.instruction_seek:
                        offset = next()
                        self.output.write('\t.word BRANCH, %s\n' % (offset*2,))
                        self._compile_remember('BRANCH')
                    elif entry == self.instruction_branch_if_false:
                        offset = next()
                        self.output.write('\t.word 0BRANCH, %s\n' % (offset*2,))
                        self._compile_remember('0BRANCH')
                    elif hasattr(entry, 'rpn_name'):
                        self.output.write('\t.word %s\n' % self.create_asm_label(entry.rpn_name.upper()))
                        self._compile_remember(entry.rpn_name)
                    elif isinstance(entry, (Frame, NativeFrame)):
                        self.output.write('\t.word %s\n' % self.create_asm_label(entry.name))
                        self._compile_remember(entry.name)
                    else:
                        raise ValueError('Cross compilation undefined for %r' % entry)
                else:
                    raise ValueError('Cross compilation undefined for %r' % entry)
        except StopIteration:
            pass
        self.output.write('\t.word EXIT\n\n')

    def _compile_native_frame(self, frame):
        """Compilation of native code function"""
        self.output.write(u';%s\n' % ('-'*76))
        self.output.write(u'; compilation of native word %s\n' % frame.name)
        self.output.write(u';%s\n' % ('-'*76))
        self.output.write(u'%s:\n' % self.create_asm_label(frame.name))
        # native code blocks are executed to get the output
        frame(self)
        self.output.write('\n')


    def instruction_cross_compile(self, stack, word=None):
        if word is None:
            word = self._frame_iterator.next()
        # when interpreting, execute the actual functionality
        # track what is done
        self.compiled_words.add(word)
        if word in self.not_yet_compiled_words:
            self.not_yet_compiled_words.remove(word)
        # get the frame and compile it - prefer target_namespace
        if word in self.target_namespace:
            item = self.target_namespace[word]
        else:
            item = self.look_up(word)
        # translate, depending on type
        if isinstance(item, Frame):
            self._compile_frame(item)
        elif isinstance(item, NativeFrame):
            self._compile_native_frame(item)
        else:
            raise ValueError('don\'t know how to compile word %r' % (word,))

    @immediate
    @rpn.word('CROSS-COMPILE')
    def word_cross_compile(self, stack):
        """Output cross compiled version of function."""
        word = self.next_word()
        print "XXXX", word
        if self.compiling:
            # when compiling add call to self and the word
            self.frame.append(self.instruction_cross_compile)
            self.frame.append(word)
        else:
            self.instruction_cross_compile(stack, word)

    @rpn.word('CROSS-COMPILE-MISSING')
    def word_cross_compile_missing(self, stack):
        """\
        Compile all the words that are used by other compiled words but not
        yet translated. While compiling words, new words can be found which are
        then also compiled.
        """
        while self.not_yet_compiled_words:
            self.instruction_cross_compile(self, word=self.not_yet_compiled_words.pop())

    @rpn.word('CROSS-COMPILE-VARIABLES')
    def word_cross_compile_variables(self, stack):
        """\
        Compile all the words that are used by other compiled words but not
        yet translated. While compiling words, new words can be found which are
        then also compiled.
        """
        self.output.write(u';%s\n' % ('-'*76))
        self.output.write(u'; Variables\n')
        self.output.write(u';%s\n' % ('-'*76))
        self.output.write(u'.bss\n')
        for variable in self.variables:
            variable.name
            self.output.write(u'%s:  .skip %d \n' % (
                    self.create_asm_label(variable.name),
                    len(variable)))
            self.output.write('\n')
        self.output.write(u'.text\n')


    @rpn.word('INCLUDE')
    def word_INCLUDE(self, stack):
        """Include definitions from an other file."""
        name = self.next_word()
        self._include(name)

    def _include(self, name):
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
                    self.interpret(rpn.words_in_string(data, name='forth/%s' % (name,)))
                    self.logger.info('done include %s' % (name,))
                    self.included_files.append(name)

    @rpn.word('SHOW')
    def word_SHOW(self, stack):
        """Show internals of given word"""
        name = self.next_word()
        sys.stderr.write('SHOW %r\n' % name)
        try:
            value = self.look_up(name)
        except KeyError:
            sys.stderr.write('    value -> <undefined>\n')
        else:
            sys.stderr.write('    value -> %r\n' % (value,))
            if isinstance(value, (Frame, NativeFrame)):
                sys.stderr.write('    contents -> %r\n' % list(repr(x) for x in value))

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
            instructions.extend(sys.stdin.read().split())
            include_paths.append('.')
        else:
            if options.verbose:
                sys.stderr.write(u'reading file "%s"...\n'% filename)
            try:
                instructions.extend(rpn.words_in_file(filename))
            except IOError as e:
                sys.stderr.write('forth: %s: File not found\n' % (filename,))
                sys.exit(1)
            include_paths.append(os.path.dirname(os.path.abspath(filename)))

    try:
        forth = Forth()
        forth.init()
        forth.output = out
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

        forth.interpret(iter(instructions))
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
