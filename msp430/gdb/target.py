#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Remote GDB programmer for the MSP430 embedded processor.
"""

import sys
import logging
from msp430.gdb import gdb

from optparse import OptionGroup
import msp430.target

VERSION = "1.0"


class GDBTarget(object):

    def __init__(self):
        self.gdb = None

    def memory_read(self, address, length):
        """Read from memory."""
        return bytearray(self.gdb.read_memory(address, length))

    def memory_write(self, address, data):
        """Write to memory."""
        return self.gdb.write_memory(address, data)

    def mass_erase(self):
        """Clear all Flash memory."""
        self.gdb.monitor('erase all')

    def main_erase(self):
        """Clear main Flash memory (excl. infomem)."""
        self.gdb.monitor('erase')

    def erase(self, address):
        """Erase Flash segment containing the given address."""
        self.gdb.monitor('erase segment 0x%x' % address)

    def execute(self, address):
        """Start executing code on the target."""
        self.gdb.cont(address) # load PC and execute

    def version(self):
        """The 16 bytes of the ROM that contain chip and BSL info are returned."""
        return self.gdb.read_memory(0x0ff0, 16)

    def reset(self):
        """Reset the device."""
        self.gdb.monitor('reset')

    def open(self, host_port):
        self.close()
        self.gdb = gdb.GDBClient(host_port)

    def close(self):
        if self.gdb is not None:
            self.gdb.close()                     # release communication port
            self.gdb = None



class GDB(GDBTarget, msp430.target.Target):
    """Combine the GDB backend and the common target code."""

    def __init__(self):
        GDBTarget.__init__(self)
        msp430.target.Target.__init__(self)
        self.logger = logging.getLogger('GDB')


    def add_extra_options(self):
        group = OptionGroup(self.parser, "Connection")

        group.add_option("-c", "--connect",
                dest="host_port",
                help="TCP/IP host name or ip and port of GDB server (default: %default)",
                action='store',
                default='localhost:2000',
                metavar='HOST:PORT')

        self.parser.add_option_group(group)


    def parse_extra_options(self):
        host, port = self.options.host_port.split(':')
        self.host_port = (host, int(port))
        if self.verbose:
            sys.stderr.write("MSP430 remote GDB programmer Version: %s\n" % VERSION)


    def close_connection(self):
        self.close()


    def open_connection(self):
        self.open(self.host_port)


def main():
    # run the main application
    gdb_target = GDB()
    gdb_target.main()

if __name__ == '__main__':
    main()
