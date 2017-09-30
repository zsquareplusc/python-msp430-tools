#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2011-2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
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
    import argparse

    parser = argparse.ArgumentParser(
        epilog='example: %(prog)s test.txt --execute "echo --"')

    parser.add_argument(
        "FILENAME",
        nargs="+")

    parser.add_argument(
        "-x", "--execute",
        metavar="COMMAND",
        help="run this command when watched file(s) changed, -- is replaced by first FILENAME")

    args = parser.parse_args()

    if args.execute:
        cmd = args.execute.replace('--', args.FILENAME[0])
        sys.stderr.write("watch: command line will be: {!r}\n".format(cmd))
    else:
        cmd = None

    def execute():
        sys.stderr.write('watch: file(s) changed {}\n'.format(datetime.datetime.now()))
        if cmd is not None:
            #~ sys.stderr.write("watch: execute: %r\n" % cmd)
            subprocess.call(cmd, shell=True)

    try:
        watch(args.FILENAME, callback=execute)
    except KeyboardInterrupt:
        sys.stdout.write('\n')

if __name__ == '__main__':
    main()
