# setup script for py2exe to create the msp430-ram-usage.py.exe
# $Id: setup-ram-usage-py2exe.py,v 1.1 2005/06/14 11:41:16 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

os.chdir('..')
sys.path.append('.')

sys.argv.append("py2exe")

setup(
    name='msp430-ram-usage.py',
    version='0.5',
    options = {"py2exe":
        {
            'dist_dir': 'bin',
        }
    },
    console = ["msp430-ram-usage.py"],
    zipfile = "lib/shared-ram-usage.zip",
    #~ data_files = ['HIL.dll', 'MSP430mspgcc.dll'],
)
