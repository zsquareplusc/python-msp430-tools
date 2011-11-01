#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

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
    from optparse import OptionParser
    logging.basicConfig()

    parser = OptionParser()
    parser.add_option("-o", "--outfile",
                      dest = "outfile",
                      help = "name of the object file",
                      metavar = "FILE")
    parser.add_option("-v", "--verbose",
                      action = "store_true",
                      dest = "verbose",
                      default = False,
                      help="print status messages")
    parser.add_option("--debug",
                      action = "store_true",
                      dest = "debug",
                      default = False,
                      help = "print debug messages to stdout")
    parser.add_option("-D", "--define",
                      action = "append",
                      dest = "defines",
                      metavar = "SYM[=VALUE]",
                      default = [],
                      help="define symbol")
    parser.add_option("-I", "--include-path",
                      action = "append",
                      dest = "include_paths",
                      metavar = "PATH",
                      default = [],
                      help="Add directory to the search path list for includes")

    (options, args) = parser.parse_args()

    if len(args) > 1:
        sys.stderr.write("Only one file at a time allowed.\n")
        sys.exit(1)

    if options.debug:
        logging.getLogger('cpp').setLevel(logging.DEBUG)
    elif options.verbose:
        logging.getLogger('cpp').setLevel(logging.INFO)
    else:
        logging.getLogger('cpp').setLevel(logging.WARN)


    if options.outfile:
        outfile = codecs.open(options.outfile, 'w', 'utf-8')
    else:
        outfile = codecs.getwriter("utf-8")(sys.stdout)


    cpp = msp430.asm.cpp.Preprocessor()
    # extend include search path
    # built in places for msp430.asm
    d = os.path.join(os.path.dirname(sys.modules['msp430.asm'].__file__), 'include')
    cpp.include_path.append(d)
    cpp.include_path.append(os.path.join(d, 'upstream'))
    # user provided directories (-I)
    cpp.include_path.extend(options.include_paths)
    # insert predefined symbols (XXX function like macros not yet supported)
    for definition in options.defines:
        if '=' in definition:
            symbol, value = definition.split('=', 1)
        else:
            symbol, value = definition, '1'
        cpp.namespace.defines[symbol] = value

    if not args or args[0] == '-':
        infilename = '<stdin>'
        infile = codecs.getreader("utf-8")(sys.stdin)
    else:
        # search include path for files
        for path in cpp.include_path:
            infilename = os.path.join(path, args[0])
            if os.path.exists(infilename):
                infile = codecs.open(infilename, 'r', 'utf-8')
                break
        else:
            sys.stderr.write('h2forth: %s: File not found\n' % (infilename,))
            sys.exit(1)

    try:
        error_found = cpp.preprocess(infile, msp430.asm.cpp.Discard(), infilename)
        if error_found:
            sys.exit(1)
    except msp430.asm.cpp.PreprocessorError, e:
        sys.stderr.write('%s:%s: %s\n' % (e.filename, e.line, e))
        if options.debug:
            if hasattr(e, 'text'):
                sys.stderr.write('%s:%s: input line: %r\n' % (e.filename, e.line, e.text))
        sys.exit(1)


    outfile.write(': <UNDEFINED> 0 ;\n')
    #~ for definition in cpp.macros:
        #~ print definition
    for name, definition in sorted(cpp.namespace.defines.items()):
        #~ print name, definition
        # MSP430 specific hack to get peripherals:
        if name.endswith('_') and not name.startswith('_'):
            name = name[:-1]
        if definition:
            value = cpp.namespace.eval(definition)
            outfile.write('%r CONSTANT %s\n' % (value, name))
        else:
            outfile.write('1 CONSTANT %s\n' % (name,))

if __name__ == '__main__':
    main()

