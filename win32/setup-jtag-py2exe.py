# setup script for py2exe to create the msp430-jtag.exe
# $Id: setup-jtag-py2exe.py,v 1.1 2004/03/01 00:11:55 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

os.chdir('..')

sys.argv.append("py2exe")

setup(
    name='pyjtag',
    version='0.5',
    options = {"py2exe":
        {
            'dist_dir': 'bin',
            'dll_excludes': ['HIL.dll', 'MSP430mspgcc.dll'],
        }
    },
    console = ["msp430-jtag.py"],
    zipfile = "lib/shared-jtag.zip",
    #~ data_files = ['HIL.dll', 'MSP430mspgcc.dll'],
)
