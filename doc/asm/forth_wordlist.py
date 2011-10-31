#! /usr/bin/env python
"""\
Create documentation of Forth system by extracting a word list 
from '.forth' files and writing a '.rst' file
"""

import sys
import re
import glob
import inspect

re_word = re.compile(r'^(?P<type>CODE|:)\s+(?P<name>\S+)\s+(?P<balance>\(.*?--.*?\))?')
re_doc_comment = re.compile(r'^\( > ?(.*?)\)?$')

wordlist = {}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# scan the forth source files. this will yield words for host and target
for filename in glob.glob('../../msp430/asm/forth/*.forth'):
    print "scanning", filename
    last_comment = []
    for n, line in enumerate(open(filename)):
        m = re_doc_comment.match(line)
        if m:
            last_comment.append(m.group(1))

        m = re_word.match(line)
        if m:
            #~ print m.groups()
            info = wordlist.setdefault(m.group('name').upper(), {'doc':'', 'deftype':set()})
            info['deftype'].add(m.group('type'))
            if m.group('balance'):
                info['stack'] = m.group('balance')
            info.setdefault('locations', []).append(u'%s:%s' % (filename[23:], n+1))
            if last_comment and info['doc']:
                print "WARNING: multiple definitions of %r, skipping docs in %s" % (m.group('name'), filename)
            else:
                info['doc'] = u'\n'.join(last_comment)
            last_comment = []

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# also include all builtin words on the host.
sys.path.append('../..')
import msp430.asm.forth
f = msp430.asm.forth.Forth()
for word, func in f.builtins.items():
    info = wordlist.setdefault(word.upper(), {'doc':'', 'deftype':set()})
    info['deftype'].add('python')
    #~ info['stack'] = m.group('balance') or 'n/a'
    info.setdefault('locations', []).append(u'forth.py')
    if func.__doc__ is not None:
        if info['doc']:
            print "WARNING: multiple definitions of %r, skipping docs in forth.py" % (word,)
        else:
            info['doc'] = u'%s\n' % inspect.getdoc(func)
            # XXX cut prefixing whitespace

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# write output in reST format
output = open('forth_words.rst', 'w')
output.write("""\
=================
 Forth Word List
=================
.. .. contents::
""")
for word, info in sorted(wordlist.items()):
    output.write('\n``%s``\n' % word)
    output.write('%s\n' % ('-'*(4+len(word))))
    output.write('%s\n' % info['doc'])
    if 'stack' in info: output.write('\nStack: ``%s``\n' % info['stack'])
    available = []
    if set([':', 'CODE']) & info['deftype']: # runs_on_target
        available.append('target')
    if set([':', 'python']) & info['deftype']: # runs_on_host
        available.append('host')
    output.write('\nAvailability: %s\n' % ' and '.join(available))
    output.write('\nDefined in file(s): %s\n' % ' and '.join('``%s``' % f for f in info['locations']))
print "%d words" % len(wordlist)
