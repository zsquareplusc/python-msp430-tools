msp430-jtag
===========

Software to talk to the parallel port and USB JTAG adapters for the MSP430.

Features
--------

- understands ELF, TI-Text and Intel-hex object files
- download to Flash and/or RAM, erase flash, verify
- reset device
- upload a memory block MSP->PC (output as binary data or hex dump, ihex)
- written in Python, runs on Win32, Linux, BSD, ...
- use on command line, or in a Python script
- reset and wait for key press (to run a device directly from the port
  power)
- TI/3rd party library support for USB JTAG adaptors


Requirements
------------
- Linux, BSD, Un*x or Windows PC
- Python 2.5 or newer
- Parallel JTAG hardware with an MSP430 device connected
- or USB adapter with a corresponding [3rd party] MSP430 library


Short introduction
------------------
This software uses the JTAG hardware that comes with the FET kits. It is
connected to the parallel port. Using 3rd party backends it is also possible
to use USB programmers.

The program can be started by typing ``msp430-jtag`` when installed correctly
If it's used from the source directory use "python -m msp430.jtag.target".

Usage: msp430.jtag.target [OPTIONS] [FILE [FILE...]]

Options:
  -h, --help            show this help message and exit
  -d, --debug           print debug messages and tracebacks (development mode)
  -v, --verbose         show more messages (can be given multiple times)
  -q, --quiet           suppress all messages
  --time                measure time
  -S, --progress        show progress while programming
  --help-backend        show help about the different backends
  -l LIBRARY_PATH, --library-path=LIBRARY_PATH
                        search for libMSP430.so or libMSP430mspgcc.so in this
                        place first

  Data input:
    File format is auto detected, unless --input-format is used. Preferred
    file extensions are ".txt" for TI-Text format, ".a43" or ".hex" for
    Intel HEX. ELF files can also be loaded.

    Multiple files can be given on the command line, all are merged before
    the download starts. "-" reads from stdin.

    -i TYPE, --input-format=TYPE
                        input format name (titext, ihex, bin, hex, elf)

  Flash erase:
    Multiple --erase options are allowed. It is also possible to use
    address ranges such as 0xf000-0xf0ff or 0xf000/4k.

    NOTE: SegmentA on F2xx is NOT erased with --mass-erase, that must be
    done separately with --erase=0x10c0 or --info-erase".

    -e, --mass-erase    mass erase (clear all flash memory)
    -m, --main-erase    erase main flash memory only
    --info-erase        erase info flash memory only (0x1000-0x10ff)
    -b, --erase-by-file
                        erase only Flash segments where new data is downloaded
    --erase=ADDRESS     selectively erase segment at the specified address or
                        address range

  Program flow specifiers:
    All these options work against the file(s) provided on the command
    line. Program flow specifiers default to "-P" if a file is given.

    "-P" usually verifies the programmed data, "-V" adds an additional
    verification through uploading the written data for a 1:1 compare.

    No default action is taken if "-P", "-V" or "-E" is given, say
    specifying only "-V" does a "check by file" of a programmed device
    without programming.

    Don't forget to erase ("-e", "-b" or "-m") before programming flash!

    -E, --erase-check   erase check by file
    -P, --program       program file
    -V, --verify        verify by file
    -U, --upload-by-file
                        upload the memory that is present in the given file(s)

  Data upload:
    This can be used to read out the device memory. It is possible to use
    address ranges such as 0xf000-0xf0ff or 0xf000/256, 0xfc00/1k.

    Multiple --upload options are allowed.

    -u ADDRESS, --upload=ADDRESS
                        upload a data block, can be passed multiple times
    -o DESTINATION, --output=DESTINATION
                        write uploaded data to given file
    -f TYPE, --output-format=TYPE
                        output format name (titext, ihex, bin, hex),
                        default:hex

  Do before exit:
    -x ADDRESS, --execute=ADDRESS
                        start program execution at specified address, might
                        only be useful in conjunction with --wait
    -r, --reset         perform a normal device reset that will start the
                        program that is specified in the reset interrupt
                        vector
    -w, --wait          wait for <ENTER> before closing the port
    --no-close          do not close port on exit

  Connection:
    NOTE: On Windows, use "USB", "TIUSB" or "COM5" etc if using MSP430.dll
    from TI. On other platforms, e.g. Linux, use "/dev/ttyUSB0" etc. if
    using libMSP430.so. If a libMSP430.so is found, it is preferred,
    otherwise libMSP430mspgcc.so is used.

    NOTE: --slowdown > 50 can result in failures for the RAM size auto
    detection (use --ramsize option to fix this). Use the --verbose option
    and watch the outputs. The DCO clock adjustment and thus the Flash
    timing may be inaccurate for large values.

    --backend=BACKEND   select an alternate backend. See --help-backend for
                        more information
    -p PORT, --port=PORT
                        specify an other parallel port or serial port for the
                        USBFET (the later requires libMSP430.so instead of
                        libMSP430mspgcc.so).  (defaults to "LPT1"
                        ("/dev/parport0" on Linux))
    --spy-bi-wire-jtag  interface is 4 wire on a spy-bi-wire capable device
    --spy-bi-wire       interface is 2 wire on a spy-bi-wire capable device
    --slowdown=MICROSECONDS
                        artificially slow down the communication. Can help
                        with long lines, try values between 1 and 50 (parallel
                        port interface with mspgcc's HIL library only).
                        (experts only)
    -R BYTES, --ramsize=BYTES
                        specify the amount of RAM to be used to program flash
                        (default: auto detected)

  JTAG fuse:
    WARNING: This is not reversible, use with care!  Note: Not supported
    with the simple parallel port adapter (7V source required).",

    --secure            blow JTAG security fuse

  Examples:
    Mass erase and program from file: "/home/lch/python-mspgcc-
    tools/msp430/jtag/target.py -e firmware.elf" Dump information memory:
    "/home/lch/python-mspgcc-tools/msp430/jtag/target.py
    --upload=0x1000-0x10ff"



.. note::
    Some versions of the Texas Instruments MSP430 Development Tool
    require that you give the '--no-close' option to msp430-jtag. This
    is because the Texas Instruments tool is powered via the JTAG
    adapter; the '--no-close' option prevents msp430-jtag from powering
    the adapter off.  You may also need to restart the program with 
    msp430-jtag (using the '--no-close' and '-r' options is sufficient)
    after rebooting your machine.

    Other development kits that rely on the parallel port for their power
    source may also need the '--no-close' option.  It is preferable to
    try programming the device *without* the '--no-close' option first,
    and introduce this option only if the uploaded code fails to start.

    Alternatively, it is possible run ``msp430-jtag -w`` to power the
    eval board from the JTAG interface.


Backends
--------
msp430-jtag can use different libraries to connect to the target.
The backend can be chosen with the --backend command line option.

"mspgcc"
    Using MSP430mspgcc.dll, the open source implementation from the mspgcc
    project.

"ti" (default)
    Using MSP430.dll, the proprietary library from TI or a compatible one
    from a 3rd party supplier.

"parjtag"
    Old way of using MSP430mspgcc.dll. Use "mspgcc" instead.

Compatibility of backends:

    +-------------------------------------------+--------+--------+
    | Feature                                   | mspgcc | ti     |
    +===========================================+========+========+
    | 4 Wire JTAG                               | yes    | yes    |
    +-------------------------------------------+--------+--------+
    | 4 Wire JTAG on devices with spy-bi-wire   | yes(1) | no     |
    +-------------------------------------------+--------+--------+
    | using --spy-bi-wire option                | no     | yes    |
    +-------------------------------------------+--------+--------+
    | support for USB JTAG adapters             | no     | yes    |
    +-------------------------------------------+--------+--------+
    | unsing --funclet option                   | yes    | no     |
    +-------------------------------------------+--------+--------+

Notes:
    (1) Timing critical, may not work on all machines or at every try.


Examples
--------
``msp430-jtag -e``
    Only erase flash.

``msp430-jtag -eErw led.txt``
    Erase flash, erase check, download an executable, run it (reset) and wait,
    the keep it powered (from the parallel port).

``msp430-jtag led.txt``
    Download of an executable to en empty (new or erased) device. (Note that
    in new devices some of the first bytes in the information memory are
    random data. If data should be downloaded there, specify -eE.)

``msp430-jtag --go=0x220 ramtest.a43``
    Download a program into RAM and run it, may not work with all devices.

``msp430-jtag -u 0x0c00/1k``
    Get a memory dump in HEX, from the bootstrap loader.
    Or save the binary in a file::

      msp430-jtag -u 0x0c00 -s 1024 -f bin >dump.bin

    or as an intel-hex file::

      msp430-jtag -u 0x0c00 -s 1024 -f ihex >dump.a43

``msp430-jtag``
    Just start the user program (with a reset).

``cat led.txt|msp430-jtag -e -``
    Pipe the data from "cat" to msp430-jtag to erase and program the flash.
    (un*x example, don't forget the dash at the end of the line)


USB JTAG adapters
-----------------
This section only applies to Windows. On Linux replace MSP430.dll with
libMSP430.so etc.

USB JTAG adapters are supported through the MSP430.dlls from the adaptor
vendor. To enable its use, copy MSP430.dll to the ``bin\lib`` folder, where
``shared.zip`` is located. Optionally copy ``HIL.dll`` to the ``bin`` folder.

For example for MSP-FET430UIF from TI:

- download a the MSP430.dll binary from the downloads section in
  http://mspgcc.sf.net
- copy MSP430.dll to ``c:\mspgcc\bin`` (substitute the source and
  destination folders according to you own setup)

The windows installer already includes this library.

To use the first available MSP-FET430UIF::

    msp430-jtag -p TIUSB --upload=0x0ff0

The MSP-FET430UIF is registered as serial port. If more than one MSP-FET430UIF
is connected, find out which COM port the desired adapter is using with the
Device Manager. Then for example run::

    msp430-jtag -p COM5 --upload=0x0ff0

Linux users have to specify the serial port differently::

    msp430-jtag -p /dev/ttyUSB0 --upload=0x0ff0


History
-------
V1.0
    Public release.

V1.1
    Fix of verify error.

V1.2
    Use the verification during programming.

V1.3
    Mainerase, progress options, ihex output.

V2.0
    Updated implementation, new ctypes backend.

V2.1
    F2xx support, improved options for funclets.

V2.2
    Added --quiet and --secure. Try to use 3rd party MSP430 libraries so that
    USB adapters can be used. Allow multiple --upload with address ranges.

V2.3
    Added support for F2xx and MSP430X architectures. Improved 3rd party
    library support for Linux and Windows.

V3.0
    Rewrite command line frontend. Changed file type options, program flow
    specifiers.


References
----------
- Python: http://www.python.org

- ctypes: http://starship.python.net/crew/theller/ctypes
  This module is included in the standard distribution since Python 2.5:
  http://docs.python.org/lib/module-ctypes.html

- Texas Instruments MSP430 homepage, links to data sheets and application
  notes: http://www.ti.com/msp430

