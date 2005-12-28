# setup script for py2exe to create the msp430-jtag.exe
# $Id: setup-downloader-py2exe.py,v 1.4 2005/12/28 19:55:48 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

os.chdir('..')
sys.path.append('.')

sys.argv.append("py2exe")

setup(
    name='msp430-downloader',
    version='0.5',
    options = {"py2exe":
        {
            'dist_dir': 'bin',
            'excludes': ['javax.comm', 'macpath', 'TERMIOS', 'FCNTL', 'os2emxpath', '_parjtag'],
            'dll_excludes': ['HIL.dll', 'MSP430mspgcc.dll'],
            'optimize': 2,
        }
    },
    windows = [
        { 'script': "msp430-downloader.py",
          'icon_resources': [(0x0001, 'win32/downloader.ico')]
        },
    ],
    zipfile = "lib/shared-downloader.zip",
)
