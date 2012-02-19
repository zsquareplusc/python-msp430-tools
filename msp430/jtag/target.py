#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2002-2012 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""
JTAG programmer for the MSP430 embedded processor.

Requires Python 2+ and the binary extension _parjtag or ctypes
and MSP430mspgcc.dll/libMSP430mspgcc.so or MSP430.dll/libMSP430.so
and HIL.dll/libHIL.so
"""

import sys
import os
import logging
import time
from msp430.jtag import jtag

from optparse import OptionGroup
import msp430.target

VERSION = "3.0"


class JTAGTarget(object):

    def __init__(self):
        self.jtagobj = jtag.JTAG()
        self.release_done = False

    def memory_read(self, address, length):
        """Read from memory."""
        return bytes(self.jtagobj.uploadData(address, length))

    def memory_write(self, address, data):
        """Write to memory."""
        return self.jtagobj.downloadData(address, data)

    def mass_erase(self):
        """Clear all Flash memory."""
        self.jtagobj.actionMassErase()

    def main_erase(self):
        """Clear main Flash memory (excl. infomem)."""
        self.jtagobj.actionMainErase()

    def erase(self, address):
        """Erase Flash segment containing the given address."""
        self.jtagobj.makeActionSegmentErase(address)()

    def execute(self, address):
        """Start executing code on the target."""
        self.jtagobj.actionRun(address) # load PC and execute

    def version(self):
        """The 16 bytes of the ROM that contain chip and BSL info are returned."""
        return bytes(self.jtagobj.uploadData(0x0ff0, 16))

    def reset(self):
        """Reset the device."""
        if not self.release_done:
            self.release_done = True
            try:
                self.jtagobj.reset(1, 1)
            except IOError, e: # XXX currently getting EEM errors on launchpad
                pass

    def close(self):
        if not self.release_done:
            self.release_done = True
            self.jtagobj.reset(1, 1)             # reset and release target
        self.jtagobj.close()                     # release communication port



class JTAG(JTAGTarget, msp430.target.Target):
    """Combine the JTAG backend and the common target code."""

    def __init__(self):
        JTAGTarget.__init__(self)
        msp430.target.Target.__init__(self)
        self.logger = logging.getLogger('JTAG')

        # some variables used in help texts
        self.text_variables = {
            'prog': sys.argv[0],
            'version': VERSION,
            'msp430': (sys.platform != 'win32') and 'libMSP430.so' or 'MSP430.dll',
            'msp430mspgcc': (sys.platform != 'win32') and 'libMSP430mspgcc.so' or 'MSP430mspgcc.dll',
        }

    def help_on_backends(self):
        """Show extended help text on backends"""
        sys.stderr.write("""\
%(prog)s can use different libraries to connect to the target.
The backend can be chosen with the --backend command line option.

"mspgcc"
Using %(msp430mspgcc)s, the open source implementation
from the mspgcc project.

"ti" (default)
Using %(msp430)s, the proprietary library from TI or a
compatible one from a 3rd party supplier.

"parjtag"
Old way of using %(msp430mspgcc)s. Use "mspgcc" instead.

Software support for interfaces:
+============================+==========+==========+==========+
| device JTAG                |  mspgcc  |         ti          |
| capabilities               |   FET    |   FET    | USB-FET  |
+============================+==========+==========+==========+
| standard    / 4 wire       |   yes    |   yes    |   yes    |
+----------------------------+----------+----------+----------+
| spy-bi-wire / 4 wire (1)   |  yes(2)  |   no     |  yes(3)  |
+----------------------------+----------+----------+----------+
| spy-bi-wire / 2 wire       |   no     |   no     |  yes(4)  |
+============================+==========+==========+==========+

Notes:
(1) 4 wire JTAG on devices with spy-bi-wire capability needs special
    timing.
(2) Timing critical, may not work on all machines or at every try.
(3) Using --spy-bi-wire-jtag option.
(4) Using --spy-bi-wire option.

