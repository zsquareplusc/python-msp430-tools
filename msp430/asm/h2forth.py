#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2011 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""\
Conversion of C header files (specially for the MSP430) to Forth.

It's main purpose is to extract the #defines from the CPU specific
header files for the TI MSP430.
"""

import logging
import codecs
import msp430.asm.cpp


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():
    import sys
    import os
    import argparse
    logging.basicConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'HEADERFILE',
        nargs='?',
        default='-',
        help='name of the input file (default: %(default)s)')

    group = parser.add_argument_group('Input')

    group.add_argument(
        '-I', '--include-path',
        action='append',
        metavar="PATH",
        default=[],
        help='Add directory to the search path list for includes')

    group.add_argument(
        '-D', '--define',
        action='append',
        dest='defines',
        metavar='SYM[=VALUE]',
        default=[],
        help='define symbol')

    group = parser.add_argument_group('Output')

    group.add_argument(
        '-o', '--outfile',
        type=argparse.FileType('w'),
        default='-',
        help='name of the output file (default: %(default)s)',
        metavar="FILE")

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help='print status messages')

    parser.add_argument(
        '--develop',
        action='store_true',
        default=False,
        help='print debug messages')

    args = parser.parse_args()

    if args.develop:
        logging.getLogger('cpp').setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger('cpp').setLevel(logging.INFO)
    else:
        logging.getLogger('cpp').setLevel(logging.WARN)

    cpp = msp430.asm.cpp.Preprocessor()
    # extend include search path
    # built in places for msp430.asm
    d = os.path.join(os.path.dirname(sys.modules['msp430.asm'].__file__), 'include')
    cpp.include_path.append(d)
    cpp.include_path.append(os.path.join(d, 'upstream'))
    # user provided directories (-I)
    cpp.include_path.extend(args.include_path)
    # insert predefined symbols (XXX function like macros not yet supported)
    for definition in args.defines:
        if '=' in definition:
            symbol, value = definition.split('=', 1)
        else:
            symbol, value = definition, '1'
        cpp.namespace.defines[symbol] = value

    if not args.HEADERFILE or args.HEADERFILE == '-':
        infilename = '<stdin>'
        infile = argparse.FileType('r')('-')
    else:
        # search include path for files
        for path in cpp.include_path:
            infilename = os.path.join(path, args.HEADERFILE)
            if os.path.exists(infilename):
                infile = codecs.open(infilename, 'r', 'utf-8')
                break
        else:
            sys.stderr.write('h2forth: {}: File not found\n'.format(infilename))
            sys.exit(1)

    try:
        error_found = cpp.preprocess(infile, msp430.asm.cpp.Discard(), infilename)
        if error_found:
            sys.exit(1)
    except msp430.asm.cpp.PreprocessorError as e:
        sys.stderr.write('{e.filename}:{e.line}: {e}\n'.format(e=e))
        if args.develop:
            if hasattr(e, 'text'):
                sys.stderr.write('{e.filename}:{e.line}: input line: {e.text!r}\n'.format(e=e))
        sys.exit(1)

    args.outfile.write(': <UNDEFINED> 0 ;\n')
    #~ for definition in cpp.macros:
        #~ print definition
    for name, definition in sorted(cpp.namespace.defines.items()):
        #~ print name, definition
        # MSP430 specific hack to get peripherals:
        if name.endswith('_') and not name.startswith('_'):
            name = name[:-1]
        if definition:
            try:
                value = cpp.namespace.eval(definition)
            except msp430.asm.cpp.PreprocessorError as e:
                sys.stderr.write('cannot convert expression: {}\n'.format(e))
            except msp430.asm.rpn.RPNError as e:
                sys.stderr.write('cannot convert expression: {}\n'.format(e))
            else:
                args.outfile.write('{!r} CONSTANT {}\n'.format(value, name))
        else:
            args.outfile.write('1 CONSTANT {}\n'.format(name))


if __name__ == '__main__':
    main()
