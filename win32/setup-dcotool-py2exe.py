# setup script for py2exe to create the msp430-jtag.exe
# $Id: setup-dcotool-py2exe.py,v 1.1 2005/12/29 04:00:01 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

os.chdir('..')
sys.path.append('.')

sys.argv.append("py2exe")

setup(
    name='msp430-dco',
    version='1.0',
    options = {"py2exe":
        {
            'dist_dir': 'bin',
            'excludes': ['javax.comm', 'macpath', 'TERMIOS', 'FCNTL', 'os2emxpath', '_parjtag'],
            'dll_excludes': ['HIL.dll', 'MSP430mspgcc.dll'],
            'optimize': 2,
        }
    },
    console = [
        { 'script': "msp430-dco.py"},
    ],
    zipfile = "lib/shared-dcotool.zip",
)