Features of backends:
+=======================================+==========+==========+
| Feature                               |  mspgcc  |   ti     |
+=======================================+==========+==========+
| Support for USB JTAG adapters         |   no     |   yes    |
+---------------------------------------+----------+----------+
| Using --funclet option                |   yes    |   no     |
+=======================================+==========+==========+

""" % self.text_variables)

    def add_extra_options(self):
        self.parser.add_option("--help-backend",
                dest="help_backend",
                help="show help about the different backends",
                default=False,
                action='store_true')

        self.parser.add_option("-l", "--library-path",
                dest="library_path",
                help="search for %(msp430)s or %(msp430mspgcc)s in this place first" % self.text_variables,
                default=None)

        self.parser.add_option("--fet-update",
                dest="do_fet_update",
                help="with TI's MSP430 library, initiate download of firmware to MSP430UIF box",
                default=False,
                action='store_true')

        group = OptionGroup(self.parser, "Connection", """\
NOTE: On Windows, use "USB", "TIUSB" or "COM5" etc if using MSP430.dll from TI.
On other platforms, e.g. Linux, use "/dev/ttyUSB0" etc. if using
libMSP430.so.
If a %(msp430)s is found, it is preferred, otherwise
%(msp430mspgcc)s is used.

NOTE: --slowdown > 50 can result in failures for the RAM size auto detection
(use --ramsize option to fix this). Use the --verbose option and watch
the outputs. The DCO clock adjustment and thus the Flash timing may be
inaccurate for large values.
    """ % self.text_variables)

        group.add_option("--backend",
                dest="backend",
                help="select an alternate backend. See --help-backend for more information",
                default=None)

        group.add_option("-p", "--port",
                dest="port_name",
                metavar="PORT",
                help='specify an other parallel port or serial port for the USBFET (the later requires %(msp430)s instead of %(msp430mspgcc)s).  (defaults to "LPT1" ("/dev/parport0" on Linux))' % self.text_variables,
                default=None)

        group.add_option("--spy-bi-wire-jtag",
                dest="spy_bi_wire_jtag",
                help="interface is 4 wire on a spy-bi-wire capable device",
                default=False,
                action='store_true')

        group.add_option("--spy-bi-wire",
                dest="spy_bi_wire",
                help="interface is 2 wire on a spy-bi-wire capable device",
                default=False,
                action='store_true')

        group.add_option("--slowdown",
                dest="slowdown",
                metavar="MICROSECONDS",
                help="artificially slow down the communication. Can help with long lines, try values between 1 and 50 (parallel port interface with mspgcc's HIL library only). (experts only)",
                default=None)

        group.add_option("-R", "--ramsize",
                dest="ramsize",
                type="int",
                help="specify the amount of RAM to be used to program flash (default: auto detected)",
                default=None,
                metavar="BYTES")

        self.parser.add_option_group(group)

        group = OptionGroup(self.parser, "JTAG fuse", """\
WARNING: This is not reversible, use with care!  Note: Not supported with the
simple parallel port adapter (7V source required).",
""")

        group.add_option("--secure",
                dest="do_secure",
                help="blow JTAG security fuse",
                default=False,
                action='store_true')

        self.parser.add_option_group(group)

        group = OptionGroup(self.parser, "Examples", """\
