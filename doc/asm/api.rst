API Documentation
=================
This section is about the internals of the ``msp430.asm`` module. It may be
interesting for developers that work on this module or who are interested in
using the functions the module provides in their own code.

Object file format
------------------
The file format of ``.o4`` files is a bit unusual. It actually contains
something that could be labeled as (specialized) Forth code. So the linker is
some sort of Forth interpreter. This has the advantage that the object files
can be debugged without any special tools, just a text editor. It also makes
the format quite universal; it could produce binaries for all sorts of CPUs
(single special case: the directive ``JMP`` is MSP430 specific).

A list of supported words can be found in the following document:

.. toctree::
    :maxdepth: 1

    linker_words

For more details also take a look at the sources of ``ld.py``.

MCU Definition file format
--------------------------
MCU memory definitions can be provided in a file with Forth like
syntax.

A list of supported words can be found in the following document:

.. toctree::
    :maxdepth: 1

    mcdudef_words

For more details also take a look at the sources of ``mcu_definition_parser.py``.

Modules
-------
.. module:: msp430.asm

``msp430.asm.as``
~~~~~~~~~~~~~~~~~
.. module:: msp430.asm.as

This module implements the MSP430(X) assembler. When the module is executed
(e.g. using ``python -m msp430.asm.as``), it acts as a command line tool.

.. class:: MSP430Assembler

    .. method:: __init__(msp430x=False, debug=False)

        :param msp430x: Set to true to enable MSP430X instruction set.
        :param debug: When set to true dump some internal data so sys.stderr while compiling.

        Create an instance of the assembler.

    .. method:: assemble(f, filename=None, output=sys.stdout)

        :param f: A file like object that supports iterating over lines.
        :param filename: An optional string that is used in error messages.
        :param output: File like object used to write the object code to.

        This method takes assembler source and transforms it to object code
        that can be forwarded to the linker.

.. exception:: AssemblerError

    This instances of this class are raised by the ``MSP430Assembler`` in case
    of errors in the source. It may be annotated with the source filename
    and line number where the error occurred.

    .. attribute:: filename
    .. attribute:: line


``msp430.asm.ld``
~~~~~~~~~~~~~~~~~
.. module:: msp430.asm.ld

This module implements the linker. When the module is executed
(e.g. using ``python -m msp430.asm.ld``), it acts as a command line tool.

.. class:: Segment

    .. method:: __init__(name, start_address=None, end_address=None, align=True, programmable=False, little_endian=True, parent=None, mirror_of=None)

    .. method:: __getitem__(segment_name)

        :param segment_name: name of an sub segment.
        :raises KeyError: when no segment with given name is found

        Easy access to subsegment by name.

    .. method:: sort_subsegments(by_address=False)

        :param by_address: Sort by address if true, otherwise sort by name.

        Sort list of subsegments either by order of definition or by order of
        start address.

    .. method:: clear()

        Clear data. Recursively with all subsegments. Segments are not removed,
        just their data.

    .. method:: __len__()

        Get the number of data bytes contained in the segment.

    .. method:: __cmp__(other)

        Compare function that allows to sort segments by their start_address.

    .. method:: __lt__(other)

        Compare function that allows to sort segments by their start_address.

    .. method:: print_tree(output, indent='', hide_empty=False)

        :param output: a file like object (supporting ``write``)
        :param indent: a prefix put before each line.
        :param hide_empty: when set to true omit empty segments (no data) in output.

        Output segment and subsegments.

    .. method:: shrink_to_fit(address=None)

        Modify start- and end_address of segment to fit the data that it
        contains.  Recursively applied to the tree of segments. Typically
        called with ``address=None``.

    .. method:: write_8bit(value)

        :param value: an integer (8 significant bits)

        Write one byte.

    .. method:: write_16bit(value)

        :param value: an integer (16 significant bits)

        Write two bytes. Order in memory depends on endianness of segment.

    .. method:: write_32bit(value)

        :param value: an integer (32 significant bits)

        Write four bytes. Order in memory depends on endianness of segment.

