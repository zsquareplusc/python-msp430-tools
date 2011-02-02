==========
 Overview
==========
This is about the python-msp430-tools, that provide a number of tools related
to the MSP430 embedded processor.

Python 2.6 or newer should be used. The Python package "msp430" can be
installed with ``python setup.py install``. These modules can be used as
standalone applications or as library for other programs.


NEWS
====
Compared to the python-mspgcc-tools:

- new "target" base implementation that all upload/download tools share

- >64k address space support for most tools

- new download tool: ``msp430.gdb.target``. It communicates with a GDB server
  for the MSP430 such as ``msp430-gdbproxy`` or ``mspdebug``.

- new BSL implementation (F1x, F2x, F4x): ``msp430.bsl.target``

- new BSL implementation (F5x, F6x): ``msp430.bsl5.hid`` and
  ``msp430.bsl5.uart``

- JTAG tool renamed to: ``msp430.jtag.target``

  - renamed command line options ``-l/--lpt``  to ``-p/--port``
  - new command line option ``-l/--library-path``

- all target tools:

  - renamed command line options ``-P``, ``-V`` to upper case
  - new command line option ``-U/--upload-by-file``
  - new command line option ``-b/--erase-by-file``
  - multiple files on the command line are merged before downloading
    (supporting overlapping areas - last one counts). Useful e.g. if a
    boot loader part should be merged with an application part.
  - specifying input format is now one option: ``-i/--input-format``
  - specifying output format is now one option: ``-f/--output-format``
  - new file formats: ``hex``, ``bin``

- new modules:

  - ``msp430.listing``              (read IAR and mspgcc listing files)
  - ``msp430.gdb``                  (GDB client code for use with GDB servers)
  - ``msp430.shell.command``        (busybox alike shell commands: ``mv``, ``cp``, ``rm`` and more)
  - ``msp430.bsl5``                 (F5xx/F6xx BSL support)

    - ``msp430.bsl5.hid``           (USB HID frontend)
    - ``msp430.bsl5.uart``          (serial frontend)

- new tools:

  - ``msp430.memory.convert``       (convert hex file formats)
  - ``msp430.memory.generate``      (create hex files with fill pattern)
  - ``msp430.memory.compare``       (compare hex files)
  - ``msp430.memory.hexdump``       (show contents of hex files)

- new license: Simplified BSD License instead of Python License.


There is no longer a separate line frontend for each tool. However tools can be
used as follows::

        python -m <module name> [options] [arguments]

e.g.::

        python -m msp430.bsl.target -p /dev/ttyUSB0 -e somefile.elf

