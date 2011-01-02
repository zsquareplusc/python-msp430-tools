import titext
import elf
import intelhex
import bin
import hexdump
import error

class Segment:
    """store a string with memory contents along with its startaddress"""
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

class Memory:
    """represent memory contents. with functions to load files"""
    def __init__(self, filename=None):
        self.segments = []
        if filename:
            load(self, filename)

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
                #segment contains data in the address range
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
        written!). The contains may span multiple (existing) segments.

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
        for segment in other:
            # XXX currently no support for overlapping data
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
                                'file %s could not be loaded (not ELF, Intel-Hex, or TI-Text)' % (filename,))
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
