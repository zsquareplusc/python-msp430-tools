This module provides MSP430 related tools that are written in Python.

Python 2.2 or newer should be used. The python package "msp430" can be
installed with "python setup.py install". These modules can be used
in user programs too.
The msp430-bsl and msp430-jtag tools are installed to the binary
directory /usr/local/msp430/bin and not in the Python library lie
the module above.

Descriptions:

msp430
    Python modules related to the MSP430.
    
    bsl.py
        Support for the boot strap loader.
        
    jtag.py
        Access to the mspgcc jtag tools using the MSP430mspgcc
        library.
    
    elf.py
        Reead elf object files and extract data segments.
    
    memory.py
        Memory implementation, used to store an memory image
        used to download to the MSP.
    
    util.py
        Different unitlity functions such as writing ihex
        files or making hex dumps.
    
    serial
        Copy of pyserial (http://pyserial.sf.net), used for bsl.py

demo
    Demonstration tools. Currently there are BSL and JTAG wrappers
    for Win32 using the NSIS installer system. The resulting
    executables contain everything thats needed to reprogram a
    device. Useful for field updaters, etc.

win32
    Windows related stuff, files to create executables and
    installers.

msp430-bsl.py
    Command line appliaction for the MSP430 Boot Strap Loader

msp430-jtag.py
    Command line appliaction for the MSP430 parallel JTAG adapter.

makefile
    Install the two command line tools and the Python library.


chris
$Id: readme.txt,v 1.1 2004/02/29 23:06:36 cliechti Exp $