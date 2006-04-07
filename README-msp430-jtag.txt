msp430-jtag
===========

Software to talk to the parallel port JTAG adapter as seen with the FET kits.
It is released under a free software license, see license.txt for more details.

(C) 2002-2006 Chris Liechti <cliechti@gmx.net>


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

Linux users should refer to the next secion.


Building from source
--------------------
The libraries from the CVS module jtag/* have to be built.

On Linux/Un*x Python 2.2+ is needed. On some distributions is Python 1.5.2
installed per default. You may meed to change the first line in the script
from "python" to "python2". Maybe Python 2.x is in a separate package that
has to be installed. There are rpm and deb binary packages and a source
tarball available through the Python homepage.

There prefered backend is the a ctypes version, which means just
libMSP430mspgcc.so/dll libHIL.so/HIL.dll is needed and of course the ctypes
python extension.

Alternatively _parjtag.so/dll from the jtag archive can be copied to the same
directory as msp430-jtag.py or to a directory on the PATH.
It's recomended to install jtag.py as "msp430-jtag" in a directory in the PATH
and make it executable.


Short introduction
------------------
This software uses the JTAG hardware that comes with the FET kits. It is
connected to the parallel port.

The program can be started by typing "msp430-jtag" when installed correctly
If its used from the source directory use "python jtag.py".


USAGE: msp430-jtag.py [options] [file]
Version: 2.2

If "-" is specified as file the data is read from stdin.
A file ending with ".txt" is considered to be in TI-Text format all
other filenames are considered to be in Intel HEX format.

General options:
  -h, --help            Show this help screen.
  -D, --debug           Increase level of debug messages. This won't be
                        very useful for the average user.
  -I, --intelhex        Force input file format to Intel HEX.
  -T, --titext          Force input file format to be TI-Text.
  -R, --ramsize         Specify the amount of RAM to be used to program
                        flash (default, if --ramsize is not given is
                        autodetect).

Connection:
  -l, --lpt=name        Specify an other (parallel) port.
                        (defaults to "LPT1" ("/dev/parport0" on Linux))

Note: On Windows, use "TIUSB" or "COM5" etc if using MSP430.dll from TI.
      If a MSP430.dll is found it is prefered, otherwise MSP430mspgcc.dll
      is used.

Funclets:
  -f, --funclet         The given file is a funclet (a small program to
                        be run in RAM).
  --parameter=<key>=<value>   Pass parameters to funclets.
                        Registers can be written like "R15=123" or "R4=0x55"
                        A string can be written to memory with "0x2e0=hello"
                        --parameter can be given more than once
  --result=value        Read results from funclets. "Rall" reads all registers
                        (case insensitive) "R15" reads R15 etc. Address ranges
                        can be read with "0x2e0-0x2ff". See also --upload.
                        --result can be given more than once.
  --timeout=value       Abort the funclet after the given time in seconds
                        if it does not exit no itself. (default 1)

Note: writing and/or reading RAM before and/or after running a funclet may not
      work as expected on devices with the JTAG bug like the F123.
Note: Only possible with MSP430mspgcc.dll, not other backends.

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
                        Note: This is not reversible, use with care!
                        Note: Not supported with the simple parallel port
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
    Mass erase and write file: "msp430-jtag.py -e firmware.elf"
    Dump Information memory: "msp430-jtag.py --upload=0x1000-0x10ff"



NOTE:   Some versions of the Texas Instruments MSP430 Development Tool
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
This section only applies to Windows (currently).

USB JTAG adapters are supported trough the MSP430.dlls from the adaptor
vendor. To enable its use, copy MSP430.dll to the
``bin\lib`` folder, where ``shared.zip`` is located.
Optionally copy ``HIL.dll`` to the ``bin`` folder.

For example for MSP-FET430UIF from TI:
- download and install CCE (Code Composer, the free version)
- install the USB driver that comes with CCE, you'll also need to install
  CCE itself, as that unpacks the MSP430.dll.
- copy MSP430.dll and HIL.dll (or simply all the files you find in the folder)
  from ``C:\Program Files\CCEssentials\FTSuite\emulation\msp430`` to
  ``c:\mspgcc\bin\lib`` (substitute the source and destination folders
  according to you own setup)
- reboot

To use the first available MSP-FET430UIF::

    msp430-jtag -l TIUSB --upload=0x0ff0

The MSP-FET430UIF is registered as serial port. If more than one MSP-FET430UIF
is connected, find out which COM port the desired adapter is using with the
Device Manager. Then for example run::

    msp430-jtag -l COM5 --upload=0x0ff0



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


References
----------
- Python: http://www.python.org

- ctypes: http://starship.python.net/crew/theller/ctypes

- Texas Instruments MSP430 Homepage, links to Datasheets and Application
  Notes: http://www.ti.com/msp430

