# setup script for py2exe to create the msp430-jtag.exe
# $Id: setup-downloader-py2exe.py,v 1.1 2004/09/08 14:58:01 cliechti Exp $

from distutils.core import setup
import glob, sys, py2exe, os

os.chdir('..')
sys.path.append('.')

sys.argv.append("py2exe")

setup(
    name='downloader',
    version='0.5',
    options = {"py2exe":
        {
            'dist_dir': 'bin',
            'dll_excludes': ['HIL.dll', 'MSP430mspgcc.dll'],
            'optimize': 2,
        }
    },
    windows = [
        { 'script': "msp430-downloader.py",
            #~ 'icon_resources': [(0x0001, 'bigicon.ico')]
        },
    ],
    zipfile = "lib/shared-downloader.zip",
    #data files required for the gui version due to EasyDialogs
    data_files = [
        os.path.join(os.path.dirname(sys.executable), 'Lib','site-packages','EasyDialogs','EasyDialogsRes.dll')
    ]
)
