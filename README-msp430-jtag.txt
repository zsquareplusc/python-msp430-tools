pyJTAG
------

Software to talk to the parallel port JTAG PCB as seen with the FET kits.
It is released under a free software license,
see license.txt for more details.

(C) 2002-2004 Chris Liechti <cliechti@gmx.net>

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

Requirements
------------
- Linux, BSD, Un*x or Windows PC
- Python 2.0 or newer, 2.2 recomeded
- Parallel JTAG hardware with an MSP430 device connected

Installation
------------
Binaries for Windows and other Linux/Un*x like OS can be found in the
downloads section of http://mspgcc.sf.net

XXX

Bilding from source
-------------------
The libraries from the CVS module jtag/* have to be built.

On Linux/Un*x just Python 2.2+ is needed. On some distributions is Python 1.5.2
installed per default. You may meed to change the first line in the script
from "python" to "python2". Maybe Python 2.x is in a separate package that
has to be installed. There are rpm and deb binary packages and a source
tarball available through the Python homepage.

_parjtag.so/dll from the jtag archive can be copied to the same directory as
jtag.py or to a directory on the PATH.
It's recomended to install jtag.py as "msp430-jtag" in a directory in the PATH
and make it executable.

XXX

Short introduction
------------------
This software uses the JTAG hardware that comes with the FET kits. It is
connected to the parallel port.

The program can be started by typing "msp430-jtag" when installed correctly
If its used from the source directory use "python jtag.py".



USAGE: msp430-jtag [options] [file]
If "-" is specified as file the data is read from stdin.
A file ending with ".txt" is considered to be in TIText format all
other filenames are considered to be in IntelHex format.

General options:
  -h, --help            Show this help screen.
  -l, --lpt=name        Specify an other parallel port.
                        (defaults to LPT1 (/dev/parport0 on unix)
  -D, --debug           Increase level of debug messages. This won't be
                        very useful for the average user...
  -I, --intelhex        Force fileformat to IntelHex
  -T, --titext          Force fileformat to be TIText
  -f, --funclet         The given file is a funclet (a small program to
                        be run in RAM)
  -R, --ramsize         Specify the amont of RAM to be used to program
                        flash (default 256).

Program Flow Specifiers:

  -e, --masserase       Mass Erase (clear all flash memory)
  -m, --mainerase       Erase main flash memory only
  --eraseinfo           Erase info flash memory only (0x1000-0x10ff)
  --erase=address       Selectively erase segment at the specified address
  -E, --erasecheck      Erase Check by file
  -p, --program         Program file
  -v, --verify          Verify by file

The order of the above options matters! The table is ordered by normal
execution order. For the options "Epv" a file must be specified.
Program flow specifiers default to "p" if a file is given.
Don't forget to specify "e" or "eE" when programming flash!
"p" already verifies the programmed data, "v" adds an additional
verification though uploading the written data for a 1:1 compare.
No default action is taken if "p" and/or "v" is given, say specifying
only "v" does a check by file of a programmed device.

Data retreiving:
  -u, --upload=addr     Upload a datablock (see also: -s).
  -s, --size=num        Size of the data block do upload. (Default is 2)
  -x, --hex             Show a hexadecimal display of the uploaded data.
                        (Default)
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


Examples
--------
msp430-jtag -e
        Only erase flash.

msp430-jtag -eErw 6port.a43
        Erase flash, erase check, download an executable, run it (reset)
        and wait.

msp430-jtag -mS -R 2048 6port.a43
        Use ramsize option on a device with 2k RAM to speed up
        download. Of course any value from 128B up to the maximum
        a device has is allowed.
        The progress and mainerase options are also activated.
        Only erasing the main memory is useful to keep calibration
        data in the information memory.

msp430-jtag 6port.a43
        Download of an executable to en empty (new or erased) device.
        (Note that in new devices some of the first bytes in the
        information memory are random data. If data should be
        downloaded there, specify -eE.)

msp430-jtag --go=0x220 ramtest.a43
        Download a program into RAM and run it, may not work
        with all devices.

msp430-jtag -f blinking.a43
        Download a program into RAM and run it. It must be
        a special format with "startadr", "entrypoint",
        "exitpoint" as the first three words in the data
        and it must end on "jmp $". See MSP430debug sources
        for more info.

msp430-jtag -u 0x0c00 -s 1024
        Get a memory dump in HEX, from the bootstrap loader.
        or save the binary in a file:
          msp430-jtag -u 0x0c00 -s 1024 -b >dump.bin
        or as an intel-hex file:
          msp430-jtag -u 0x0c00 -s 1024 -i >dump.a43

msp430-jtag -r
        Just start the user program (with a reset).

cat 6port.a43|msp430-jtag -e -
        Pipe the data from "cat" to jtag.py to erase and program the
        flash. (un*x example, don't forget the dash at the end of the
        line)

History
-------
1.0     public release
1.1     fix of verify error
1.2     use the verification during programming
1.3     mainerase, progress options, ihex output

References
----------
- Python: http://www.python.org

- Texas Instruments MSP430 Homepage, links to Datasheets and Application
  Notes: http://www.ti.com/sc/msp430

