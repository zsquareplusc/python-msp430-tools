msp430-bsl
==========

MSP430 Boot Strap Loader software for F1xx, F2xx, F4xx.

Features
--------

- Understands ELF, TI-Text and Intel-hex object files.
- Download to Flash and/or RAM, erase, verify, ...
- Reset and wait for key press (to run a device directly from the port
  power).
- Load address into R0/PC and run.
- Password file can be any data file, e.g. the one used to program the
  device in an earlier session.
- Upload a memory block MSP->PC (output as binary data or hex dump).
- Written in Python, runs on Win32, Linux, BSD (and others).
- Use on command line, or in a Python script.
- Downloadable BSL for larger devices (integrated).
- Baud rate change for newer MSP430-BSLs.
- Test and reset lines can be inverted or exchanged for non standard BSL
  hardware. Test singal on TX line is also possible.


Requirements
------------
- Linux, BSD, Un*x or Windows PC
- Python 2.5 or newer
- pySerial (2.4 or newer recommended)
- BSL hardware with an MSP430 device connected to a serial port


Short introduction
------------------
First the MSP430 BSL hardware is needed. An example schematics can be found
in the application note "slaa96b" from TI (see references). Then this
program can be used to communicate between the PC and the MSP430 device.

The program can be started by typing "msp430-bsl" in a console.
To run it in the source directory, use "python msp430-bsl"

Usage: msp430.bsl.target [OPTIONS] [FILE [FILE...]]

Options:
  -h, --help            show this help message and exit
  -d, --debug           print debug messages and tracebacks (development mode)
  -v, --verbose         show more messages (can be given multiple times)
  -q, --quiet           suppress all messages
  --time                measure time
  -S, --progress        show progress while programming

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

  Communication settings:
    -p PORT, --port=PORT
                        Use com-port
    --invert-test       invert RTS line
    --invert-reset      invert DTR line
    --swap-reset-test   exchenage RST and TEST signals (DTR/RTS)
    --test-on-tx        TEST/TCK signal is muxed on TX line

  BSL settings:
    --no-start          no not use ROM-BSL start pattern on RST+TEST/TCK
    -s SPEED, --speed=SPEED
                        change baud rate (default 9600)
    --password=FILE     transmit password before doing anything else, password
                        is given in given (TI-Text/ihex/etc) file
    --ignore-answer     do not wait for answer to BSL commands
    --control-delay=CONTROL_DELAY
                        set delay in seconds (float) for BSL start pattern
    --replace-bsl       download replacement BSL (V1.50) for F1x and F4x
                        devices with 2k RAM
    --erase-cycles=EXTRA_ERASE_CYCLES
                        configure extra erase cycles (e.g. very old F149 chips
                        require this for --main-erase)



If it says ``command failed (DATA_NAK)`` it's probably because no or a wrong
password was specified, while a ``ERROR:BSL:Sync failed, aborting...`` is
typical when the BSL could not be started at all.


Examples
--------
``led.txt`` in the following examples is a place holder for some sort of binary
for the MSP430. A ``led.txt`` that contains an example in TI-Text format can be
built from the code in ``examples/asm/led``.

``msp430-bsl -e``
        Only erase flash.

``msp430-bsl -eErw led.txt``
        Erase flash, erase check, download an executable, run it (reset)
        and wait.

        Old F149 devices need additional erase cycles! Use the
        ``--erase-cycles`` option in this case (``--erase-cycles 20`` will be
        OK is most cases)

``msp430-bsl led.txt``
        Download of an executable to en empty (new or erased) device.
        (Note that in new devices, some of the first bytes in the
        information memory are random data. If data should be
        downloaded there, specify -e.)


``msp430-bsl --upload 0x0c00/1024 --password led.txt``
        Get a memory dump in HEX, from the bootstrap loader (on a device
        that was previously programmed with led.txt and therefore needs
        a specific password):

``msp430-bsl -rw``
        Just start the user program (with a reset) and wait.


``cat led.txt|msp430-bsl -e -``
        Pipe the data from "cat" to the BSL to erase and program the
        flash. (un*x example, don't forget the dash at the end of the
        line)

``msp430-bsl --replace-bsl -e -s 38400 led.txt``
        First download the internal replacement BSL and then use it
        to program at 38400 baud. Only works with targets with more
        than 1kB of RAM. Newer devices with already know this command, in that
        case omit the ``--replace-bsl``


History
-------
V1.4
    uses improved serial library,
    support for BSL download to MSP,
    support for higher baudrates (up to 38400)

V1.5
    ELF file support,
    replacement BSLs are now internal

V2.0
    New implementation. Some command line options have been renamed or
    replaced.


References
----------
- Python: http://www.python.org

- pySerial: Serial port extension for Python
  http://pypi.python.org/pypi/pyserial

- slaa89.pdf: "Features of the MSP430 Bootstrap Loader in the
  MSP430F1121", TI, http://www.ti.com/msp430

- slaa96b.pdf: "Application of Bootstrap Loader in MSP430 With Flash
  Hardware and Software Proposal", TI

- Texas Instruments MSP430 Homepage, links to data sheets and application
  notes: http://www.ti.com/msp430

