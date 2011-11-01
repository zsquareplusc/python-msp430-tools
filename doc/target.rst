==============
 Target Tools
==============

``msp430.bsl.target``
=====================
``python -m msp430.bsl.target -h [OPTIONS] [FILE [FILE...]]``:

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


``msp430.bsl5.hid``
===================
``python -m msp430.bsl5.hid [OPTIONS] [FILE [FILE...]]``:

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


``msp430.bsl5.uart``
====================
``python -m msp430.bsl5.uart -h [OPTIONS] [FILE [FILE...]]``:

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

``msp430.jtag.dco``
===================
``python -m msp430.jtag.dco [options] frequency``:

MSP430 clock calibration utility V1.1

This tool can measure the internal oscillator of F1xx, F2xx and F4xx devices,
display the supported frequencies, or run a software FLL to find the settings
for a specified frequency.

The target device has to be connected to the JTAG interface.

Examples:
  See min and max clock speeds:
    dco.py --measure

  Get clock settings for 2.0MHz +/-1%:
    dco.py --tolerance=0.01 2.0e6

  Write clock calibration for 1.5MHz to the information memory at 0x1000:
    dco.py 1.5e6 BCSCTL1@0x1000 DCOCTL@0x1000

Use it at your own risk. No guarantee that the values are correct.

Options:
  -h, --help            show this help message and exit
  -o FILE, --output=FILE
                        write result to given file
  --dcor                use external resistor
  -d, --debug           print debug messages
  -l LPT, --lpt=LPT     set the parallel port
  -m, --measure         measure min and max clock settings and exit
  -c, --calibrate       Restore calibration values on F2xx devices
  -t TOLERANCE, --tolerance=TOLERANCE
                        set the clock tolerance as factor. e.g. 0.01 means 1%
                        (default=0.005)
  --define              output #defines instead of assignments
  --erase=ERASE         erase flash page at given address. Use with care!

``msp430.jtag.target``
======================
``python -m msp430.jtag.target [OPTIONS] [FILE [FILE...]]``:

Options:
  -h, --help            show this help message and exit
  --debug               print debug messages and tracebacks (development mode)
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
    Mass erase and program from file: "/home/lch/python-
    msp430-tools/msp430/jtag/target.py -e firmware.elf" Dump information
    memory: "/home/lch/python-msp430-tools/msp430/jtag/target.py
    --upload=0x1000-0x10ff"

``msp430.jtag.profile``
=======================
``python -m msp430.jtag.profile [OPTIONS]``:

Options:
  -h, --help            show this help message and exit
  -v, --verbose         show more messages (can be given multiple times)
  -o FILENAME, --output=FILENAME
                        write result to given file

``msp430.gdb.target``
=====================
``python -m msp430.gdb.target [OPTIONS] [FILE [FILE...]]``:

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

  Connection:
    -c HOST:PORT, --connect=HOST:PORT
                        TCP/IP host name or ip and port of GDB server
                        (default: localhost:2000)

