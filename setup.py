# setup.py
#
# $Id: setup.py,v 1.1 2004/02/29 23:06:36 cliechti Exp $

from distutils.core import setup
import sys

setup(
    name="msp430-python-tools",
    description="MSP430 Python Tools",
    version="1.0",
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="http://mspgcc.sourceforge.net/",
    packages=['msp430', 'msp430.serial'],
    license="Python",
    long_description="Python Tools for the MSP430 processor includeing BSL, JTAG",
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Python Software Foundation License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
)
