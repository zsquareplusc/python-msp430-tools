# setup.py
#
# $Id: setup.py,v 1.5 2006/04/11 18:35:23 cliechti Exp $

from distutils.core import setup
import sys

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
if sys.version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

setup(
    name="python-mspgcc",
    description="MSP430 Python tools from the mspgcc toolchain",
    version="1.1",
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="http://mspgcc.sourceforge.net/",
    packages=['mspgcc', 'mspgcc.serial'],
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
