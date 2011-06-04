#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
This is a parser for MSP430 memory/peripheral descriptions.

Supported commands are:

PERIPHERAL <name>  ...  END-PERIPHERAL
    Define a peripheral. It may consist of multiple REGISTER definitions.

REGISTER  ...  END-REGISTER
    Defines a register - a set of named bits and values.

NAMED <name>
    Set a name and address for the regsiter (address taken from stack).
    Only valid within register definition.

BIT <name>
    Define bit with name (bit number taken from stack). Only valid
    within register definition.

VALUE <name>
    Define multi-bit value name (value taken from stack). Only valid
    within register or peripheral definition.

SHORTCUT <name>
    Define shortcut for current register. When <name> is used within an
    other regoster definition, the bits of this one are copied. Only valid
    within register definition.

BYTE-ACCESS <name>
    Set current regsiter with to 8 bits. Only valid within register
    definition.

WORD-ACCESS <name>
    Set current regsiter with to 16 bits. Only valid within register
    definition.
"""

from msp430.asm import rpn
import pkgutil

class SymbolError(Exception):
    """for errors in de definition file"""


class SymbolDefinitions(rpn.RPN):

    def __init__(self):
        rpn.RPN.__init__(self)
        self.registers_by_name = {}
        self.registers_by_address = {}
        self.peripherals = {}
        self.peripheral = None
        self.bits = None
        self.register_values = None
        self.named = None
        self.included_files = []

    @rpn.word('INCLUDE')
    def word_INCLUDE(self, stack):
        """Include definitions from an other file."""
        name = self.next_word()
        if name not in self.included_files:
            self.included_files.append(name)
            #~ print "XXX including %r" % name
            # XXX currently only internal imports are supported
            data = pkgutil.get_data('msp430.asm', 'definitions/%s.peripheral' % (name,))
            self.interpret(rpn.words_in_string(data, name='definitions/%s.peripheral' % (name,)))

    @rpn.word('BIT')
    def word_BIT(self, stack):
        """Define a bit"""
        if self.bits is None:
            raise SymbolError('BIT outside REGISTER definition not allowed')
        bit_name = self.next_word()
        value = 1 << self.pop()
        self.bits[value] = bit_name
        self.namespace[bit_name.lower()] = value

    @rpn.word('VALUE')
    def word_VALUE(self, stack):
        """Define a value"""
        value_name = self.next_word()
        value = self.pop()
        if self.register_values is not None:
            self.register_values[value] = value_name
        elif self.peripheral is not None:
            if '__values__' not in self.peripheral:
                self.peripheral['__values__'] = {}
            self.peripheral['__values__'][value] = value_name
        else:
            raise SymbolError('VALUE outside REGISTER or PERIPHERAL definition not allowed')
        self.namespace[value_name.lower()] = value

    @rpn.word('REGISTER')
    def word_REGISTER(self, stack):
        """Start definition of a register"""
        if self.bits is not None:
            raise SymbolError('missing END-REGISTER')
        if self.peripheral is None:
            raise SymbolError('not within PERIPHERAL')
        self.bits = {}
        self.register_values = {}
        self.register_width = None
        self.named = []

    @rpn.word('SHORTCUT')
    def word_SHORTCUT(self, stack):
        """Set a shortcut for the current register, so that it can be reused"""
        if self.bits is None:
            raise SymbolError('only possible within REGISTER definition')
        symbol_name = self.next_word()
        def update_bits(stack, bits=self.bits):
            self.bits.update(bits)
        self.namespace[symbol_name.lower()] = update_bits

    @rpn.word('NAMED')
    def word_NAMED(self, stack):
        """Set a name for an address that represents current register"""
        if self.bits is None:
            raise SymbolError('only possible within REGISTER definition')
        name = self.next_word()
        address = self.pop()
        self.named.append((name, address))

    @rpn.word('VIRTUAL')
    def word_VIRTUAL(self, stack):
        """Set a name current register, not assigning it to an address"""
        if self.bits is None:
            raise SymbolError('only possible within REGISTER definition')
        name = self.next_word()
        self.named.append((name, None))

    @rpn.word('BYTE-ACCESS')
    def word_BYTE_ACCESS(self, stack):
        """Set access mode for current peripheral"""
        if self.bits is None:
            raise SymbolError('only possible within REGISTER definition')
        self.register_width = 8

    @rpn.word('WORD-ACCESS')
    def word_WORD_ACCESS(self, stack):
        """Set access mode for current peripheral"""
        if self.bits is None:
            raise SymbolError('only possible within REGISTER definition')
        self.register_width = 16

    @rpn.word('END-REGISTER')
    def word_END_REGISTER(self, stack):
        """Terminate current REGISTER definition"""
        if self.bits is None:
            raise SymbolError('currently not within REGISTER defintion')
        for name, address in self.named:
            register = {}
            register['__name__'] = name
            if address is not None:
                register['__address__'] = address
            register['__bits__'] = self.bits
            register['__values__'] = self.register_values
            if self.register_width is not None:
                register['__width__'] = self.register_width
            self.registers_by_name[name] = register
            self.registers_by_address[address] = register
            self.peripheral[name] = register
        self.bits = None
        self.register_values = None
        self.register_width = None
        self.named = None

    @rpn.word('PERIPHERAL')
    def word_PERIPHERAL(self, stack):
        """begin a new PERIPHERAL definition"""
        if self.peripheral is not None:
            raise SymbolError('missing END-PERIPHERAL')
        peripheral_name = self.next_word()
        self.peripheral = {}
        self.peripherals[peripheral_name] = self.peripheral

    @rpn.word('END-PERIPHERAL')
    def word_END_PERIPHERAL(self, stack):
        """Terminate current PERIPHERAL definition"""
        if self.bits is not None:
            raise SymbolError('END-PERIPHERAL without previous END-REGISTER')
        if self.peripheral is None:
            raise SymbolError('currently not within PERIPHERAL defintion')
        self.peripheral = None

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def parse_words(iterable):
    """\
    Parse a configuration file/text using the given iterable.
    """
    s = SymbolDefinitions()
    s.interpret(iterable)
    return s


def load_symbols(filename):
    """\
    Load symbols from given filename.
    """
    return parse_words(rpn.words_in_file(filename))


def load_internal(name):
    """\
    Load symbols from internal definition given name.
    """
    data = pkgutil.get_data('msp430.asm', 'definitions/%s.peripheral' % (name,))
    return parse_words(rpn.words_in_string(data))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# test only
if __name__ == '__main__':
    from optparse import OptionParser
    from pprint import pprint
    import os.path

    parser = OptionParser()

    parser.add_option("--test",
            action = "store_true",
            dest = "test",
            default = False,
            help = "test run using internal data")

    (options, args) = parser.parse_args()

    try:
        if options.test:
            symbols = load_symbols(os.path.join(os.path.dirname(__file__), 'definitions', 'F1xx.txt'))
            pprint(symbols.peripherals)

        for filename in args:
            symbols = load_symbols(filename)
            pprint(symbols.peripherals)
    except rpn.RPNError as e:
        print "%s:%s: %s" % (e.filename, e.lineno, e)
        #~ raise
