msp430-bsl5
===========

MSP430 Boot Strap Loader software for F5xx, F6xx.

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
- USB-HID BSL version:

  - Automatic detection of HID device.

- UART BSL version:

  - Baud rate change
  - Test and reset lines can be inverted and/or exchanged for non standard BSL
    hardware. Test singal on TX line is also possible.


Requirements
------------
- Linux, BSD, Un*x or Windows PC

- Python 2.6 or newer

- USB support requires:

  - "pywinusb" library on Windows
  - "rawhid" kernel driver on Linux
  - other platforms are currently not supported

- pySerial (2.4 or newer recommended)

- MSP430 F5x / F6x with UART BSL connected to a serial port or a USB capable
  device connected to USB.


Short introduction
------------------
There are separate command line fontends for the USB and UART version:

- ``python -m msp430.bsl5.uart``  - UART version
- ``python -m msp430.bsl5.hid``   - USB version

Usage: hid.py [OPTIONS] [FILE [FILE...]]

Options:
  -h, --help            show this help message and exit
  --debug               print debug messages and tracebacks (development mode)
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
    -d DEVICE, --device=DEVICE
                        device name (default: auto detection)

  BSL settings:
    --password=FILE     transmit password before doing anything else, password
                        is given in given (TI-Text/ihex/etc) file


The UART version only differs in the options controlling the "Communication"
and "BSL" settings:

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

Examples
--------
``led.txt`` in the following examples is a place holder for some sort of binary
for the MSP430. A ``led.txt`` that contains an example in TI-Text format can be
built from the code in ``examples/asm/led5x``.

``python -m msp430.bsl5.hid -e``
        Only erase flash.

``python -m msp430.bsl5.uart -eErw led.txt``
        Erase flash, erase check, download an executable, run it (reset)
        and wait.

``python -m msp430.bsl5.hid led.txt``
        Download of an executable to en empty (new or erased) device.
        (Note that in new devices, some of the first bytes in the
        information memory are random data. If data should be
        downloaded there, specify -e.)


``python -m msp430.bsl5.hid --upload 0xf000/1024 --password led.txt``
        Get a memory dump in HEX, from a part of the memory (on a device
        that was previously programmed with led.txt and therefore needs
        a specific password):

`python -m msp430.bsl5.uart -rw``
        Just start the user program (with a reset) and wait.


``cat led.txt|python -m msp430.bsl5.uart -e -``
        Pipe the data from "cat" to the BSL to erase and program the
        flash. (un*x example, don't forget the dash at the end of the
        line)

``python -m msp430.bsl5.uart -e -s 38400 led.txt``
        Change to faster baud rate for download.


Tips & Tricks
-------------
USB-HID Linux permissions
    The USB HID device simply works when plugged in under Linux and the tool can use
    the device when the "rawhid" kernel module is present. It will create
    ``/dev/rawhid*`` devices. However, those devices are usually only writeable by
    root. To automatically change the permissions of the device, the following udev
    rule can be applied.

    Create a file, e.g. ``/etc/udev/rules.d/20-msp430-hid.rules`` with the
    following contents::

        SUBSYSTEM=="hidraw", ATTRS{idVendor}=="2047", ATTRS{idProduct}=="0200" , MODE="0666"


History
-------
V1.0
    New tool.

References
----------
- Python: http://www.python.org

- pySerial: Serial port extension for Python
  http://pypi.python.org/pypi/pyserial

- pywinusb: USB HID library
  http://pypi.python.org/pypi/pywinusb/

- slau319a.pdf: "MSP430 Programming Via the Bootstrap Loader"
  http://www.ti.com/msp430

- Texas Instruments MSP430 Homepage, links to data sheets and application
  notes: http://www.ti.com/msp430