.. class:: Linker

    .. method:: __init__(instructions)

        :param instructions: list of directives for the linker

        Initialize a linker instance. The given instructions are essentially
        what is read from a ``.o4`` file as sequence of words.

    .. method:: segments_from_definition(segment_definitions)

        :param segment_definitions: dictionary describing the memory map

        This sets the memory map used for linking. See 
        :class:`mcu_definition_parser` for a way to load this description.

    .. method:: update_mirrored_segments()

        Called before writing the final output. In case the memory map contains
        segments that mirror the contents of other segments, they are updated.
        This is typically used for ``.data_init`` which contains the initial
        values that are copied by startup code to the ``.data`` segment in RAM.

    .. method:: pass_one()

        Run the linkers 1st pass. It iterates through the instructions and
        places the data into segments.

    .. method:: pass_two()

        Run the linkers 2nd pass. It iterates through the instructions and
        finds all the labels and saves their position.

    .. method:: pass_three()

        Run the linkers 3rd pass. It iterates through the instructions and
        creates the final binary with all known labels set to their target
        address.

.. exception:: LinkError

    Exception object raised when errors during linking occur. May be annotated
    with the location of the line within the original source file causing the
    error.

    .. attribute:: filename
    .. attribute:: lineno
    .. attribute:: column


``msp430.asm.cpp``
~~~~~~~~~~~~~~~~~~
.. module:: msp430.asm.cpp

This module implements the preprocessor. When the module is executed
(e.g. using ``python -m msp430.asm.cpp``), it acts as a command line tool.

.. function:: line_joiner(next_line)

    Given an iterator for lines, yield lines. It joins consecutive lines with
    the continuation marker (``\\``) to a single line.

.. class:: AnnoatatedLineWriter

    This object is used by the preprocessor to write out the preprocessed text.
    It adds notes in the form ``#line <line> "<filename>"``. These notes are
    used by the assembler to know where a source line originally came from (as
    preprocessed text may contain additional lines etc.)

    .. method:: __init__(output, filename)

        :param output: file like object to write to
        :param filename: the filename used in the notes

    .. method:: write(lineno, text)

        :param linno: line number being written
        :param text: the actual contents of the line

.. class:: Preprocessor

    .. method:: preprocess(infile, outfile, filename)

        :param infile: file like object to read from
        :param outfile: file like object to write to
        :param filename: original file name of the input (infile)

        This runs the preprocessor over the given input.

.. exception:: PreprocessorError

    Exception object raised when errors during preprocessing occur.


``msp430.asm.disassemble``
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.asm.disassemble

This module implements the disassembler. When the module is executed (e.g.
using ``python -m msp430.asm.disassemble``), it acts as a command line tool.

.. class:: MSP430Disassembler

    .. method:: __init__(memory, msp430x=False, named_symbols=None)

        :param memory: A msp43.memory.Memory instance containing the binary.
        :param msp430x: Set to true to enable MSP430X instruction set.
        :param named_symbols: An (optional) instance of :class:`NamedSymbols` which is used to label peripherals and bits.

        Initialize the disassembler with data.

    .. method:: disassemble(output, source_only=False)

        :param output: A file like object used for the resulting text.
        :param source_only: When set to true, the address and data columns are omitted from the output.

        Run the disassembler, result is written to output.


``msp430.asm.rpn``
~~~~~~~~~~~~~~~~~~
.. module:: msp430.asm.rpn

This module implements the an RPN calculator. The calculator can be tested by
executing the module (e.g.  using ``python -m msp430.asm.rpn``).

.. class:: Word(unicode)

    This class is used to wrap words so that their source location can be
    tracked. This is useful for error messages.

    .. method:: __new__(cls, word, filename, lineno, text)

        :param cls: Class for __new__
        :param word: The word (unicode)
        :param filename: Filename where the word was read from.
        :param lineno: Line number within the file.
        :param text: The complete line (or context).
        :type filename: unicode or None
        :type lineno: int or None
        :type text: unicode or None

        Create new instance with a word that was read from given location.

.. class:: RPN

    An RPN calculator. It provides a data stack and implements a number of
    basic operations (arithmetical and stack)

    .. method:: interpret(next_word)

        :param next_word: A function return the next word from input when called.

        Interpret a sequence of words given by the iterator next_word.

.. function:: annotated_words(sequence, filename=None, lineno=None, offset=None, text=None)

    Create an generator for :class:`Word`, all annotated with the given
    information.

.. function:: words_in_string(data, name='<string>')

    :param data: String with (lines) of text.
    :param name: Optional name, used in error messages.

    Create a generator for annotated :class:`Word` in string (``splitlines()``
    is used).

.. function:: words_in_file(filename)

    :param filename: Name of a file to read from.

    Create a generator for annotated :class:`Word` read from file given by name.

