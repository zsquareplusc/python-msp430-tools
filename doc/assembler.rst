===========
 Assembler
===========

The module ``msp430.asm`` provides an assembler for MSP430 and MSP430X CPUs.
There is also a disassembler.

Additionally a (almost C compatible) preprocessor is provided.

The User section covers the command line tools and how to use them. The API
section is about the internals of the tools and may be interesting to
developers that extended the tools or use them as a library.

Also available is a Forth cross compiler that can translate Forth programs to
MSP430 assembler.

.. toctree::
    :maxdepth: 3

    asm/tutorial
    asm/commandline
    asm/forth
    asm/api
