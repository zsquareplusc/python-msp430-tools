#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
This tool repeatedly checks the size and modification time of a file. When a
change is detected it can run the specified command.

Example of usage: automatically download to MCU a file when it has changed (due
to a new, successful compilation run).
"""

import os
import stat
import sys
import time
import datetime
import subprocess


def get_file_stats(filename):
    """get the size and modification time of a file"""
    if os.path.exists(filename):
        stats = os.stat(filename)
        return stats[stat.ST_SIZE], stats[stat.ST_MTIME]
    else:
        return (0, 0)


def watch(filenames, callback):
    """repeatedly check the given files and run the callback when one has changed"""

    last_stats = [get_file_stats(filename) for filename in filenames]
    while True:
        stats = [get_file_stats(filename) for filename in filenames]
        if stats != last_stats:
            last_stats = stats
            callback()
        time.sleep(2)


def main():
    from optparse import OptionParser

    parser = OptionParser(usage='%prog FILENAME [FILENAME...] --execute "some_program --"')

    parser.add_option("-x", "--execute",
            action = "store",
            dest = "execute",
            default = None,
            metavar = "COMMAND",
            help = "run this command when watched file(s) changed, -- is replaced by first FILENAME")

    (options, args) = parser.parse_args()

    if not args:
        parser.error('at least one filename is required')

    if options.execute:
        cmd = options.execute.replace('--', args[0])
        sys.stderr.write("watch: command line will be: %r\n" % cmd)
    else:
        cmd = None

    def execute():
        sys.stderr.write("watch: file(s) changed %s\n" % datetime.datetime.now())
        if cmd is not None:
            #~ sys.stderr.write("watch: execute: %r\n" % cmd)
            subprocess.call(cmd, shell=True)

    watch(args, callback=execute)

if __name__ == '__main__':
    main()