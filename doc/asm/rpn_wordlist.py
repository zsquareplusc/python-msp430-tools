#! /usr/bin/env python
"""\
Create documentation of msp430.asm.rpn based classes.
"""

import sys
import inspect
import codecs

def create_wordlist(obj, output, title):
    wordlist = {}

    for word, func in obj.builtins.items():
        info = wordlist.setdefault(word.upper(), {'doc':'', 'deftype':set()})
        info['deftype'].add('python')
        #~ info['stack'] = m.group('balance') or 'n/a'
        #~ info.setdefault('locations', []).append(obj.__class__.__name__)
        if func.__doc__ is not None:
            if info['doc']:
                print "WARNING: multiple definitions of %r, skipping docs in forth.py" % (word,)
            else:
                info['doc'] = u'%s\n' % inspect.getdoc(func)
                # XXX cut prefixing whitespace

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # write output in reST format
    if title:
        output.write('%s\n' % ('=' * (2+len(title))))
        output.write('%s\n' % title)
        output.write('%s\n' % ('=' * (2+len(title))))

    for word, info in sorted(wordlist.items()):
        output.write('\n``%s``\n' % word)
        output.write('%s\n' % ('-'*(4+len(word))))
        output.write('%s\n' % info['doc'])
        if 'stack' in info: output.write('\nStack: ``%s``\n' % info['stack'])
        #~ available = []
        #~ if set([':', 'CODE']) & info['deftype']: # runs_on_target
            #~ available.append('target')
        #~ if set([':', 'python']) & info['deftype']: # runs_on_host
            #~ available.append('host')
        #~ output.write('\nAvailability: %s\n' % ' and '.join(available))
        if 'locations' in info:
            output.write('\nDefined in file(s): %s\n' % ' and '.join('``%s``' % f for f in info['locations']))
    print "%d words" % len(wordlist)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main():
    import sys
    import os
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-t", "--title",
                      dest = "title",
                      help = "document title")
    parser.add_option("-o", "--outfile",
                      dest = "outfile",
                      help = "name of the object file",
                      metavar = "FILE")
    parser.add_option("-v", "--verbose",
                      action = "store_true",
                      dest = "verbose",
                      default = False)

    (options, args) = parser.parse_args()

    #~ if len(args) > 1:
        #~ sys.stderr.write("Only one module name at a time.\n")
        #~ sys.exit(1)

    if options.outfile:
        outfile = codecs.open(options.outfile, 'w', 'utf-8')
    else:
        outfile = codecs.getwriter("utf-8")(sys.stdout)

    sys.path.append('../..')
    mod = __import__(args[0])
    cls = getattr(sys.modules[args[0]], args[1])
    obj = cls()
    create_wordlist(obj, outfile, options.title)

if __name__ == '__main__':
    main()

