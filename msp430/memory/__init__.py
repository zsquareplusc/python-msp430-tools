#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2002-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Manage a set of addressed binary strings (Segments) in a Memory object.
This type of data is used to represent memory contents of teh MCU.
"""

from msp430.memory import titext, elf, intelhex, bin, hexdump, error

class DataStream(object):
    """\
    An iterator for addressed bytes. It yields all the bytes of a ``Memory``
    instance in ascending order. It allows peeking at the current position
    by reading the ``.address`` attribute. ``None`` signals that there are
    no more bytes (and ``next()`` would raise ``StopIteration``).
    """
    def __init__(self, memory):
        self.segments = sorted(list(memory.segments))   # get a sorted copy
        self.address = None
        self.current_offset = None
        self.current_data = None
        if self.segments:
            segment = self.segments.pop(0)
            self.current_data = segment.data
            self.address = segment.startaddress
            self.current_offset = 0

    def next(self):
        if self.current_data is None:
            raise StopIteration()
        result = (self.address, self.current_data[self.current_offset])
        self.address += 1
        self.current_offset += 1
        if self.current_offset >= len(self.current_data):
            if self.segments:
                segment = self.segments.pop(0)
                self.current_data = segment.data
                self.address = segment.startaddress
                self.current_offset = 0
            else:
                self.current_data = None
                self.address = None
        return result

    def __repr__(self):
        return "DS[%s %s]" % (self.address, len(self.segments))


def stream_merge(*streams):
    """\
    Merge multiple streams of addressed bytes. If data is overlapping, take
    it from the later stream in the list.

    :param streams: Any number of ``DataStream`` instances.
    """
    streams = list(streams)
    while streams:
        # get the lowest address, if there are several entries with the same
        # address, take the latest
        next_stream = None
        address = 2**32
        for s in streams:
            if s.address is not None and s.address <= address:
                address = s.address
                next_stream = s
        if next_stream is not None:
            # got one, yield that
            yield next_stream.next()
            # then remove all the elements with lower addresses from all
            # streams. if a stream is exhausted, remove it from the list
            # of streams
            for s in list(streams): # iterate over copy as we delete
                while s.address is not None and s.address <= address:
                    s.next()
                if s.address is None:
                    streams.remove(s)
        else:
            raise ValueError('streams not sorted?')



class Segment(object):
    """Store a string or list with memory contents (bytes) along with its startaddress"""
    def __init__(self, startaddress = 0, data=None):
        if data is None:
            self.data = ''
        else:
            self.data = data
        self.startaddress = startaddress

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return "Segment(startaddress = 0x%04x, data=%r)" % (self.startaddress, self.data)

    def __cmp__(self, other):
        """Compare two segments. Implemented to support sorting a list of segments by address"""
        return cmp(self.startaddress, other.startaddress)

    def __lt__(self, other):
        """Compare two segments. Implemented to support sorting a list of segments by address"""
        return self.startaddress < other.startaddress


class Memory(object):
    """represent memory contents. with functions to load files"""
    def __init__(self, filename=None):
        self.segments = []
        if filename:
            load(self, filename)    # XXX

    def append(self, seg):
        self.segments.append(seg)

    def __getitem__(self, index):
        return self.segments[index]

    def __len__(self):
        return len(self.segments)

    def __repr__(self):
        return "Memory:\n%s" % ('\n'.join([repr(seg) for seg in self.segments]),)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def get_range(self, fromadr, toadr, fill='\xff'):
        """\
        Get a range of bytes from the memory. Unavailable values are filled
        with ``fill`` (default 0xff).

        :param fromadr: Start address (including)
        :param toadr: End address (including)
        :param fill: Fill value (a byte)
        :return: A byte string covering the given memory range.
        """
        res = ''
        toadr = toadr + 1   # python indexes are excluding end, so include it
        while fromadr < toadr:
            for seg in self.segments:
                segend = seg.startaddress + len(seg.data)
                if seg.startaddress <= fromadr and fromadr < segend:
                    if toadr > segend:   # not all data in segment
                        catchlength = segend - fromadr
                    else:
                        catchlength = toadr - fromadr
                    res = res + seg.data[fromadr-seg.startaddress : fromadr-seg.startaddress+catchlength]
                    fromadr = fromadr + catchlength    # adjust start
                    if len(res) >= toadr - fromadr:
                        break   # return res
            else:   # undefined memory is filled with 0xff
                res = res + fill
                fromadr = fromadr + 1 # adjust start
        return res

    def get(self, address, size):
        """\
        Get a range of bytes from the memory.

        :param address: Start address of block to read
        :param size: Size of the of block to read
        :return: A byte string covering the given memory range.
        :exception ValueError: unavailable addresses are tried to read"""
        data = []
        for seg in self.segments:
            #~ print "0x%04x  " * 2 % (seg.startaddress, seg.startaddress + len(seg.data))
            if seg.startaddress <= address and seg.startaddress + len(seg.data) >= address:
                # segment contains data in the address range
                offset = address - seg.startaddress
                length = min(len(seg.data)-offset, size)
                data.append(seg.data[offset:offset+length])
                address += length
        value = ''.join(data)
        if len(value) != size:
            raise ValueError("could not collect the requested data")
        return value

    def set(self, address, contents):
        """\
        Write a range of bytes to the memory. A segment covering the address
        range to be written has to be existent. A ValueError is raised if not
        all data could be written (attention: a part of the data may have been
        written!). The contents may span multiple (existing) segments.

        :param address: Start address of block to read
        :param contents: Bytes to write to the memory
        :exception ValueError: Writing to an undefined memory location
        """
        #~ print "%04x: %r" % (address, contents)
        for seg in self.segments:
            #~ print "0x%04x  " * 3 % (address, seg.startaddress, seg.startaddress + len(seg.data))
            if seg.startaddress <= address and seg.startaddress + len(seg.data) >= address:
                # segment contains data in the address range
                offset = address - seg.startaddress
                length = min(len(seg.data)-offset, len(contents))
                seg.data = seg.data[:offset] + contents[:length] + seg.data[offset+length:]
                contents = contents[length:]    # cut away what is used
                if not contents: return         # stop if done
                address += length
        raise ValueError("could not write all data")


    def merge(self, other):
        """\
        Merge an other Memory object into this one.

        :param other: A Memory instance, its contents is copied to this instance.
        """
        if self.segments:
            # not empty, smart merge
            new_segments = []
            segmentdata = []
            segment_address = 0
            last_address = 0
            for address, byte in stream_merge(DataStream(self), DataStream(other)):
                if address != last_address:
                    if segmentdata:
                        new_segments.append(Segment(segment_address, ''.join(segmentdata)))
                    last_address = address
                    segment_address = address
                    segmentdata = []
                segmentdata.append(byte)
                last_address += 1
            if segmentdata:
                new_segments.append(Segment(segment_address, ''.join(segmentdata)))
            self.segments = new_segments
        else:
            # empty: just take the new data
            for segment in other:
                self.segments.append(segment)


def load(filename, fileobj=None, format=None):
    """\
    Return a Memory object with the contents of a file.
    File type is determined from extension and/or inspection of content.

    :param filename: Name of the file to open
    :param fileobj: None to let this function open the file or an open, seekable file object
    :param format: File format name, ``None`` for auto detection.
    :return: Memory object
    """
    close = False
    if fileobj is None:
        fileobj = open(filename, "rb")
        close = True
    try:
        if format is None:
            # first check extension
            try:
                if filename[-4:].lower() == '.txt':
                    return titext.load(fileobj)
                elif filename[-6:].lower() == '.titxt' or filename[-7:].lower() == '.titext':
                    return titext.load(fileobj)
                elif filename[-4:].lower() in ('.a43', '.hex'):
                    return intelhex.load(fileobj)
            except error.FileFormatError:
                # do contents based detection below
                fileobj.seek(0)
            # then do a contents based detection
            try:
                return elf.load(fileobj)
            except elf.ELFException:
                fileobj.seek(0)
                try:
                    return titext.load(fileobj)
                except error.FileFormatError:
                    fileobj.seek(0)
                    try:
                        return titext.load(fileobj)
                    except error.FileFormatError:
                        raise error.FileFormatError(
                                'file %s could not be loaded (auto detection failed)' % (filename,))
        else:
            if format == 'titext':
                return titext.load(fileobj)
            elif format == 'ihex':
                return intelhex.load(fileobj)
            elif format == 'elf':
                return elf.load(fileobj)
            elif format == 'hex':
                return hexdump.load(fileobj)
            elif format == 'bin':
                return bin.load(fileobj)
            raise ValueError('unsupported file format %s' % (format,))
    finally:
        if close:
            fileobj.close()


def save(memory, fileobj, format='titext'):
    if format == 'titext':
        return titext.save(memory, fileobj)
    elif format == 'ihex':
        return intelhex.save(memory, fileobj)
    elif format == 'elf':
        return elf.save(memory, fileobj)
    elif format == 'bin':
        return bin.save(memory, fileobj)
    elif format == 'hex':
        return hexdump.save(memory, fileobj)
    raise ValueError('unsupported file format %s' % (format,))


load_formats = ['titext', 'ihex', 'bin', 'hex', 'elf']
save_formats = ['titext', 'ihex', 'bin', 'hex']
