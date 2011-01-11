===========================================
 MSP430 Tools (Python scripts and library)
===========================================
This is about the python-msp430-tools, that provide a number of tools related
to the MSP430 embedded processor.

Python 2.5 or newer should be used. The python package "msp430" can be
installed with "python setup.py install". These modules can be used as
standalone applications or as library for other programs.


Description of command line tools
=================================
msp430-bsl
    Command line application for the MSP430 Boot Strap Loader. Erasing,
    programming, uploading of flash and RAM.

msp430-dco
    Command line application for the MSP430 parallel JTAG adapter. Measure
    or callibrate the DCO clock.

msp430-gdb
    Command line application do download using a GDB proxy (TCP/IP connection).

msp430-convert
    Command line utility to convert between hex file formats.

msp430-compare
    Compare two hex files

msp430-hexdump
    Show contents of hex files

msp430-generate
    Create hex files with a defined pattern. Can be used for testing or to
    create underlays for other binaries (e.g. to fill unused memory with
    "NOPs" or "JMP $")

msp430-downloader
    Small program, suitable for file associations, so that double clicking an
    ELF or a43 file can be used to download via JTAG.

msp430-jtag
    Command line application for the MSP430 parallel JTAG adapter. Erasing,
    programming, uploading of flash and RAM.


Description of Python library
=============================
msp430
    Root package for the Python modules related to the MSP430.

msp430.bsl
    Support for the boot strap loader. ``msp430.bsl.target`` is the main module
    for the downloader.

msp430.jtag
    JTAG tools using the MSP430[mspgcc] library. ``msp430.jtag.target`` is the
    main module for the downloader.

msp430.gdb
    Communicate with a GDB server/proxy. ``msp430.gdb.target`` is the
    main module for the downloader.

msp430.memory
    Memory implementation, used to store an memory image used to download to
    the MSP430. File format handlers are here too.

msp430.shell.commands
    Shell commands, useful for makefiles etc.

msp430.listing
    Parser for listing files.

msp430.legacy
    Support code for older tools.


Other files
===========
demo
    Demonstration tools. Currently there are BSL and JTAG wrappers for Win32
    using the NSIS installer system. The resulting executables contain
    everything that's needed to reprogram a device. Useful for field updaters,
    etc.

    mmc.py: a Python demo that reads an MMC card connected to the JTAG port.
    See source file for wiring.

win32
    Windows related stuff, files to create executables and installers.

makefile
    Install the two command line tools and the Python library.
