#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2001-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Linker for TI MSP430.

Inputs are '.o4' files from 'as.py'
"""

import sys
import codecs
from msp430.asm import mcu_definition_parser
from msp430.asm import rpn, peripherals


class LinkError(rpn.RPNError):
    """\
    Exception class for errors that can occur during linking. The exception can
    be annotated with the location in the source file.
    """


# a segment has a valid range of addresses that is set by
# start_address to end_address (excluding!)
# if the data is complete, a call to shrink_to_fit() adjusts the
# start and end addresses for a final positioning of the data
class Segment(object):
    """\
    Store data bytes along with information about a segment. A segment can
    also contain subsegments.
    """
    def __init__(self, name, start_address=None, end_address=None, align=True, programmable=False, little_endian=True, parent=None, mirror_of=None):
        self.name = name
        self.start_address = start_address
        self.end_address = end_address
        self.align = align          # place data on even addresses
        self.data = []
        self.programmable = programmable
        self.little_endian = little_endian
        self.parent = parent
        self.mirror_of = mirror_of
        self.subsegments = []
        self.read_only = False
        self.order = 0

    def __getitem__(self, segment_name):
        """Easy access to subsegment by name."""
        for segment in self.subsegments:
            if segment.name == segment_name:
                return segment
        raise KeyError('no subsegment with name %s found' % segment_name)

    def sort_subsegments(self, by_address=False):
        """\
        Sort list of subsegments either by order of definition or by order of
        start address.
        """
        if by_address:
            self.subsegments.sort()
        else:
            self.subsegments.sort(lambda a,b: cmp(a.order , b.order))
        for segment in self.subsegments:
            segment.sort_subsegments(by_address)

    def clear(self):
        """Clear data. Recursively with all subsegments."""
        del self.data[:]
        for segment in self.subsegments:
            segment.clear()

    def __len__(self):
        """Get the number of bytes contained in the segment."""
        return len(self.data)

    def __lt__(self, other):
        """Compare function that allows to sort segments by their start_address."""
        return self.start_address < other.start_address

    def __cmp__(self, other):
        """Compare function that allows to sort segments by their start_address."""
        return cmp(self.start_address, other.start_address)

    def __repr__(self):
        return 'Segment[%s, %s, %s%s%s]' % (
                self.name,
                self.start_address is not None and '0x%04x' % self.start_address or None,
                self.end_address is not None and '0x%04x' % self.end_address or None,
                self.programmable and ', programmable=True' or '',
                self.little_endian and ', little_endian=True' or '')

    def print_tree(self, output, indent='', hide_empty=False):
        """Output segment and subsegments."""
        if None not in (self.end_address, self.start_address):
            size = self.end_address - self.start_address
            if size:
                start = '0x%04x' % (self.start_address,)
                end = '0x%04x' % (self.end_address - 1,)
            else:
                start = end = 'n/a'
            size_str = '%d B' % (size,)
        else:
            start = end = ''
            size = 0
            size_str = ''
        if not hide_empty or size:
            output.write("%s%-24s%s%8s-%-8s %8s  %s%s%s%s\n" % (
                    indent,
                    self.name,
                    ' ' * (8-len(indent)),
                    start,
                    end,
                    size_str,
                    self.little_endian and 'LE' or 'BE',
                    self.programmable and ', downloaded' or '',
                    self.mirror_of and (', mirror of "%s"' % (self.mirror_of,)) or '',
                    self.read_only and ', read_only' or '',
                    ))
        for segment in self.subsegments:
            segment.print_tree(output, indent=indent+'   ', hide_empty=hide_empty)

    def shrink_to_fit(self, address=None):
        """modify start- and end_address of segment to fit the data that it contains"""
        #~ if self.read_only: return

        if address is None:
            address = self.start_address
        else:
            self.start_address = address
        # pad own data
        if self.align and len(self.data) & 1:
            self.data.append(0xff) # pad to align data on even addresses
        # reserve space for own data
        if address is not None:
            address += len(self.data)
        # assign areas for each subsegment
        for segment in self.subsegments:
            segment.shrink_to_fit(address)
            if address is not None:
                address += len(segment.data)
        # save true end address, but not before checking if data fits in segment
        if None not in (address, self.end_address) and address > self.end_address:
            raise LinkError('Segment %s contains too much data (total %d bytes, %d too much)' % (
                                self.name, len(self.data), address - self.end_address))
        if address is not None:
            self.end_address = address

    def write_8bit(self, value):
        """Write one byte"""
        self.data.append(value & 0xff)

    def write_16bit(self, value):
        """Write two bytes. Order in memory depends on endianness of segment"""
        if self.little_endian:
            self.data.append(value & 0xff)
            self.data.append((value >> 8) & 0xff)
        else:
            self.data.append((value >> 8) & 0xff)
            self.data.append(value & 0xff)

    def write_32bit(self, value):
        """Write four bytes. Order in memory depends on endianness of segment"""
        if self.little_endian:
            self.data.append(value & 0xff)
            self.data.append((value >> 8) & 0xff)
            self.data.append((value >> 16) & 0xff)
            self.data.append((value >> 24) & 0xff)
        else:
            self.data.append((value >> 24) & 0xff)
            self.data.append((value >> 16) & 0xff)
            self.data.append((value >> 8) & 0xff)
            self.data.append(value & 0xff)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Linker(rpn.RPN):
    """\
    The linker processes a set of instructions and builds a memory image.

    The current address is maintained (PC) and can be used in expressions.

    It supports labels which can be set to a arbitrary value or the current
    address. The data handling instructions can calculate with the labels
    values (and PC).

    The file format that the linker reads has Forth like syntax. The rpn module
    is used to read and process it. Linker specific instructions are
    implemented in this class.
    """
    def __init__(self, instructions=[]):
        rpn.RPN.__init__(self)
        # separate name space for symbols from the data
        self.labels = {}
        # weak aliases are checked if a label is undefined.
        self.weak_alias = {}
        # the linking will require multiple passes, a flag controls
        # if errors are fatal or ignored
        self.errors_are_fatal = True
        # to check labels for duplicate definition
        self.check_labels = None
        # The link instructions
        self.instructions = instructions
        # information about the input
        self.source_filename = '<unknown>'
        self.source_line = None
        self.source_column = None
        # internal states
        self.current_segment = None
        self.address = 0
        self.segments = {}

    def linker_error(self, message):
        """\
        Raise a LinkError. This function generate an exception with information
        annotated about source (filename, lineo, etc.).
        """
        raise LinkError(message, self.source_filename, self.source_line, self.source_column)


    @rpn.word('RESET')
    def word_reset(self, rpn):
        """\
        Reset state. This can be used between files, so that every file starts
        with the same preconditions (such as no segment selected).
        """
        self.current_segment = None
        self.source_filename = '<unknown>'
        self.source_line = None
        self.source_column = None

    @rpn.word('SEGMENT')
    def word_SEGMENT(self, rpn):
        """\
        Select a different segment to put data into. The segment name must be
        known. The location counter is set to append to any existing data in
        the segment. Example::

            SEGMENT .vectors
        """
        name = rpn.next_word()
        try:
            segment = self.segments[name]
        except KeyError:
            self.linker_error("There is no segment named %s" % (name,))
        self.current_segment = segment
        if segment.start_address is not None:
            address = segment.start_address
        else:
            # this happens in the first pass
            address = 0
        self.address = address + len(segment.data)

    @rpn.word('FILENAME')
    def word_FILENAME(self, rpn):
        """\
        Store source filename for error messages. This also clears all local
        symbols. Example::

            FILENAME source.S
        """
        self.source_filename = self.next_word()

    @rpn.word('LINE')
    def word_LINE(self, rpn):
        """\
        Store source filename for error messages.
        Example::

            5 LINE
        """
        self.source_line = self.pop()

    @rpn.word('COLUMN')
    def word_COLUMN(self, rpn):
        """\
        Store source filename for error messages.
        Example::

            10 COLUMN
        """
        self.source_column = self.pop()

    @rpn.word('8BIT')
    def word_8BIT(self, rpn):
        """\
        Store a byte (8 bits) from the stack in the current segment. The value
        is masked to 8 bits. Example::

            0x12 8BIT
        """
        if self.current_segment is None:
            self.linker_error('No segment selected (use .text, .section etc.)')
        self.current_segment.write_8bit(int(self.pop()))
        self.address += 1

    @rpn.word('16BIT')
    def word_16BIT(self, rpn):
        """\
        Store a word (16 bits) from the stack in the current segment. The value
        is masked to 16 bits. Example::

            0x1234 16BIT
        """
        if self.current_segment is None:
            self.linker_error('No segment selected (use .text, .section etc.)')
        self.current_segment.write_16bit(int(self.pop()))
        self.address += 2

    @rpn.word('32BIT')
    def word_32BIT(self, rpn):
        """\
        Store an integer (32 bits) from the stack in the current segment. The value
        is masked to 32 bits. Example::

            0x12345678 32BIT

        """
        if self.current_segment is None:
            self.linker_error('No segment selected (use .text, .section etc.)')
        self.current_segment.write_32bit(int(self.pop()))
        self.address += 4

    @rpn.word('RESERVE')
    def word_RESERVE(self, rpn):
        """\
        Reserve space in the current segment. Length in bytes is taken from
        the stack.
        """
        if self.current_segment is None:
            self.linker_error('No segment selected (use .text, .section etc.)')
        count = self.pop()
        for i in xrange(count):
                self.current_segment.data.append(None)
        self.address += count

    @rpn.word('ALIGN')
    def word_ALIGN(self, rpn):
        """Make location counter (PC) even."""
        if self.current_segment is None:
            self.linker_error('No segment selected (use .text, .section etc.)')
        exponent = self.pop()
        if exponent > 0:
            mask = (1 << exponent) - 1
            while self.address & mask:
                self.current_segment.data.append(None)
                self.address += 1

    @rpn.word('PC')
    def word_PC(self, rpn):
        """Put the value of the location counter on the stack."""
        self.push(self.address)

    @rpn.word('CONSTANT-SYMBOL')
    def _constant_symbol(self, rpn):
        """Create symbol and assign to it the value from the stack. Example: ``1 CONSTANT-SYMBOL somelabel``"""
        name = self.name_symbol(self.next_word())
        value = self.pop()
        if self.check_labels is not None:
            if name in self.check_labels and self.check_labels[name] != value:
                self.linker_error('redefinition of symbol %r with different value (previous: %r, new: %r)' % (
                            name,
                            self.labels[name],
                            value))
            self.check_labels[name] = value
        self.labels[name] = value

    @rpn.word('WEAK-ALIAS')
    def _weak_alias(self, rpn):
        """\
        Assign a symbol for an other symbol. The alias is used when the symbol is not defined.

        Example: ``WEAK-ALIAS __vector_0 _unused_vector`` here, if
        ``__vector_0`` is not defined, it will point to ``_unused_vector``.
        """
        name = self.name_symbol(self.next_word())
        alias = self.name_symbol(self.next_word())
        if name in self.weak_alias and self.weak_alias[name] != alias:
            self.linker_error('Weak alias %r redefined (old value: %r)' % (name, self.weak_alias[name]))
        self.weak_alias[name] = alias

    @rpn.word('CREATE-SYMBOL')
    def _create_symbol(self, rpn):
        """Mark current location with symbol. Example: ``CREATE-SYMBOL somelabel``"""
        name = self.name_symbol(self.next_word())
        #~ # this simple check does not work as we're doing multiple passes
        if self.check_labels is not None:
            if name in self.check_labels:
                self.linker_error('Label %r redefined (old value: %r)' % (name, self.labels[name]))
            self.check_labels[name] = self.address
        self.labels[name] = self.address

    @rpn.word('GET-SYMBOL')
    def _get_symbol(self, rpn):
        """Get a symbol and put its value on the stack. Example: ``GET-SYMBOL somelabel``"""
        name = self.name_symbol(self.next_word())
        # check if there is an alias as long as its not already found in labels
        if name in self.weak_alias and name not in self.labels:
            name = self.weak_alias[name]
        try:
            value = self.labels[name]
        except KeyError:
            # other wise it is undefined
            if self.errors_are_fatal:
                self.linker_error('Label %r is not defined' % (name,))
            else:
                value = 0
        self.push(value)


    # XXX this should be separate as it is machine dependant (while the rest of
    #     the linker is not). The calculation is not the problem, the error
    #     messages are - there are currently no instructions for that
    @rpn.word('JMP')
    def word_JMP(self, rpn):
        """\
        MSP430 jump instruction (insns dist). Takes offset and instruction
        from stack, calculate final opcode and store it.

        Example::

            0x2000 GET-SYMBOL somelabel PC - 2 - JMP
        """
        distance = self.pop()
        instruction = self.pop()
        if distance & 1:
            if self.errors_are_fatal:
                self.linker_error('Jump distance must be of even length (distance %d)' % (distance,))
        if distance < -512*2 or distance > 511*2:
            if self.errors_are_fatal:
                self.linker_errorr('Jump out of range (distance %d)' % (distance,))
        else:
            instruction |= 0x3ff & (distance/2)
        self.current_segment.write_16bit(instruction)
        self.address += 2

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def segments_from_definition(self, segment_definitions):
        """\
        Initialize flat list of segments and the top level segment given a
        dictionary with segment descriptions (input from
        mcu_definition_parser.
        """
        self.top_segment = Segment('<default segment>')
        symbols = []
        # step 1: create a flat list of segments
        for name, definition in segment_definitions.items():
            # skip special entries
            if name.startswith('__'): continue
            if definition['__type__'] == 'segment':
                # create a segment
                start, end = definition.get('start'), definition.get('end')
                if end is not None: end += 1
                self.segments[name] = Segment(
                        name,
                        start,
                        end,
                        programmable = 'programmable' in definition['flags'],
                        parent = definition.get('in'),
                        mirror_of = definition.get('mirror'),
                        )
                self.segments[name].order = definition.get('order')
                self.segments[name].read_only = 'read-only' in definition['flags']
            elif definition['__type__'] == 'symbol':
                symbols.append(definition)
            else:
                self.linker_error('unknown record type in memory map: %r' % definition['__type__'])

        # step 2: create a hierarchical tree of segments
        for segment in self.segments.values():
            if segment.parent is not None:
                self.segments[segment.parent].subsegments.append(segment)
            else:
                self.top_segment.subsegments.append(segment)

        self.top_segment.sort_subsegments()
        self.segments['default'] = self.top_segment

        # create calculated symbols
        for definition in symbols:
            name = definition['__name__']
            if 'address' in definition:
                self.labels[name] = definition['address']
            else:
                segment = self.segments[definition['in']]
                location = definition.get('location', 'start')
                if location == 'start':
                    self.labels[name] = segment.start
                elif location == 'end':
                    self.labels[name] = segment.end_address
                else:
                    self.linker_error('invalid location %r for symbol %r' % (location, name))

    def update_mirrored_segments(self):
        """In all mirrored segments, update the copied data."""
        for segment in self.segments.values():
            if segment.mirror_of is not None:
                segment.data = list(self.segments[segment.mirror_of].data)

    def name_symbol(self, name):
        """Name mangling for local symbols, otherwise return original name."""
        if name[0] == '.':
            name = ".%s%s" % (self.source_filename.encode('hex'), name[1:])
        return name

    def clear_local_symbols(self):
        """Forget about local symbols (the ones starting with a dot)"""
        for name in list(self.labels):  # iterate over a copy
            if name[0] == '.':
                del self.labels[name]

    # helper functions for 3 pass linking

    def pass_one(self):
        """\
        Shortcut to run the 1st pass of 3 stage linking.
        Segment sizes and positioning is determined.
        """
        self.errors_are_fatal = False     # 1st two runs are used to find out data positioning only
        self.top_segment.clear()
        self.interpret_sequence(self.instructions)
        # update segment start and end_addresses, handle alignment
        self.update_mirrored_segments()
        self.top_segment.shrink_to_fit()

    def pass_two(self):
        """\
        Shortcut to run the 2nd pass of 3 stage linking.
        This run is used to find all labels at their final locations.
        """
        self.top_segment.clear()
        self.check_labels = {}
        self.interpret_sequence(self.instructions)
        self.check_labels = None
        # create automatic labels for all segments (start/end)
        for segment in self.segments.values():
            name = segment.name.replace('.', '')    # remove dots in names
            # create labels if addresses are defined
            if segment.start_address is not None:
                self.labels['_%s_start' % name] = segment.start_address
            if segment.end_address is not None:
                self.labels['_%s_end' % name] = segment.end_address

    def pass_three(self):
        """\
        Shortcut to run the 3rd pass of 3 stage linking.
        This run uses all the labels and creates the final contents.
        """
        self.errors_are_fatal = True
        self.top_segment.clear()
        self.interpret_sequence(self.instructions)
        self.update_mirrored_segments()
        self.clear_local_symbols()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def substitute_none(data):
    """Ensure that stream does not contain None"""
    for value in data:
        if value is None:
            yield 0
        else:
            yield value


def to_addressed_byte_stream(segments):
    """\
    Create a stream of (address, byte) tuples from the list of segments. The
    output is sorted by ascending address.
    """
    for segment in sorted(segments.values()):
        if segment.data and segment.programmable:
            for n, byte in enumerate(substitute_none(segment.data)):
                yield (segment.start_address + n, byte)


def to_TI_Text(segments):
    """\
    Return a string containing TI-Text, given a dictionary with segments.
    """
    out = []
    row_count = 0
    last_address = None
    for address, byte in to_addressed_byte_stream(segments):
        # need to start a new block if address jumping
        if address - 1 != last_address:
            if out and row_count != 0: # except for the 1st one
                out.append("\n")
            out.append("@%04x\n" % (address,))
            row_count = 0
        last_address = address
        # output byte
        out.append("%02x" % byte)
        row_count += 1
        # after 16 bytes (a row) insert a newline
        if row_count == 16:
            out.append("\n")
            row_count = 0
        else:
            out.append(" ")
    if row_count != 0:
        out.append("\n")
    out.append("q\n")
    return ''.join(out)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main():
    import os
    import logging
    from optparse import OptionParser
    logging.basicConfig()

    parser = OptionParser(usage="""\
%prog [options] [FILE...]|-]

