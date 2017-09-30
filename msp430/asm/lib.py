#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2011 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""\
Librarian - Access source code library based on templates.

It more or less just a copy program, that copies files from a library of
snippets to the given output. It can textually replace words, so that
the output can be adjusted, e.g. when a template contains variables.
"""

import logging
import codecs
import pkgutil

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def main():
    import sys
    import os
    import argparse
    logging.basicConfig()

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('TEMLATE_NAME', nargs='?')
    group.add_argument(
        '-l', '--list',
        action='store_true',
        default=False,
        help='List available snippets')

    parser.add_argument(
        '-o', '--outfile',
        type=argparse.FileType('w'),
        default='-',
        help='name of the object file (default: %(default)s)',
        metavar="FILE")
    parser.add_argument(
        '-D', '--define',
        action='append',
        dest='defines',
        metavar='SYM[=VALUE]',
        default=[],
        help='define symbol')
    parser.add_argument(
        '--develop',
        action='store_true',
        default=False,
        help='print debug messages to stdout')

    args = parser.parse_args()

    if args.list:
        args.outfile.write('List of available snippets:\n')
        # XXX this method won't work when package is zipped (e.g. py2exe)
        d = os.path.join(os.path.dirname(sys.modules['msp430.asm'].__file__), 'librarian')
        for root, dirs, files in os.walk(d):
            for filename in files:
                args.outfile.write('    {}\n'.format(os.path.join(root, filename)[1 + len(d):]))
        sys.exit(0)

    # load desired snippet
    try:
        template = pkgutil.get_data('msp430.asm', 'librarian/{}'.format(args.TEMLATE_NAME)).decode('utf-8')
    except IOError:
        sys.stderr.write('lib: {}: File not found\n'.format(args.TEMLATE_NAME))
        if args.develop:
            raise
        sys.exit(1)

    # collect predefined symbols
    defines = {}
    for definition in args.defines:
        if '=' in definition:
            symbol, value = definition.split('=', 1)
        else:
            symbol, value = definition, ''
        defines[symbol] = value

    # perform text replacements
    for key, value in defines.items():
        template = template.replace(key, value)

    # write final result
    args.outfile.write(template)


if __name__ == '__main__':
    main()
