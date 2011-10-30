#! /usr/bin/env python
"""\
Create documentation of Forth system by extracting a word list 
from '.forth' files and writing a '.rst' file
"""

import sys
import re

re_word = re.compile(r'^(?P<type>CODE|:)\s+(?P<name>\S+)\s+(?P<balance>\(.*?--.*?\))?')
re_doc_comment = re.compile(r'^\( > ?(.*?)\)?$')

wordlist = {}
for filename in sys.argv[1:]:
    print "scanning", filename
    last_comment = []
    for n, line in enumerate(open(filename)):
        m = re_doc_comment.match(line)
        if m:
            last_comment.append(m.group(1))

        m = re_word.match(line)
        if m:
            #~ print m.groups()
            info = wordlist.setdefault(m.group('name'), {'doc':''})
            info['deftype'] = m.group('type')
            info['stack'] = m.group('balance') or 'n/a'
            info.setdefault('locations', []).append(u'%s:%s' % (filename, n+1))
            if last_comment and info['doc']:
                print "WARNING: multiple definitions of %r, skipping docs in %s" % (m.group('name'), filename)
            else:
                info['doc'] = u'\n'.join(last_comment)
            last_comment = []

output = open('forth_words.rst', 'w')
output.write("""\
=================
 Forth Word List
=================
.. contents::
""")
for word, info in sorted(wordlist.items()):
    output.write('\n``%s``\n' % word)
    output.write('%s\n' % ('-'*(4+len(word))))
    output.write('%s\n' % info['doc'])
    output.write('\n- stack: ``%s``\n' % info['stack'])
    output.write('- defined in file(s): %s\n' % ' and '.join('``%s``' % f for f in info['locations']))
    #~ if deftype == 'CODE':
        #~ output.write('- target only\n')
