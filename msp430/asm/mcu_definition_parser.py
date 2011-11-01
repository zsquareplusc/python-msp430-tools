#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
This is a parser for configuration files that describe the memory map of a
micro controller.

The syntax is quite simple: it is parsed as white space delimited words.
# <-- this is a comment, it skips the rest of the line

It also supports templates that can be used to abbreviate definitions.
Template processing is also quite simple. Once the template text and the
variables are defined, it reads in the words, assigns it to the variables.
Every time values for all variables are available it parses the resulting text
using the same rules described here.

Supported commands are:




Words in brackets ("<...>") mean that the words following the command are
consumed as parameter to the command.

Example::

    memory-map-begin
        name        LOGICAL
        # declare a "DATA" segment at the beginning of RAM
        segment     .data           in:RAM
        segment     .bss            in:RAM
        segment     .noinit         in:RAM
        symbol      _stack          in:RAM,location:end


        # declare multiple segments that are located in FLASH
        programmable segment     .text           in:FLASH
        programmable segment     .const          in:FLASH
        programmable segment     .data_init      in:FLASH,mirror:.data
    memory-map-end

    memory-map-begin
        name         MSP430F2xx
        based-on     LOGICAL
        read-only    segment     .bootloader     0x0c00-0x0fff
        programmable segment     .infomem        0x1000-0x10ff
        programmable segment     .infoD          0x1000-0x103f
        programmable segment     .infoC          0x1040-0x107f
        programmable segment     .infoB          0x1080-0x10bf
        programmable segment     .infoA          0x10c0-0x10ff
        programmable segment     .vectors        0xffe0-0xffff
    memory-map-end

    template-begin
        memory-map-begin
            based-on    MSP430F2xx
            segment     RAM             <RAM>
            programmable segment     FLASH           <FLASH>
            name                        <MCU>
        memory-map-end
    template-variables
        <MCU>           <RAM>           <FLASH>
    template-values
        MSP430F2001     0x0200-0x027f   0xfc00-0xffdf   # 128B RAM, 1kB Flash
        MSP430F2002     0x0200-0x027f   0xfc00-0xffdf   # 128B RAM, 1kB Flash
        MSP430F2003     0x0200-0x027f   0xfc00-0xffdf   # 128B RAM, 1kB Flash
        MSP430F2011     0x0200-0x027f   0xf800-0xffdf   # 128B RAM, 2kB Flash
        MSP430F2012     0x0200-0x027f   0xf800-0xffdf   # 128B RAM, 2kB Flash
        MSP430F2013     0x0200-0x027f   0xf800-0xffdf   # 128B RAM, 2kB Flash
    template-end
