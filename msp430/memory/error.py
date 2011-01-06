#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2002-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Error messages for file handler modules.
"""

class FileFormatError(Exception):
    """\
    Exception for "file is not in the expected format" messages.
    """
    def __init__(self, message, filename=None, lineno=None):
        Exception.__init__(self, message)
        self.filename = filename
        self.lineno = lineno

    def __repr__(self):
        return "%s(%s, %s, %s)" % (
                self.__class__.__name__,
                Exception.__repr__(self),
                self.filename,
                self.lineno)

    def __str__(self):
        return "%s:%s: %s)" % (
                self.filename,
                self.lineno,
                Exception.__str__(self))
