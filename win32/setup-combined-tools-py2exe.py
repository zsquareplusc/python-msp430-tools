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
    url="http://launchpad.net/python-msp430-tools/",
    
    version = '0.3',
    options = { "py2exe":
        {
            'dist_dir': 'bin',
            'excludes': ['javax.comm', 'macpath', 'TERMIOS', 'FCNTL',
                    'os2emxpath', '_parjtag',
                    'IronPythonConsole', 'System', 'System.IO.Ports', 'System.Windows.Forms.Clipboard', 'clr',
                    'modes.editingmodes', 'startup', 'Carbon', 'Carbon.Files'],
            'packages': ['msp430', 'msp430.asm', 'msp430.memory', 'msp430.shell',
                        'msp430.gdb', 'msp430.jtag', 'msp430.bsl', 'msp430.bsl5'],
            'includes': ['pywinusb', 'EasyDialogs'],
            'dll_excludes': ['HIL.dll', 'MSP430mspgcc.dll'],
            'optimize': 2,
        }
    },
    console = [
        "scripts/msp430-bsl.py",
        "scripts/msp430-jtag.py",
        "scripts/msp430-tool.py",
    ],
    windows = [
        {
            'script': "scripts/msp430-downloader.py",
            'icon_resources': [(0x0001, 'win32/downloader.ico')]
        },
    ],
    zipfile = "lib/shared.zip",
)