If no input files are specified data is read from stdin.
Output is in "TI-Text" format."""
            )
    parser.add_option(
            "-o", "--outfile",
            dest="outfile",
            help="name of the resulting binary (TI-Text)",
            metavar="FILE",
            default=None)

    parser.add_option(
            "-T", "--segmentfile",
            dest="segmentfile",
            help="linker definition file",
            metavar="FILE",
            default=None)

    parser.add_option(
            "-m", "--mcu",
            dest="mcu_name",
            help="name of the MCU (used to load memory map)",
            metavar="MCU",
            default='MSP430F1121')

    parser.add_option(
            "--mapfile",
            dest="mapfile",
            help="write map file",
            metavar="FILE")

    parser.add_option(
            "-v", "--verbose",
            action="count",
            dest="verbose",
            default=0,
            help="print status messages, gan be given multiple times to increase messages")

    parser.add_option(
            "--debug",
            action="store_true",
            dest="debug",
            default=False,
            help="print debug messages")

    parser.add_option("--symbols",
            dest="symbols",
            help="read register names for given architecture (e.g. F1xx)",
            metavar="NAME")

    (options, args) = parser.parse_args()

    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif options.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARN)

    # prepare output
    if options.outfile is not None:
        out = open(options.outfile, "wb")
    else:
        out = sys.stdout

    # XXX make stderr unicode capable
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr)

    instructions = []
    for filename in args:
        if filename == '-':
            if options.verbose > 2:
                sys.stderr.write(u'reading stdin...\n')
            instructions.append('reset')
            instructions.extend(['filename', '<stdin>'])
            instructions.extend(sys.stdin.read().split())
        else:
            if options.verbose > 2:
                sys.stderr.write(u'reading file "%s"...\n'% filename)
            instructions.append('reset')
            instructions.extend(['filename', filename])
            try:
                instructions.extend(rpn.words_in_file(filename))
            except IOError, e:
                sys.stderr.write('ld: %s: File not found\n' % (filename,))
                sys.exit(1)

    linker = Linker(instructions)

    # load symbols
    if options.symbols is not None:
        all_peripherals = peripherals.load_internal(options.symbols)
        for peripheral in all_peripherals.peripherals.values():
            for reg_name, register in peripheral.items():
                if reg_name.startswith('__'): continue
                if '__address__' in register:
                    linker.labels[register['__name__']] = register['__address__']
                for value, name in register['__bits__'].items():
                    linker.labels[name] = value
                for value, name in register['__values__'].items():
                    linker.labels[name] = value
            if '__values__' in peripheral:
                for value, name in peripheral['__values__'].items():
                    linker.labels[name] = value

    # ========= load MCU definition =========

    if options.verbose > 1:
        sys.stderr.write("Step 1: load segment descriptions.\n")

    # load the file and get the desired MCU description
    try:
        if options.segmentfile:
            mem_maps = mcu_definition_parser.load_from_file(options.segmentfile)
        else:
            mem_maps = mcu_definition_parser.load_internal()
        options.mcu_name = options.mcu_name.upper() # XXX hack
        segment_definitions = mcu_definition_parser.expand_definition(mem_maps, options.mcu_name)
    except Exception, msg:
        sys.stderr.write('ERROR loading segment descriptions: %s\n' % (msg,))
        sys.exit(1)

    linker.segments_from_definition(segment_definitions)

    if options.verbose > 2:
        sys.stderr.write('Segments available:\n')
        linker.top_segment.print_tree(sys.stderr)

    # ========= Do the actual linking =========

    try:
        if options.verbose > 1:
            sys.stderr.write("Step 2: generate machine code\n")
            sys.stderr.write("        Pass 1: determinate segment sizes.\n")
        linker.pass_one()

        if options.verbose > 1:
            sys.stderr.write("        Pass 2: calculate labels.\n")
        linker.pass_two()

        if options.verbose > 1:
            sys.stderr.write("        Pass 3: final output.\n")
        linker.pass_three()
    except LinkError as e:
        sys.stderr.write(u'%s:%s: %s\n' % (e.filename, e.lineno if e.lineno is not None else '?', e))
        sys.exit(1)
    except rpn.RPNError as e:
        sys.stderr.write(u'%s:%s: %s\n' % (e.filename, e.lineno if e.lineno is not None else '?', e))
        if options.debug and e.text:
            sys.stderr.write(u"%s:%s: input line was: %r\n" % (e.filename, e.lineno, e.text))
        if options.debug: raise
        sys.exit(1)

    # ========= Output final result =========

    if options.verbose > 1:
        sys.stderr.write("Step 3: write machine code to file.\n")

    out.write(to_TI_Text(linker.segments))

    if options.verbose > 1:
        sys.stderr.write("Labels:\n")
        labels = linker.labels.keys()
        labels.sort()
        for i in labels:
            sys.stderr.write(u'    %-24s = 0x%08x\n' % (i, linker.labels[i]))

    if options.mapfile:
        mapfile = codecs.open(options.mapfile, "w", "utf-8")
        labels = [(v,k) for k,v in linker.labels.items()]
        labels.sort()
        for address, label in labels:
            mapfile.write(u'0x%04x %s\n' % (address, label))
        mapfile.close()

    if options.verbose:
        sys.stderr.write('Segments used:\n')
        linker.top_segment.sort_subsegments(by_address=True)
        linker.top_segment.print_tree(sys.stderr, hide_empty=True)


if __name__ == '__main__':
    main()
