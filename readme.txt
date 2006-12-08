This module provides MSP430 related tools that are written in Python.

Python 2.2 or newer should be used. The python package "mspgcc" can be
installed with "python setup.py install". These modules can be used in user
programs too.
The msp430-bsl and msp430-jtag tools are installed to the binary directory
/usr/local/msp430/bin and not in the Python library like the module above.

Descriptions:

mspgcc
    Python modules related to the MSP430.
    
    bsl.py
        Support for the boot strap loader.
        
    jtag.py
        Access to the mspgcc jtag tools using the MSP430mspgcc library.
    
    elf.py
        Reead elf object files and extract data segments.
    
    memory.py
        Memory implementation, used to store an memory image used to download
        to the MSP.
    
    util.py
        Different utility functions such as writing ihex files or making
        hex dumps.
    
    HIL.py
        Access to the HIL.dll/libHIL.so

    hilspi.py
        An SPI master over the JTAG lines.

    serial
        Copy of pyserial (http://pyserial.sf.net), used for bsl.py

demo
    Demonstration tools. Currently there are BSL and JTAG wrappers for Win32
    using the NSIS installer system. The resulting executables contain
    everything that's needed to reprogram a device. Useful for field updaters,
    etc.
    
    mmc.py: a Python demo that reads an MMC card connected to the JTAG port.
    See source file for wiring.

win32
    Windows related stuff, files to create executables and installers.

msp430-bsl.py
    Command line application for the MSP430 Boot Strap Loader. Erasing,
    programming, uploading of flash and RAM. 

msp430-dco.py
    Command line application for the MSP430 parallel JTAG adapter. Measure
    or callibrate the DCO clock.

msp430-downloader.py
    Small program, suitable for file associations, so that double clicking an
    elf or a43 file can be used to download via JTAG.

msp430-jtag.py
    Command line application for the MSP430 parallel JTAG adapter. Erasing,
    programming, uploading of flash and RAM. Additionaly it can run funclets.

makefile
    Install the two command line tools and the Python library.


chris

$Id: readme.txt,v 1.5 2006/12/08 22:05:56 cliechti Exp $