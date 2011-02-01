=====================
 MSP430[X] Assembler
=====================

(C) 2001-2006, 2010-2011 Chris Liechti <cliechti@gmx.net>

Released under the Simplified BSD license.


Overview
--------

This is an experimental assembler and linker for the TI MSP430 processor.
It is implemented in Python (get it from www.python.org).

The assembler (``as.py``) produces a file in a proprietary object format which
can be read by the linker (``ld.py``). The linker writes TI-Text format files
which can be downloaded to the processor or run in the simulator.

A disassembler (``disassemble.py``) is also provided.


Features
--------
- Complete MSP430 assembler instruction set, including MSP430X instructions

- Constant registers are used.

- Assembler directives are implemented as pseudo instructions.

- Number formats:

    - "0x1af" for hexadecimal
    - "0b101" binary
    - "123" for decimal

- Memory layout (segments) is loaded from file optionally use a user supplied
  definition file and can be specified

- Expressions are evaluated by a built in calculator.
  (some operators: +, -, *, /, %, <<, >>, |, &, ^, and, or, not)


Example
-------
(for use in a un*x like shell, windows users can replace "./" by "python "
or the full path to the interpreter or use cygwin/bash)

    ./as.py led.S
    ./as.py intvec.S
    ./ld.py intvec.o4 led.o4


Sections
--------
These are the sections as they are meant to be used by the provided MCU
definition file. The user can supply a different file with completely
different sections, when desired.

.data
    This section is in the RAM. It is meant for initialized variables, see also
    .data_init.

.bss
    This section is in the RAM and meant for uninitialized variables. The
    startup code should zero out this section.

.noinit
    An other section in the RAM. It is not altered by the startup code.

.const
    This is like .text in the Flash. It is meant for non-code items.

.text
    Code and other things in the Flash.

.data_init
    Automatically created copy of .data but placed in Flash.
    The startup code would then copy the contents of this
    segment to the .data section in RAM.

Symbols:
_stack
    The last address in RAM, used to initialized the stack pointer.

.. note::

    using ``_stack``, copying ``.data_init``, zeroing ``.bss`` needs to
    be implemented in startup code which is not provided.

