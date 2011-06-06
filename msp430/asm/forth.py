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
        old_iterator = stack._iterator
        stack._iterator = iterable
        try:
            while True:
                instruction = iterable.next()
                instruction(stack)
        except StopIteration:
            pass
        finally:
            stack._iterator = old_iterator


class NativeFrame(list):
    """Storage for native function definitions"""
    def __init__(self, name):
        list.__init__(self)
        self.name = name

    def __call__(self, stack):
        """Execute code in frame"""
        iterable = SeekableIterator(self)
        old_iterator = stack._iterator
        stack._iterator = iterable
        try:
            while True:
                instruction = iterable.next()
                instruction(stack)
        except StopIteration:
            pass
        finally:
            stack._iterator = old_iterator


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
        self.compiling = False
        self.output = sys.stdout
        self.frame = None
        self.included_files = []
        self.compiled_words = set()
        self.not_yet_compiled_words = set()
        self.logger = logging.getLogger('forth')

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
                ('[', '_open_bracket_'),
                (']', '_close_bracket_'),
                ('!', '_excl_'),
        ):
            name = name.replace(t_in, t_out)
        return name

    def interpret_word(self, word):
        """Depending on mode a word is executed or compiled"""
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


    @immediate
    @rpn.word(':')
    def word_colon(self, stack):
        """Begin defining a function"""
        if self.frame is not None: raise ForthError('already in colon definition')
        name = self._iterator.next()   # next word
        self.frame = Frame(name)
        self.compiling = True

    @immediate
    @rpn.word(';')
    def word_semicolon(self, stack):
        """End definition of function"""
        if self.frame is None: raise ForthError('not in colon definition')
        #~ print "defined", self.frame.name, self.frame     # XXX DEBUG
        self.namespace[self.frame.name.lower()] = self.frame
        self.frame = None
        self.compiling = False


    @immediate
    @rpn.word('CODE')
    def word_code(self, stack):
        """Begin defining a native code function"""
        if self.frame is not None: raise ForthError('already in colon definition')
        name = self._iterator.next()   # next word
        self.frame = NativeFrame(name)
        self.compiling = True

    @immediate
    @rpn.word('END-CODE')
    def word_end_code(self, stack):
        """End definition of a native code function"""
        if self.frame is None: raise ForthError('not in colon definition')
        #~ print "defined", self.frame.name, self.frame     # XXX DEBUG
        self.namespace[self.frame.name.lower()] = self.frame
        self.frame = None
        self.compiling = False


    @immediate
    @rpn.word('IMMEDIATE')
    def word_immediate(self, stack):
        """Tag current function definition as immediate"""
        if self.frame is None: raise ForthError('not in colon definition')
        self.frame.forth_immediate = True

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


    def instruction_literal(self, stack):
        """lowlevel instruction to get a literal and push it on the stack"""
        stack.push(stack._iterator.next())

    def instruction_seek(self, stack):
        """Get offset from sequence and jump to this position."""
        difference = stack._iterator.next()
        stack._iterator.seek(difference)

    def instruction_branch_if_false(self, stack):
        """Get offset from sequence and a boolean from stack. Jump if boolean was false."""
        difference = stack._iterator.next()
        if not stack.pop():
            stack._iterator.seek(difference)

    @immediate
    @rpn.word('IF')
    def word_if(self, stack):
        if self.frame is None: raise ForthError('not in colon definition')
        # put conditional branch operation in sequence, remeber position of offset on stack
        self.frame.append(self.instruction_branch_if_false)
        self.push(len(self.frame))
        self.frame.append(0)

    @immediate
    @rpn.word('ELSE')
    def word_else(self, stack):
        if self.frame is None: raise ForthError('not in colon definition')
        # get old offset from stack
        offset = self.pop()
        # put unconditional branch operation in sequence, remeber position of offset on stack
        self.frame.append(self.instruction_seek)
        self.push(len(self.frame))
        self.frame.append(0)
        # patch offset at 'if' with current location
        self.frame[offset] = len(self.frame) - offset - 1

    @immediate
    @rpn.word('ENDIF')
    def word_endif(self, stack):
        if self.frame is None: raise ForthError('not in colon definition')
        # patch offset at if or else with current location
        offset = self.pop()
        self.frame[offset] = len(self.frame) - offset - 1


    @immediate
    @rpn.word('BEGIN')
    def word_begin(self, stack):
        if self.frame is None: raise ForthError('not in colon definition')
        # remeber this position on stack
        self.push(len(self.frame))

    @immediate
    @rpn.word('LOOP')
    def word_loop(self, stack):
        if self.frame is None: raise ForthError('not in colon definition')
        # get old offset from stack
        offset = self.pop()
        # put unconditional branch to loop begin
        self.frame.append(self.instruction_seek)
        self.frame.append(offset - len(self.frame) - 1)

    @immediate
    @rpn.word('WHILE')
    def word_while(self, stack):
        if self.frame is None: raise ForthError('not in colon definition')
        # get old offset from stack
        offset = self.pop()
        # put unconditional branch to loop begin
        self.frame.append(self.instruction_branch_if_false)
        self.frame.append(offset - len(self.frame) - 1)


    @rpn.word('LITERAL')
    def word_literal(self, stack):
        if self.frame is None: raise ForthError('not in colon definition')
        # add literal to compiled word
        self.frame.append(self.instruction_literal)
        self.frame.append(self.pop())

    @rpn.word('WORD')
    def word_word(self, stack):
        stack.push(stack.next_word())

    @rpn.word('.')
    def word_dot(self, stack):
        self.output.write(unicode(stack.pop()))

    @rpn.word('EMIT')
    def word_emit(self, stack):
        self.output.write(unichr(stack.pop()))

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
        words = stack._iterator.next()
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
                    if hasattr(entry, 'rpn_word'):
                        self.output.write('\t.word %s\n' % self.create_asm_label(entry.rpn_word))
                        # track what is not yet done
                        if entry.name not in self.compiled_words:
                            self.not_yet_compiled_words.add(entry.name)
                    elif entry == self.instruction_output_text:
                        text = next()
                        self.output.write(text)
                        self.output.write('\n')
                    elif entry == self.instruction_literal:
                        value = next()
                        self.output.write('\t.word LIT, %s\n' % value)
                    elif entry == self.instruction_seek:
                        offset = next()
                        self.output.write('\t.word BRANCH, %s\n' % (offset*2,))
                    elif entry == self.instruction_branch_if_false:
                        offset = next()
                        self.output.write('\t.word BRANCH0, %s\n' % (offset*2,))
                    elif isinstance(entry, (Frame, NativeFrame)):
                        self.output.write('\t.word %s\n' % self.create_asm_label(entry.name))
                        # track what is not yet done
                        if entry.name not in self.compiled_words:
                            self.not_yet_compiled_words.add(entry.name)
                    else:
                        # builtins - XXX must be provided by user
                        #~ self.output.write('\t.word %s\n' % entry.name)
                        self.output.write('; error1: %s\n' % entry)
                else:
                    self.output.write('; error2: %s\n' % entry)
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


    @immediate
    @rpn.word('CROSS-COMPILE')
    def word_cross_compile(self, stack, word=None):
        """Output cross compiled version of function."""
        if word is None:
            word = self.next_word()
        if self.compiling:
            # when compiling add call to self and the word
            self.frame.append(self.word_cross_compile)
            self.frame.append(word)
        else:
            # when interpreting, execute the actual functionality
            # track what is done
            self.compiled_words.add(word)
            if word in self.not_yet_compiled_words:
                self.not_yet_compiled_words.remove(word)
            # get the frame and compile it
            item = self.look_up(word)
            if isinstance(item, Frame):
                self._compile_frame(item)
            elif isinstance(item, NativeFrame):
                self._compile_native_frame(item)
            else:
                raise ValueError('don\'t know how to compile word %r: %r' % (word, frame))

    @rpn.word('CROSS-COMPILE-MISSING')
    def word_cross_compile_missing(self, stack):
        """\
        Compile all the words that are used by other compiled words but not
        yet translated. While compiling words, new words can be found which are
        then also compiled.
        """
        while self.not_yet_compiled_words:
            self.word_cross_compile(self, word=self.not_yet_compiled_words.pop())


    @rpn.word('INCLUDE')
    def word_INCLUDE(self, stack):
        """Include definitions from an other file."""
        name = self.next_word()
        if name not in self.included_files:
            self.included_files.append(name)
            self.logger.info('processing include %s' % (name,))
            #~ # XXX currently only internal imports are supported
            #~ data = pkgutil.get_data('msp430.asm', 'definitions/%s.peripheral' % (name,))
            #~ self.interpret(rpn.words_in_string(data, name='definitions/%s.peripheral' % (name,)))
            self.interpret(rpn.words_in_file(name))
            self.logger.info('done include %s' % (name,))

    @rpn.word('SHOW')
    def word_SHOW(self, stack):
        """Show internals of given word"""
        name = self.next_word()
        sys.stderr.write('SHOW %r\n' % name)
        if name in self.namespace:
            sys.stderr.write('value -> <undefined>\n')
        else:
            sys.stderr.write('value -> %r\n' % self.look_up(name))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main():
    import os
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
    for filename in args:
        if filename == '-':
            if options.verbose:
                sys.stderr.write(u'reading stdin...\n')
            instructions.extend(sys.stdin.read().split())
        else:
            if options.verbose:
                sys.stderr.write(u'reading file "%s"...\n'% filename)
            try:
                instructions.extend(rpn.words_in_file(filename))
            except IOError as e:
                sys.stderr.write('forth: %s: File not found\n' % (filename,))
                sys.exit(1)

    forth = Forth()
    forth.output = out

    # insert defined symbols
    for definition in options.defines:
        if '=' in definition:
            symbol, value = definition.split('=', 1)
        else:
            symbol, value = definition, '1'
        forth.namespace[symbol.lower()] = value # XXX inserted as string only

    try:
        forth.interpret(iter(instructions))
    except rpn.RPNError as e:
        sys.stderr.write(u"%s:%s: %s\n" % (e.filename, e.lineno, e))
        if options.debug and e.text:
            sys.stderr.write(u"%s:%s: input line was: %r\n" % (e.filename, e.lineno, e.text))
        #~ if options.debug: raise
        sys.exit(1)

    # enter interactive loop when desired
    if options.interactive:
        rpn.interpreter_loop(debug = options.debug, rpn_instance=forth)

if __name__ == '__main__':
    main()