.. function:: rpn_function(code)

    :param code: A string in RPN notation
    :return: A Python function.

    Return a wrapper - a function that evaluates the given RPN code when
    called.  This can be used to insert functions implemented as RPN into the
    name space.

.. function:: word(name)

    Function decorator used to tag methods that will be visible in the RPN
    built-in name space.

.. function:: val(words, stack=[], namespace={})

    :param words: Sequence of words.
    :param stack: Optional initial stack.
    :param namespace: Optional namespace.
    :return: The top element from the stack

    Evaluate sequence of words.

.. function:: python_function(code, namespace={})

    :param code: RPN code to execute.
    :param namespace: Optional namespace.
    :return: A python function that executes ``code`` when called.

    Create a Python function that will execute given code when called. All
    parameters given to the Python function will be placed on the stack and the
    top of stack will be returned.

.. function:: interpreter_loop(namespace={}, debug=False)

    Run an interactive loop. Can be used as calculator.

.. exception:: RPNError

    Exception type used for errors when parsing or executing RPN code.
    It may be annotated with the source position where the word causing the
    error came from.

    .. attribute:: filename
    .. attribute:: lineno
    .. attribute:: offset
    .. attribute:: text


``msp430.asm.peripherals``
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.asm.peripherals

This module implements a parser for a file format describing the peripherals
and their bits of a MCU.  The module can be executed (e.g. using ``python -m
msp430.asm.peripherals``) to test definition files.

.. class:: SymbolDefinitions(msp430.asm.rpn.RPN)

    This class implements the parser and keeps the result. It inherits from :class:`RPN`.

.. function:: load_symbols(filename)

    :param filename: Load symbols from a file named like this.
    :return: instance of :class:`SymbolDefinitions`

    Load definitions from a file of given name.

.. function:: load_internal(name)

    :param name: Name of an internal file.
    :return: instance of :class:`SymbolDefinitions`

    This tries to load internal data (using ``pkgutil``).

.. exception:: SymbolError

    Exception object used for errors in the definition file.


``msp430.asm.mcu_definition_parser``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.asm.mcu_definition_parser

This module implements the a parser for files describing the memory map of a
CPU.  The module can be executed (e.g. using ``python -m
msp430.asm.mcu_definition_parser``) to test definition files.

.. class:: MCUDefintitions(msp430.asm.rpn.RPN)

    This class implements the parser and keeps the result. It inherits from :class:`msp430.asm.rpn.RPN`.
    Loaded definitions may contain the memory maps of many MCUs and also
    partial maps (that may depend on each other).

.. function:: load_from_file(filename)

    :param filename: Load definitions from file of given name.
    :return: instance of :class:`MCUDefintitions`

.. function:: load_internal()

    :return: instance of :class:`MCUDefintitions`

    Load internal list. The default list is included in
    ``msp430/asm/definitions/msp430-mcu-list.txt``

.. function:: expand_definition(memory_maps, name)

    :param memory_maps: Memory map descriptions.
    :param name: Name of an MCU that should be extracted
    :type memory_maps: MCUDefintitions
    :return: Dictionary with recursively expanded memory map.

    Return the memory map of a specific MCU. If the definition depends on
    others, it is expanded so that a single, complete description is
    returned.


``msp430.asm.infix2postfix``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.asm.infix2postfix

This module implements a converter that can translate infix (arithmetical)
notation to postfix notation (RPN). It is used by the preprocessor and
assembler when evaluating expressions.

.. function:: infix2postfix(expression, variable_prefix='', scanner=Scanner, precedence=default_precedence)

    :param expression: Input string in infix notation.
    :param variable_prefix: A string that is prepended to symbols found in the expression.
    :param scanner: The class that is used to parse the expression.
    :param precedence: A dictionary returning the priority given an operator as key.
    :return: A string with the expression in postfix notation.

.. function:: convert_precedence_list(precedence_list)

    :param precedence_list: A list of lists that defines operator priorities.
    :return: A dictionary mapping operators to priorities.

    Input will look like this::

        default_precedence_list = [
                # lowest precedence
                ['or'],
                ['and'],
                ['not'],
                ['<', '<=', '>', '>=', '==', '!='],
                ['|', '^', '&'],
                ['<<', '>>'],
                ['+', '-'],
                ['*', '/', '%'],
                ['~', 'neg', '0 +'],
                ['(', ')'],
                # highest precedence
            ]
