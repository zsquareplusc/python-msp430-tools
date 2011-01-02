# setup.py

from distutils.core import setup
import sys

setup(
    name="python-msp430-tools",
    description="Python MSP430 tools",
    version="0.5",
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="http://python-msp430-tools/",
    packages=['msp430'],
    license="Python",
    long_description="Python tools for the MSP430 processor including BSL, JTAG",
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
