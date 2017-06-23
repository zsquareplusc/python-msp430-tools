# This is a setup script for pythons distutils. It will install the
# python-msp430-tools extension when run as: python setup.py install

# Author: Chris Liechti <cliechti@gmx.net>
#
# This is open source software under the BSD license. See LICENSE.txt for more
# details.


from distutils.core import setup
import sys
import glob

setup(
    name="python-msp430-tools",
    description="Python MSP430 Tools",
    version="0.7",
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="https://github.com/zsquareplusc/python-msp430-tools",
    packages=[
        'msp430',
        'msp430.asm',
        'msp430.bsl',
        'msp430.bsl.target',
        'msp430.bsl5',
        'msp430.gdb',
        'msp430.jtag',
        'msp430.legacy',
        'msp430.listing',
        'msp430.memory',
        'msp430.shell',
    ],
    package_dir={'msp430': 'msp430'},
    package_data={'msp430': [
        'asm/definitions/msp430-mcu-list.txt',
        'bsl/BL_150S_14x.txt',
        'bsl/BL_150S_44x.txt',
        'bsl/BS_150S_14x.txt',
        'bsl/patch.txt',
        'bsl5/RAM_BSL.00.06.05.34.txt',
    ]},
    entry_points={
        'console_scripts': [
            'msp430-bsl = msp430.bsl.target:main',
            'msp430-bsl-fcdprog = msp430.bsl.target.fcdprog:main',
            #~ 'msp430-bsl-legacy = scripts/msp430-bsl-legacy.py',
            'msp430-bsl-telosb = msp430.bsl.target.telosb.main',
            'msp430-compare = msp430.memory.compare:main',
            'msp430-convert = msp430.memory.convert:main',
            #~ 'msp430-downloader = scripts/msp430-downloader.py',
            #~ 'msp430-gdb = msp430.gdb.target:main',
            'msp430-generate = msp430.memory.generate:main',
            'msp430-hexdump = msp430.memory.hexdump:main',
            'msp430-jtag = msp430.jtag.target:main',
            #~ 'msp430-jtag-legacy = scripts/msp430-jtag-legacy.py',
            #~ 'msp430-ram-usage = scripts/msp430-ram-usage.py',
            #~ 'msp430-tool = scripts/msp430-tool.py',
        ],
    },
    scripts=[
        'scripts/msp430-bsl-legacy',
        'scripts/msp430-downloader',
        'scripts/msp430-jtag-legacy',
        'scripts/msp430-ram-usage',
        'scripts/msp430-tool',
    ],
    license="Simplified BSD License",
    long_description=open('README.rst').read(),
    classifiers = [
#        'Development Status :: 5 - Production/Stable',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Assemblers',
        'Topic :: Software Development :: Libraries',
    ],
)
