
Command line tools
==================

``msp43.asm.as``
----------------
An assembler for MSP430(X).

.. warning:: This tool is currently in an experimental stage. Is has been used
             to successfully create simple programs but it is not broadly
             tested.

Command line
~~~~~~~~~~~~
Usage: as.py [options]

Options:
  -h, --help            show this help message and exit
  -x, --msp430x         Enable MSP430X instruction set
  -o FILE, --outfile=FILE
                        name of the object file
  --filename=FILE       Use this filename for input (useful when source is
                        passed on stdin)
  -v, --verbose         print status messages to stderr
  --debug               print debug messages to stderr
  -i, --instructions    Show list of supported instructions and exit (see also
                        -x)

Supported directives
~~~~~~~~~~~~~~~~~~~~
The instruction set as documented in the MSP430 family guides is supported as
well as the following pseudo instructions:

- ``.ASCII``   Insert the given text as bytes
- ``.ASCIIZ``  Insert the given text as bytes, append null byte
- ``.BSS``     Select ``.bss`` section for output
- ``.BYTE``    Insert the given 8 bit values
- ``.DATA``    Select ``.data`` section for output
- ``.EVEN``    Align address pointer to an even address
- ``.LONG``    Insert the given 32 bit values
- ``.SECTION`` Select named section for output
- ``.SET``     Define a symbol with a value (can be used at link time)
- ``.SKIP``    Skip the given amount of bytes
- ``.TEXT``    Select ``.text`` section for output
- ``.WEAKALIAS`` Create alias for label in case it is not defined directly
- ``.WORD``    Insert the given 16 bit values


``msp430.asm.ld``
-----------------
The linker processes one or multiple ``.o4`` files (the output from ``as``)
and creates a binary file that can be downloaded to a target.

Command line
~~~~~~~~~~~~
Usage: ld.py [options] [FILE...]|-]

If no input files are specified data is read from stdin.
Output is in "TI-Text" format.

Options:
  -h, --help            show this help message and exit
  -o FILE, --outfile=FILE
                        name of the resulting binary (TI-Text)
  -T FILE, --segmentfile=FILE
                        linker definition file
  -m MCU, --mcu=MCU     name of the MCU (used to load memory map)
  --mapfile=FILE        write map file
  -v, --verbose         print status messages
  --debug               print debug messages


``msp430.asm.cpp``
------------------
This is an (almost C compatible) preprocessor. It can work with macros
(``#define``) and evaluate arithmetic expressions.

Supported directives are:

- ``#define``   Define a value or function like macro
- ``#include``  Read and insert given file
- ``#if``       Conditional compilation is predicate is true. ``defined`` is also supported.
- ``#ifdef``    Conditional compilation if given symbol is defined
- ``#ifndef``   Conditional compilation if given symbol is not defined
- ``#else``     For the inverse of ``#if``/``#ifdef``/``#ifndef``
- ``#endif``    Finish ``#if``/``#ifdef``/``#ifndef`` / ``#else``
- ``#undef``    Forget about the definition of a macro


Command line
~~~~~~~~~~~~
Usage: cpp.py [options]

Options:
  -h, --help            show this help message and exit
  -o FILE, --outfile=FILE
                        name of the object file
  -p FILE, --preload=FILE
                        process this file first. its output is discarded but
                        definitions are kept.
  -v, --verbose         print status messages
  --debug               print debug messages to stdout
  -D SYMVALUE, --define=SYMVALUE
                        define symbol
  -I PATH, --include-path=PATH
                        Add directory to the search path list for includes

To define symbols, use ``-D SYMBOL=VALUE`` respectively ``--define SYMBOL=VALUE``


``msp430.asm.disassemble``
--------------------------
This is a disassembler for MSP430(X) code. It outputs an annotated listing.
Each jump target is assigned an automatic label and a newline is inserted after
each non conditional jump to make reading the source easier.

The disassembler currently has no knowledge about the memory map or usage of
memory. Therefore it disassembles just anything, even if it is not code.

Provided with a symbol file, it can insert the names and named bits of accessed
peripherals (for details see ``msp430/asm/definitions/F1xx.txt``).

.. warning:: This tool is currently in an experimental stage. It is not fully
             tested and especially the cycle counts are not verified.

Command line
~~~~~~~~~~~~
Usage: disassemble.py [options] [SOURCE...]

MSP430(X) disassembler.


Options:
  -h, --help            show this help message and exit
  -o DESTINATION, --output=DESTINATION
                        write result to given file
  --debug               print debug messages
  -v, --verbose         print more details
  -i TYPE, --input-format=TYPE
                        input format name (titext, ihex, bin, hex, elf)
  -x, --msp430x         Enable MSP430X instruction set
  --source              omit hex dump, just output assembler source
  --symbols=NAME        read register names for given architecture (e.g. F1xx)

