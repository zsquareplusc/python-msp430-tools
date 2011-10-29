#! /usr/bin/env python
"""\
Create documentation of Forth system by extracting a word list 
from '.forth' files and writing a '.rst' file
"""

import sys
import re

re_word = re.compile(r'^(CODE|:)\s+(?P<name>\S+)\s+(?P<balance>\(.*?--.*?\))?')
re_doc_comment = re.compile(r'^\( > (.*?)\)?$')

wordlist = []
for filename in sys.argv[1:]:
    print "scanning", filename
    last_comment = []
    for line in open(filename):
        m = re_doc_comment.match(line)
        if m:
            last_comment.append(m.group(1))

        m = re_word.match(line)
        if m:
            #~ print m.groups()
            wordlist.append((
                    m.group('name'),
                    m.group('balance') or 'n/a',
                    filename,
                    u'\n'.join(last_comment),
                    ))
            last_comment = []

output = open('forth_words.rst', 'w')
output.write("""\
=================
 Forth Word List
=================
.. contents::
""")
for word, stackinfo, filename, doc in sorted(wordlist):
    output.write('\n``%s``\n' % word)
    output.write('%s\n' % ('-'*(4+len(word))))
    output.write('%s\n\n' % doc)
    output.write('- stack: ``%s``\n' % stackinfo)
    output.write('- defined in file: ``%s``\n' % filename)

