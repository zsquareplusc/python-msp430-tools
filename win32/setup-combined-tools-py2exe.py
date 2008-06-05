# setup script for py2exe to create the executeable of all the python tools
# this setup uses one shared zip file for the library to save space
#
# $Id: setup-combined-tools-py2exe.py,v 1.5 2008/06/05 12:49:59 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

sys.path.insert(0, os.path.abspath('..'))
os.chdir('..')

sys.argv.append("py2exe")

setup(
    name = 'http://mspgcc.sourceforge.net',
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="http://mspgcc.sourceforge.net/",
    
    version = '1.0',
    options = { "py2exe":
        {
            'dist_dir': 'bin',
            'excludes': ['javax.comm', 'macpath', 'TERMIOS', 'FCNTL', 'os2emxpath', '_parjtag'],
            'dll_excludes': ['HIL.dll', 'MSP430mspgcc.dll'],
            'optimize': 2,
        }
    },
    console = [
        "msp430-bsl.py",
        "msp430-jtag.py",
        "msp430-dco.py",
        "ihex2titext.py", "titext2ihex.py",
        "msp430-ram-usage.py",
        "msp430-hexdump.py",
        "msp430-miniterm.py",
    ],
    windows = [
        {
            'script': "msp430-downloader.py",
            'icon_resources': [(0x0001, 'win32/downloader.ico')]
        },
    ],
    zipfile = "lib/shared.zip",
)
