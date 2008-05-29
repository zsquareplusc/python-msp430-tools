===================
 msp430-downloader
===================

Software to talk to the parallel port and USB JTAG adapters as seen with the
FET kits.
It is released under a free software license, see license.txt for more details.

(C) 2002-2008 Chris Liechti <cliechti@gmx.net>


Features
========

- understands ELF, TI-Text and Intel-hex object files
- download to Flash and/or RAM, erase flash, verify
- reset device
- upload a memory block MSP->PC (output as binary data or hex dump, ihex)
- written in Python, runs on Win32, Linux, BSD, ...
- use on command line, or in a Python script
- reset and wait for keypress (to run a device directly from the port
  power)
- TI/3rd party library support for USB JTAG adaptors (Windows only)


Installation
============
Binaries for Windows can be found in the download section of
http://mspgcc.sf.net

Linux users should refer to the last section.


Short introduction
==================
The tool is intended to be assigned to .a43 and .elf files (the mspgcc Windows
installer is doing this on request, by default).

Without configuration file a dialog box is shown, first to ask for the
programmer type, USB or parallel, and then the erase mode. These settings
and some additional options can be preconfigured in a configuration file.

The confiuration file togther with the binary can be bundled into a single ZIP
archive (extension must be renamed tp .z43). The name of the configuration file
is irrelevant as the first one with the ending ``.m43`` is loaded. The binary
is referenced in the configuration file, its name must match.

Example configuration file ``downloader-demo.m43``::

    ##########################################################################
    # This is a configuration file for msp430-download
    # It shows and describes all available options.
    #
    # When used as separate file:
    #   - copy a binary to the destination folder
    #   - copy this file to the destination folder
    #   - edit configuration for your needs
    #
    # When used with a ZIP file:
    #   - as above copy binary and configuration file, edit config
    #   - add all files to a zip file and rename it with to a .z43 ending
    #
    ##########################################################################

    [modes]
    ##########################################################################
    ## Erase modes:
    ##   "all" or "mass"     erase all memory
    ##   "main"              leave information memory
    ##   "ask"               ask the user
    erase_mode = mass

    ##########################################################################
    ## Interface selection:
    ##   "ask"               ask the user
    ##   "1" or "parallel"   parallel port. hint: numbers: LPT1, LPT2 etc
    ##   "TIUSB" or "COMn"   USB interface
    interface = parallel

    ##########################################################################
    ## Program in a loop, so that several targets can easily be programmed
    ## Single run and exit if not set.
    #loop = Yes

    ##########################################################################
    ## Ask again before programming.
    ## Recomended if no ther questions before programming are enabled, so that
    ## the user has a chance to abort. It is forced on if "loop" programming
    ## is on.
    #ask_start = Yes

    ##########################################################################
    ## Fake the progress bar and increment depending on state, not depending
    ## on data. Automaticaly set if the USB JTAG is used.
    fake_progess = No

    ##########################################################################
    ## For developers only. Remove key or set it to "no" for releases.
    ## When enabled, some diagnostic messages are printed to stdout.
    #debug = Yes

    ##########################################################################
    ## Backend selection:
    ##   "mspgcc"            use MSP430mspgcc.dll
    ##   "parjtag"           use _parjtag + MSP430mspgcc.dll (not recomended)
    ##   "ti"                use MSP430.dll from TI ord 3rd party
    ## Autodetect if key is not given.
    #backend = mspgcc

    [data]
    ##########################################################################
    ## A filename can be predefined.
    ## File open dialog will not be shown in this case.
    filename = leds.a43

    ##########################################################################
    ## If defined, a question is displayed, asking the user if he wants to
    ## see the readme.
    #readme = readme.txt

    ##########################################################################
    ## Select the viewer for the readme. Possible values are:
    ##   "browser"           the default webbrowser or text editor, depending
    ##                       on file ending
    ##   "internal"          use a message box (only for very short texts)
    viewer = browser



Building from source
====================

Requirements
------------
- Linux, BSD, Un*x or Windows PC
- Python 2.3+, EasyDialogs extension
- Parallel JTAG hardware with an MSP430 device connected
  (optionaly a USB adapter and a coresponding MSP430.dll on Windows)

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
