# setup script for py2exe to create the msp430-bsl.exe
# $Id: setup-bsl-py2exe.py,v 1.1 2004/03/01 00:11:55 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

os.chdir('..')

sys.argv.append("py2exe")

setup(
    name='pybsl',
    version='0.5',
    options = {"py2exe":
        {
            'dist_dir': 'bin',
            'excludes': ['javax.comm'],
        }
    },
    console = ["msp430-bsl.py"],
    zipfile = "lib/shared-bsl.zip",
)