Mass erase and program from file: "%(prog)s -e firmware.elf"
Dump information memory: "%(prog)s --upload=0x1000-0x10ff"
""" % self.text_variables)
        self.parser.add_option_group(group)


    def parse_extra_options(self):
        """Process the extra options we added above"""
        if self.options.help_backend:
            self.help_on_backends()
            sys.exit()

        if self.options.backend is not None:
            if self.options.backend == 'mspgcc':
                backend = jtag.CTYPES_MSPGCC
            elif self.options.backend == 'parjtag':
                backend = jtag.PARJTAG
            elif self.options.backend == 'ti':
                backend = jtag.CTYPES_TI
            else:
                raise parser.error("no such backend: %r" % self.options.backend)
            jtag.init_backend(backend, verbose=self.options.verbose)
        else:
            jtag.init_backend(verbose=self.options.verbose)

        if self.options.do_fet_update:
            if jtag.backend == jtag.CTYPES_TI:
                sys.stderr.write("NOTICE: Please wait while updating - do not interrupt!\n")
                if jtag.MSP430_FET_FwUpdate(None, None, 0) == 0:
                    sys.stderr.write("--fet-upgarde done successfuly - terminating\n")
                    sys.exit(0)
                else:
                    sys.stderr.write("ERROR: --fet-upgarde failed\n")
                    sys.exit(1)
            else:
                self.parser.error('--fet-update only supported with TI backend')

        if self.options.spy_bi_wire:
            jtag.interface = 'spy-bi-wire'
        if self.options.spy_bi_wire_jtag:
            jtag.interface = 'spy-bi-wire-jtag'

        if self.options.do_secure:
            self.add_action(self.jtagobj.actionSecure)

        self.jtagobj.verbose = self.verbose
        internal_level = max(self.verbose - 2, 0)
        try:
            self.jtagobj.setDebugLevel(internal_level)
        except IOError:
            sys.stderr.write("WARNING: Failed to set debug level in backend library\n")
        #~ memory.DEBUG = internal_level

        if self.options.progress:
            self.jtagobj.showprogess = 1

        if self.verbose:
            sys.stderr.write("MSP430 JTAG programmer Version: %s\n" % VERSION)

        self.jtagobj.data = self.download_data      # prepare downloaded data


    def close_connection(self):
        """Close connection to target"""
        self.close()


    def open_connection(self):
        """Connect to target"""
        self.jtagobj.open(self.options.port_name)   # try to open port
        if self.options.ramsize is not None:
            self.jtagobj.setRamsize(self.options.ramsize)
        self.jtagobj.connect()                  # connect to target

        if self.options.slowdown is not None:
            import ctypes
            if sys.platform == 'win32':
                HIL_SetSlowdown = ctypes.windll.HIL.HIL_SetSlowdown
            else:
                # XXX and posix platforms?!
                libHIL, backend_info = jtag.locate_library('libHIL.so', jtag.search_path, ctypes.cdll)
                HIL_SetSlowdown = libHIL.HIL_SetSlowdown
            HIL_SetSlowdown.argtypes  = [ctypes.c_ulong]
            #~ HIL_SetSlowdown.restype   = ctypes.c_int # actually void
            # set slowdown
            HIL_SetSlowdown(int(self.options.slowdown))



def main():
    # special preprocessing of command line arguments.
    # because setting the LD_LIBRARY_PATH only works correctly for new
    # processes, as the loader for the current one does not re-check the
    # variable. therefore we have to restart ourselves. do this now before any
    # other actions have been done, such as writing to stdout/stderr.
    library_path = None
    for x in sys.argv:
        if x.startswith('-l=') or x.startswith('--library-path='):
            _, library_path = x.split('=', 1)
            sys.argv.remove(x)
            break
        if x == '-l' or x == '--library-path':
            index = sys.argv.index(x)
            library_path = sys.argv.pop(index+1)
            sys.argv.remove(x)
            break
    if library_path is not None:
        #~ print sys.argv
        if sys.platform == 'win32':
            os.environ['PATH'] = '%s;%s' % (library_path, os.environ.get('PATH', ''))
            os.environ['LIBMSPGCC_PATH'] = library_path
        else:
            os.environ['LD_LIBRARY_PATH'] = library_path
            os.environ['LIBMSPGCC_PATH'] = library_path
        # start a new process
        if hasattr(sys, "frozen"):      # py2exe
            sys.exit(os.spawnve(os.P_WAIT, sys.executable, [sys.executable] + sys.argv[1:], os.environ))
        else:
            # XXX this does only work if module is in pythons search path..
            os.execve(sys.executable, [sys.executable, '-m', 'msp430.jtag.target'] + sys.argv[1:], os.environ)
            #~ os.execve(sys.executable, [sys.executable, __file__] + sys.argv, os.environ)
        return

    # run the main application
    jtag_target = JTAG()
    jtag_target.main()

if __name__ == '__main__':
    main()
