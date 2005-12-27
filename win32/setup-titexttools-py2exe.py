# setup script for py2exe to create the ihex2titext.exe and titext2ihex.exe
# $Id: setup-titexttools-py2exe.py,v 1.1 2005/12/27 14:58:28 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

os.chdir('..')
sys.path.append('.')

sys.argv.append("py2exe")

setup(
    name='titexttools',
    version='1.0',
    options = {"py2exe":
        {
            'dist_dir': 'bin',
        }
    },
    console = ["ihex2titext.py", "titext2ihex.py"],
    zipfile = "lib/shared-titexttools.zip",
)
