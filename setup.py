# This is a setup script for pythons distutils. It will install the
# python-msp430-tools extension when run as: python setup.py install

# Author: Chris Liechti <cliechti@gmx.net>
#
# This is open source software under the BSD license. See LICENSE.txt for more
# details.


from distutils.core import setup
import sys

setup(
    name="python-msp430-tools",
    description="Python MSP430 Tools",
    version="0.5",
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="http://launchpad.net/python-msp430-tools/",
    packages=['msp430'],
    package_dir={'msp430': 'msp430'},
    package_data={'msp430': [
            'msp430/asm/definitions/msp430-mcu-list.txt',
            'msp430/bsl/BL_150S_14x.txt',
            'msp430/bsl/BL_150S_44x.txt',
            'msp430/bsl/BS_150S_14x.txt',
            'msp430/bsl/patch.txt',
            'msp430/bsl5/RAM_BSL.00.05.04.34.txt',
            ]},
    license="Simplified BSD License",
    long_description=open('README.txt').read(),
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
