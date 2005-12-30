# setup.py
#
# $Id: setup.py,v 1.4 2005/12/30 03:47:49 cliechti Exp $

from distutils.core import setup
import sys

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
if sys.version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

setup(
    name="msp430-python-tools",
    description="MSP430 Python Tools",
    version="1.1",
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="http://mspgcc.sourceforge.net/",
    packages=['msp430', 'msp430.serial'],
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
