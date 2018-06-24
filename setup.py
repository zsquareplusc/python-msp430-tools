#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
#
# This is a setup script for pythons distutils. It will install the
# python-msp430-tools extension when run as: python setup.py install
from setuptools import setup, find_packages
import sys
import glob

setup(
    name="python-msp430-tools",
    description="Python MSP430 Tools",
    version="0.9.2",
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="https://github.com/zsquareplusc/python-msp430-tools",
    packages=find_packages(),
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
            'msp430-bsl-legacy = msp430.legacy.bsl_main:main',
            'msp430-bsl-telosb = msp430.bsl.target.telosb:main',
            'msp430-compare = msp430.memory.compare:main',
            'msp430-convert = msp430.memory.convert:main',
            'msp430-downloader = msp430.downloader:main',
            #~ 'msp430-gdb = msp430.gdb.target:main',
            'msp430-generate = msp430.memory.generate:main',
            'msp430-hexdump = msp430.memory.hexdump:main',
            'msp430-jtag = msp430.jtag.target:main',
            'msp430-jtag-legacy = msp430.legacy.jtag:main',
            'msp430-ram-usage = msp430.ram_usage:main',
            'msp430-tool = msp430.tool:main',
        ],
    },
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
