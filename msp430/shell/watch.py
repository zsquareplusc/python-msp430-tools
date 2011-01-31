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

def watch(filename, callback):
    """repeatedly check the file and run the callback when it has changed"""
    last_stat = get_file_stats(filename)
    while True:
        stats = get_file_stats(filename)
        if stats != last_stat:
            last_stat = stats
            callback(*stats)
        time.sleep(2)


if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser(usage='%prog FILENAME --execute "some/program/ --"')

    parser.add_option("-x", "--execute",
            action = "store",
            dest = "execute",
            default = None,
            metavar = "COMMAND",
            help = "run this command when watched file changed, -- is replaced by FILENAME")

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("expected exactly one filename")

    if options.execute:
        cmd = options.execute.replace('--', args[0])
        sys.stderr.write("watch: command lie will be: %r\n" % cmd)
    else:
        cmd = None
    def execute(size, date):
        if date:    # only download if file exits
            sys.stderr.write("watch: file changed %s\n" % datetime.datetime.now())
            if cmd is not None:
                #~ sys.stderr.write("watch: execute: %r\n" % cmd)
                subprocess.call(cmd, shell=True)
        else:
            sys.stderr.write("watch: file disappeared\n")

    watch(args[0], callback=execute)
