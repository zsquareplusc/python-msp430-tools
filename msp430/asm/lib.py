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
    from optparse import OptionParser
    logging.basicConfig()

    parser = OptionParser(usage='%prog [options] temlate-name')
    parser.add_option("-o", "--outfile",
                      dest = "outfile",
                      help = "name of the object file",
                      metavar = "FILE")
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
    parser.add_option("-l", "--list",
                      action = "store_true",
                      dest = "list",
                      default = False,
                      help="List available snippets")

    (options, args) = parser.parse_args()

    if options.outfile:
        outfile = codecs.open(options.outfile, 'w', 'utf-8')
    else:
        outfile = codecs.getwriter("utf-8")(sys.stdout)

    if options.list:
        outfile.write('List of available snippets:\n')
        # XXX this method wont work when package is zipped (e.g. py2exe)
        d = os.path.join(os.path.dirname(sys.modules['msp430.asm'].__file__), 'librarian')
        for root, dirs, files in os.walk(d):
            for filename in files:
                outfile.write('    %s\n' % (os.path.join(root, filename)[1+len(d):],))
        sys.exit(0)

    if len(args) != 1:
        parser.error("Expected name of template as argument.")

    # load desired snippet
    try:
        template = pkgutil.get_data('msp430.asm', 'librarian/%s' % args[0])
    except IOError:
        sys.stderr.write('lib: %s: File not found\n' % (args[0]),)
        if options.debug:
            raise
        sys.exit(1)

    # collect predefined symbols
    defines = {}
    for definition in options.defines:
        if '=' in definition:
            symbol, value = definition.split('=', 1)
        else:
            symbol, value = definition, ''
        defines[symbol] = value

    # perform text replacements
    for key, value in defines.items():
        template = template.replace(key, value)

    # write final result
    outfile.write(template)


if __name__ == '__main__':
    main()

