# setup script for py2exe to create the msp430-bsl.exe
# $Id: setup-bsl-py2exe.py,v 1.3 2004/11/15 12:43:49 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

os.chdir('..')
sys.path.append('.')

sys.argv.append("py2exe")

setup(
    name='msp430-bsl',
    version='0.5',
    options = {"py2exe":
        {
            'dist_dir': 'bin',
            'excludes': ['javax.comm', 'macpath', 'TERMIOS', 'FCNTL', 'os2emxpath'],
        }
    },
    console = ["msp430-bsl.py"],
    zipfile = "lib/shared-bsl.zip",
)
