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
    description="Python MSP430 tools",
    version="0.1",
    author="Chris Liechti",
    author_email="cliechti@gmx.net",
    url="http://launchpad.net/python-msp430-tools/",
    packages=['msp430'],
    license="Python",
    long_description=open('README.txt').read(),
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
)
