msp430-jtag
===========

Software to talk to the parallel port and USB JTAG adapters as seen with the
FET kits.
It is released under a free software license, see license.txt for more details.

(C) 2002-2008 Chris Liechti <cliechti@gmx.net>


Features
--------

- understands ELF, TI-Text and Intel-hex object files
- download to Flash and/or RAM, erase flash, verify
- reset device
- upload a memory block MSP->PC (output as binary data or hex dump, ihex)
- written in Python, runs on Win32, Linux, BSD, ...
- use on command line, or in a Python script
- reset and wait for keypress (to run a device directly from the port
  power)
- TI/3rd party library support for USB JTAG adaptors (Windows only)


Requirements
------------
- Linux, BSD, Un*x or Windows PC
- Python 2.0 or newer, 2.3+ recomeded
- Parallel JTAG hardware with an MSP430 device connected
  (optionaly a USB adapter and a coresponding MSP430.dll on Windows)


Installation
------------
Binaries for Windows can be found in the download section of
http://mspgcc.sf.net

Linux users should refer to the next section.


Building from source
--------------------
The libraries from the CVS module jtag/* have to be built. This includes
MSP430mspgcc.dll and HIL.dll (respectively libMSP430mspgcc.so and
libHIL.so ony Un*x platforms)

On Linux/Un*x Python 2.2+ is needed. On some distributions is Python 1.5.2
installed per default. You may meed to change the first line in the script
from "python" to "python2". Maybe Python 2.x is in a separate package that
has to be installed. There are rpm and deb binary packages and a source
tarball available through the Python homepage.

There prefered backend is the a ctypes version, which means just
libMSP430mspgcc.so/dll libHIL.so/HIL.dll is needed and of course the ctypes
python extension. The ctypes backend is also capable of using the closed
source MSP430.dll/libMSP430.so library from TI or 3rd party supliers.

Alternatively there is the older python extension module implemented in c
called _parjtag.so/dll. Its sources can be found in the "python" folder of
the CVS repository mentioned above. However, not all of the newest features
may work with this backend.


Short introduction
------------------
This software uses the JTAG hardware that comes with the FET kits. It is
connected to the parallel port. Using 3rd party backends it is also possible
to use USB programmers.

The program can be started by typing ``msp430-jtag`` when installed correctly
If it's used from the source directory use "python msp430-jtag.py".


USAGE: msp430-jtag [options] [file]
Version: 2.2

If "-" is specified as file the data is read from stdin.
A file ending with ".txt" is considered to be in TI-Text format all
other filenames are considered to be in Intel HEX format.

General options:
  -h, --help            Show this help text.
  --help-backend        Show help about the different backends.
  -D, --debug           Increase level of debug messages. This won't be
                        very useful for the average user.
  -I, --intelhex        Force input file format to Intel HEX.
  -T, --titext          Force input file format to be TI-Text.
  -R, --ramsize         Specify the amount of RAM to be used to program
                        flash (default, if --ramsize is not given is
                        autodetect).

Connection:
  -l, --lpt=name        Specify an other parallel port or serial port for the
                        USBFET (the later requires MSP430.dll instead of
                        MSP430mspgcc.dll).
                        (defaults to "LPT1" ("/dev/parport0" on Linux))
  --slowdown=microsecs  Artificially slow down the communication. Can help
                        with long lines, try values between 1 and 50 (parallel
                        port interface with mspgcc's HIL library only).
                        (experts only)
  --backend=backend     Select an alternate backend. See --help-backend for
                        more information.

.. note:: On Windows, use "TIUSB" or "COM5" etc if using MSP430.dll from TI.
          If a MSP430.dll is found it is prefered, otherwise MSP430mspgcc.dll
          is used.
.. note:: --slowdown > 50 can result in failures for the ramsize autodetection
          (use --ramsize option to fix this). Use the --debug option and watch
          the outputs. The DCO clock adjustment and thus the Flash timing may
          be inaccurate for large values.

Funclets:
  -f, --funclet         The given file is a funclet (a small program to
                        be run in RAM).
  --parameter=option    Pass parameters to funclets.
                        Registers can be written like "R15=123" or "R4=0x55"
                        A string can be written to memory with "0x2e0=hello"
                        --parameter can be given more than once.
  --result=value        Read results from funclets. "Rall" reads all registers
                        (case insensitive) "R15" reads R15 etc. Address ranges
                        can be read with "0x2e0-0x2ff". See also --upload.
                        --result can be given more than once.
  --timeout=value       Abort the funclet after the given time in seconds
                        if it does not exit no itself. (default 1)

.. note:: Writing and/or reading RAM before and/or after running a funclet may
          not work as expected on devices with the JTAG bug like the F123.
.. note:: Only possible with MSP430mspgcc.dll, not other backends.

Program flow specifiers:
  -e, --masserase       Mass Erase (clear all flash memory).
                        Note: SegmentA on F2xx is NOT erased, that must be
                        done separately with --erase=0x1000
  -m, --mainerase       Erase main flash memory only.
  --eraseinfo           Erase info flash memory only (0x1000-0x10ff).
  --erase=address       Selectively erase segment at the specified address.
  --erase=adr1-adr2     Selectively erase a range of segments.
  -E, --erasecheck      Erase Check by file.
  -p, --program         Program file.
  -v, --verify          Verify by file.
  --secure              Blow JTAG security fuse.
  
                        .. warning:: This is not reversible, use with care!
                                
                        .. note:: Not supported with the simple parallel port
                                  adapter (7V source required).

The order of the above options matters! The table is ordered by normal
execution order. For the options "E", "p" and "v" a file must be specified.
Program flow specifiers default to "p" if a file is given.
Don't forget to specify "e", "eE" or "m" when programming flash!
"p" already verifies the programmed data, "v" adds an additional
verification through uploading the written data for a 1:1 compare.
No default action is taken if "p" and/or "v" is given, say specifying
only "v" does a "check by file" of a programmed device.

Data retrieving:
  -u, --upload=addr     Upload a datablock (see also: --size).
                        It is also possible to use address ranges. In that
                        case, multiple --upload parameters are allowed.
  -s, --size=num        Size of the data block to upload (Default is 2).
  -x, --hex             Show a hexadecimal display of the uploaded data.
                        This is the default format, see also --bin, --ihex.
  -b, --bin             Get binary uploaded data. This can be used
                        to redirect the output into a file.
  -i, --ihex            Uploaded data is output in Intel HEX format.
                        This can be used to clone a device.

Do before exit:
  -g, --go=address      Start programm execution at specified address.
                        This implies option "w" (wait)
  -r, --reset           Reset connected MSP430. Starts application.
                        This is a normal device reset and will start
                        the programm that is specified in the reset
                        interrupt vector. (see also -g)
  -w, --wait            Wait for <ENTER> before closing parallel port.
  --no-close            Do not close port on exit. Allows to power devices
                        from the parallel port interface.

Address parameters for --erase, --upload, --size can be given in
decimal, hexadecimal or octal.

Examples:
    Mass erase and program from file: "msp430-jtag -e firmware.elf"
    Dump Information memory: "msp430-jtag --upload=0x1000-0x10ff"


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

    Aleternatively, it is possible run ``msp430-jtag -w`` to power the
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
    from a 3rd pary supplier.

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

``msp430-jtag -eErw 6port.a43``
    Erase flash, erase check, download an executable, run it (reset) and wait,
    the keep it powered (from the parallel port).

``msp430-jtag -mS -R 2048 6port.a43``
    Use ramsize option on a device with 2k RAM to speed up download. Of
    course any value from 128B up to the maximum a device has is allowed.
    The progress and mainerase options are also activated. Only erasing the
    main memory is useful to keep calibration data in the information memory.

``msp430-jtag 6port.a43``
    Download of an executable to en empty (new or erased) device. (Note that
    in new devices some of the first bytes in the information memory are
    random data. If data should be downloaded there, specify -eE.)

``msp430-jtag --go=0x220 ramtest.a43``
    Download a program into RAM and run it, may not work with all devices.

``msp430-jtag -f blinking.a43``
    Download a program into RAM and run it. It must be a special format with
    "startadr", "entrypoint", "exitpoint" as the first three words in the
    data and it must end on "jmp $". See MSP430mspgcc sources for more info.

``msp430-jtag -u 0x0c00 -s 1024``
    Get a memory dump in HEX, from the bootstrap loader.
    Or save the binary in a file::
    
      msp430-jtag -u 0x0c00 -s 1024 -b >dump.bin
    
    or as an intel-hex file::
    
      msp430-jtag -u 0x0c00 -s 1024 -i >dump.a43

``msp430-jtag``
    Just start the user program (with a reset).

``cat 6port.a43|msp430-jtag -e -``
    Pipe the data from "cat" to msp430-jtag to erase and program the flash.
    (un*x example, don't forget the dash at the end of the line)


USB JTAG adapters
-----------------
This section only applies to Windows. On linux replace MSP430.dll with
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

    msp430-jtag -l TIUSB --upload=0x0ff0

The MSP-FET430UIF is registered as serial port. If more than one MSP-FET430UIF
is connected, find out which COM port the desired adapter is using with the
Device Manager. Then for example run::

    msp430-jtag -l COM5 --upload=0x0ff0

Linux users have to specify the serial port differently::

    msp430-jtag -l /dev/ttyUSB0 --upload=0x0ff0


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


References
----------
- Python: http://www.python.org

- ctypes: http://starship.python.net/crew/theller/ctypes
  This module is included in the standard distribution since Python 2.5:
  http://docs.python.org/lib/module-ctypes.html

- Texas Instruments MSP430 Homepage, links to Datasheets and Application
  Notes: http://www.ti.com/msp430

