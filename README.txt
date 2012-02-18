===========================================
 MSP430 Tools (Python scripts and library)
===========================================

The python-msp430-tools are a collection of tools related to the MSP430
embedded processor.

Python 2.6 or newer (2.x series) is required for most modules. The python
package "msp430" can be installed with "python setup.py install". These modules
can be used as standalone applications or as library for other programs.

Download tools
==============
Command line tools, e.g. ``python -m msp430.gdb.target``. They can up and
download memory of MSP430 targets.

- ``msp430.jtag.target``    JTAG interface
- ``msp430.bsl.target``     F1x, F2x, F4x BSL
- ``msp430.bsl5.uart``      F5x, F6x BSL (non-USB devices)
- ``msp430.bsl5.hid``       F5x, F6x BSL (USB devices)
- ``msp430.gdb.target``     Using a GDB proxy (TCP/IP connection).


Other tools
===========
- ``msp430.memory.convert``  Convert between hex file formats

- ``msp430.memory.dco``      Measure or calibrate the DCO clock

- ``msp430.memory.compare``  Compare two hex files

- ``msp430.memory.hexdump``  Show contents of hex files

- ``msp430.memory.generate`` Create hex files with a defined pattern. Can be
  used for testing or to create underlays for other binaries (e.g. to fill
  unused memory with "NOPs" or "JMP $")

- ``msp430.memory.downloader``   Small program, suitable for file associations,
  so that double clicking an ELF or a43 file can be used to download via
  JTAG.

- ``msp430.asm.as``, ``msp430.asm.ld``, ``msp430.asm.cpp``: An assembler,
  linker and preprocessor for MSP430(X)

- ``msp430.asm.disassemble``


Description of Python library
=============================
``msp430``
    Root package for the Python modules related to the MSP430.

``msp430.asm``
    A simple assembler and linker, also a disassembler, supporting MSP430(X).

``msp430.bsl``
    Support for the boot strap loader. ``msp430.bsl.target`` is the main 
    package for the downloader and contains subclassed modules for target
    specific BSL hardware.

``msp430.bsl5``
    Support for the boot strap loader of F5xx/F6xx devices. ``msp430.bsl5.hid``
    is the main module for the downloader for F5xx USB devices and
    ``msp430.bsl5.uart`` for all others.

``msp430.jtag``
    JTAG tools using the MSP430[mspgcc] library. ``msp430.jtag.target`` is the
    main module for the downloader.

``msp430.gdb``
    Communicate with a GDB server/proxy. ``msp430.gdb.target`` is the
    main module for the downloader.

``msp430.memory``
    Memory implementation, used to store an memory image used to download to
    the MSP430. File format handlers are here too.
    Interesting submodules are:
    - convert
    - compare
    - hexdump
    - generate

``msp430.shell.commands``
    Shell commands, useful for makefiles etc.

``msp430.shell.watch``
    Watch a file for changes and execute a command in that case.

``msp430.listing``
    Parser for listing files.

``msp430.legacy``
    Support code for older tools.