"""

import rpn
import pkgutil

class MCUDefintitionError(Exception):
    """for errors in de MCU definition file"""


class MCUDefintitions(rpn.RPN):

    def __init__(self):
        rpn.RPN.__init__(self)
        self.flags = []
        self.memory_maps = {}
        self.memory_map = None
        self.order = 0

    def address_range(self, range_str):
        """\
        Split an address range (string) like '0x0200-0x0300' in a (from, to)
        tuple.
        """
        a, b = range_str.split('-')
        return int(a, 0), int(b, 0)

    @rpn.word('TEMPLATE-BEGIN')
    def word_TEMPLATE_BEGIN(self, stack):
        """\
        Read and execute a template. This command consists of 3 sections:

        - definition of a text
        - definition of a set of variables
        - values for the variables

        template-begin
            Begin a template. What follows is the text of the template itself.  It may
            contain special words that will be used as variables.  They can have any
            name. The template text is finished with the command
            'template_variables'.

        template-variables
            The names of the variables follow. These are the words that are used in the
            previously defined template text. This section is terminated by
            'template_values'.

        template-values
            Values are following until 'template_end' is found. Each word that is read
            is assigned to the list of values. When the list of values has the same
            length as the list of variables are they replaced in the template text and
            the resulting text is parsed again.

        template-end
            Denotes the end of a values section in a template.

        Example::

            template-begin
                memory-map-begin
                    name        <MCU>
                    based-on    MSP430F2xx
                                 segment     RAM             <RAM>
                    programmable segment     FLASH           <FLASH>
                memory-map-end
            template-variables
                <MCU>           <RAM>           <FLASH>
            template-values
                MSP430F2001     0x0200-0x027f   0xfc00-0xffdf   # 128B RAM, 1kB Flash
                MSP430F2002     0x0200-0x027f   0xfc00-0xffdf   # 128B RAM, 1kB Flash
                MSP430F2003     0x0200-0x027f   0xfc00-0xffdf   # 128B RAM, 1kB Flash
                MSP430F2011     0x0200-0x027f   0xf800-0xffdf   # 128B RAM, 2kB Flash
                MSP430F2012     0x0200-0x027f   0xf800-0xffdf   # 128B RAM, 2kB Flash
                MSP430F2013     0x0200-0x027f   0xf800-0xffdf   # 128B RAM, 2kB Flash
            template-end
        """
        template = []
        # read the template itself
        while True:
            word = self.next_word()
            if word.lower() == 'template-variables':
                break
            template.append(word)
        template = ' '.join(template)
        # read the variables
        template_variables = []
        while True:
            word = self.next_word()
            if word.lower() == 'template-values':
                break
            template_variables.append(word)
        # apply the template to the following values
        template_row = []
        while True:
            word = self.next_word()
            if word.lower() == 'template-end':
                if template_row:
                    raise MCUDefintitionError('Values in template values section left')
                break
            # collect values
            template_row.append(word)
            # enough values for template -> apply
            if len(template_row) == len(template_variables):
                t = template
                for k, v in zip(template_variables, template_row):
                    t = t.replace(k, v)
                self.memory_maps.update(parse_words(iter(t.split())))
                template_row = []


    @rpn.word('PROGRAMMABLE')
    def word_PROGRAMMABLE(self, stack):
        """\
        Set flag that the next defined segment is programmed on the target.
        Example::

            programmable segment     .text           in:FLASH
        """
        if self.memory_map is None:
            raise MCUDefintitionError('flags outside memory map definition not allowed')
        self.flags.append('programmable')

    @rpn.word('READ-ONLY')
    def word_READ_ONLY(self, stack):
        """\
        Set flag that the next defined segment is read-only (not programmed to
        target).
        Example::

            read-only  segment bootloader 0x0c00-0x0fff
        """
        if self.memory_map is None:
            raise MCUDefintitionError('flags outside memory map definition not allowed')
        self.flags.append('read-only')

    @rpn.word('MEMORY-MAP-BEGIN')
    def word_MEMORY_MAP_BEGIN(self, stack):
        """
        Start the definition of a memory map for a MCU. It's expected that the
        NAME_ and SEGMENT_ commands are used to define a memory map.
        Example::

            memory-map-begin
                name        LOGICAL
                # declare a "DATA" segment at the beginning of RAM
                segment     .data           in:RAM
                segment     .bss            in:RAM
                segment     .noinit         in:RAM
                symbol      _stack          in:RAM,location:end


                # declare multiple segments that are located in FLASH
                programmable segment     .text           in:FLASH
                programmable segment     .const          in:FLASH
                programmable segment     .data_init      in:FLASH,mirror:.data
            memory-map-end

            memory-map-begin
                name         MSP430F2xx
                based-on     LOGICAL
                read-only    segment     .bootloader     0x0c00-0x0fff
                programmable segment     .infomem        0x1000-0x10ff
                programmable segment     .infoD          0x1000-0x103f
                programmable segment     .infoC          0x1040-0x107f
                programmable segment     .infoB          0x1080-0x10bf
                programmable segment     .infoA          0x10c0-0x10ff
                programmable segment     .vectors        0xffe0-0xffff
            memory-map-end
        """
        if self.memory_map is not None:
            raise MCUDefintitionError('MEMORY-MAP-BEGIN without terminating the last map')
        self.memory_map = {}

    @rpn.word('MEMORY-MAP-END')
    def word_MEMORY_MAP_END(self, stack):
        """Terminate current memory map definition. See `MEMORY-MAP-BEGIN`_."""
        if '__name__' not in self.memory_map:
            raise MCUDefintitionError('each memory map requires a NAME')
        self.memory_maps[self.memory_map['__name__']] = self.memory_map
        self.memory_map = None

    @rpn.word('SEGMENT')
    def word_SEGMENT(self, stack):
        """\
        Example::

            segment <name>  <memory_range>

        Defines a segment.
        Previously set flags are applied and cleared.
        ``<memory_range>`` can be an address range like ``0x0200-0x0300`` or a
        set of ``key:value`` pairs:

        ``in:<segment_name>``
            This segment is placed within an other parent segment. The memory
            range is inherited from the parent. Multiple segments can be placed
            in one parent segment.

        ``mirror:<segment_name>``
            The contents of this segment will be a copy of the given one. A typical use is
            to make a copy of the ``.data`` section that is in RAM and needs to
            be initialized (by the startup code) from a copy located in Flash memory::

                programmable segment     .data_init      in:FLASH,mirror:.data
        """
        if self.memory_map is None:
            raise MCUDefintitionError('SEGMENT outside memory map definition not allowed')
        segment_name = self.next_word()
        address = self.next_word()
        if ':' in address:
            # dictionary mode
            self.memory_map[segment_name] = {}
            for pair in address.split(','):
                key, value = pair.split(':')
                self.memory_map[segment_name][key] = value
        else:
            # address range
            start, end = self.address_range(address)
            self.memory_map[segment_name] = {'start':start, 'end':end}
        self.memory_map[segment_name]['order'] = self.order
        self.memory_map[segment_name]['flags'] = self.flags
        self.memory_map[segment_name]['__name__'] = segment_name
        self.memory_map[segment_name]['__type__'] = 'segment'
        self.flags = []
        self.order += 1

    @rpn.word('SYMBOL')
    def word_SYMBOL(self, stack):
        """\
        Example::

            symbol <name> <address>

        Defines a symbol with the value specified. ``<address>`` can also be a computed
        value. e.g. ``in:RAM,location:end``.

        Supported are: ``in:<segment_name>`` and ``location:[start|end]``.  These
        values are computed at load time, i.e. the segment still have the address
        range specified in the definition (opposed to the values after the linker has
        "shrinked" the segments to the size of actually present data). Note that
        ``location:end`` is the segments last address plus one (end is exclusive in
        this case).
        """
        symbol_name = self.next_word()
        address = self.next_word()
        if ':' in address:
            # dictionary mode
            self.memory_map[symbol_name] = {}
            for pair in address.split(','):
                key, value = pair.split(':')
                self.memory_map[symbol_name][key] = value
        else:
            # address
            self.memory_map[symbol_name] = {'address':int(address,16)}
        self.memory_map[symbol_name]['__name__'] = symbol_name
        self.memory_map[symbol_name]['__type__'] = 'symbol'

    @rpn.word('NAME')
    def word_NAME(self, stack):
        """\
        Set the name of a memory map.
        Example::

            name <name>
        """
        if self.memory_map is None:
            raise MCUDefintitionError('NAME outside memory map definition not allowed')
        self.memory_map['__name__'] = self.next_word()

    @rpn.word('BASED-ON')
    def word_BASED_ON(self, stack):
        """\
        Tell that a memory map definition builds on an other definition.
        All the definitions are merged when used.
        Example::

            based-on <name>

        """
        if self.memory_map is None:
            raise MCUDefintitionError('BASED-ON outside memory map definition not allowed')
        self.memory_map['__based_on__'] = self.next_word()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def parse_words(iterable):
    """\
    Parse a configuration file/text using the given iterable.
    """
    p = MCUDefintitions()
    p.interpret(iterable)
    return p.memory_maps


def expand_definition(memory_maps, name):
    """\
    Recursively expand the '__based_on__' keys to create a 'flat' definition
    for the given MCU name.
    """
    map = dict(memory_maps[name]) # get a copy of the dict
    try:
        base = map.pop('__based_on__')
    except KeyError:
        pass
    else:
        map.update(expand_definition(memory_maps, base))
    if '__name__' in map: del map['__name__']   # name was overwritten by lowest base
    map['__name__'] = name
    return map


def load_internal():
    """\
    Load configuration file and only return a single, expanded memory map for
    given mcu_name.
    """
    data = pkgutil.get_data('msp430.asm', 'definitions/msp430-mcu-list.txt')
    return parse_words(rpn.words_in_string(data))

def load_from_file(filename):
    """\
    Load configuration file and only return a single, expanded memory map for
    given mcu_name.
    """
    return parse_words(rpn.words_in_file(filename))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# test only
if __name__ == '__main__':
    from optparse import OptionParser
    from pprint import pprint

    parser = OptionParser()

    parser.add_option("-l", "--list",
            action = "store_true",
            dest = "list",
            default = False,
            help = "list available MCU names")

    parser.add_option("-d", "--dump",
            action = "store_true",
            dest = "dump",
            default = False,
            help = "dump all data instead of pretty printing")

    (options, args) = parser.parse_args()

    try:
        memory_maps = load_internal()
    except rpn.RPNError, e:
        print "%s:%s: %s" % (e.filename, e.lineno, e)
    else:
        if options.list:
            for mcu in sorted(memory_maps):
                print mcu
            #~ pprint(memory_maps)
        for mcu in args:
            print '== memory map for %s ==' % mcu
            memmap = expand_definition(memory_maps, mcu)
            if options.dump:
                pprint(memmap)
            else:
                for name, segment in sorted(memmap.items()):
                    if not name.startswith('__') and 'start' in segment:
                        print '%-12s %08x-%08x %s' % (
                                name,
                                segment['start'],
                                segment['end'],
                                ','.join(segment['flags']))
