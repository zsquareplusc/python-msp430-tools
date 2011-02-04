#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Helper module to parse [msp]gcc/binutils listing files.
"""

import re

regexp_address = re.compile(r'([0-9a-f]+).*\t([0-9a-f]+) (\w+)')

def label_address_map(filename):
    """\
    Scan the listing and return a dict with variables as keys, address of
    them as values.
    """
    labels = {}

    for line in open(filename):
        # don't read the entire file, just the symbol table at the beginning
        if line.startswith("Disassembly"): break
        # match labels
        m = regexp_address.match(line)
        if m:
            address = int(m.group(1), 16)
            size    = int(m.group(2), 16)
            label   = m.group(3)
            labels[label] = address
    return labels

