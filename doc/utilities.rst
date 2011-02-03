===========
 Utilities
===========

Tools
=====
``msp430.memory.convert``
-------------------------

This is a command line tool that can load multiple hex files, combine them and
output a hex file of the same or different file type.
(run as ``python -m msp430.memory.convert``)

Usage: convert.py [options] [INPUT...]

Simple hex file conversion tool.

It is also possible to specify multiple input files and create a single,
merged output.

Options:
  -h, --help            show this help message and exit
  -o DESTINATION, --output=DESTINATION
                        write result to given file
  -i TYPE, --input-format=TYPE
                        input format name (titext, ihex, bin, hex, elf)
  -f TYPE, --output-format=TYPE
                        output format name (titext, ihex, bin, hex)
  -d, --debug           print debug messages


``msp430.memory.compare``
-------------------------
Compare two hex files. The files are loaded and a hex dump is compared. The
diff between the hex dumps is output (unless the ``--html`` option is used).
The tool also sets the shell exit code so that it could be used in shell/bat
scripts.

(run as ``python -m msp430.memory.compare``)

Usage: compare.py [options] FILE1 FILE2

Compare tool.

This tool reads binary, ELF or hex input files, creates a hex dump and shows
the differences between the files.


Options:
  -h, --help            show this help message and exit
  -o DESTINATION, --output=DESTINATION
                        write result to given file
  -d, --debug           print debug messages
  -v, --verbose         print more details
  -i TYPE, --input-format=TYPE
                        input format name (titext, ihex, bin, hex, elf)
  --html                create HTML output

``msp430.memory.generate``
--------------------------
Generate hex files filled with some pattern. The pattern can be a counter or
a useful MSP430 instruction such as ``JMP $`` (0x3fff).

(run as ``python -m msp430.memory.generate``)

Usage:     generate.py [options]

    Test File generator.

    This tool generates a hex file, of given size, ending on address
    0xffff if no start address is given.

Options:
  -h, --help            show this help message and exit
  -o DESTINATION, --output=DESTINATION
                        write result to given file
  -f TYPE, --output-format=TYPE
                        output format name (titext, ihex, bin, hex)
  -l SIZE, --length=SIZE
                        number of bytes to generate
  -s START_ADDRESS, --start-address=START_ADDRESS
                        start address of data generated
  -c, --count           use address as data
  --const=CONST         use given 16 bit number as data (default=0x3fff)
  --random              fill with random numbers


``msp430.memory.hexdump``
-------------------------
Show hex dump of files. Note that the same can be achieved with
``msp430.memory.convert -f hex``.

(run as ``python -m msp430.memory.hexdump``)

Usage: hexdump.py [options] [SOURCE...]

Hexdump tool.

This tool generates hex dumps from binary, ELF or hex input files.

What is dumped?
- Intel hex and TI-Text: only data
- ELF: only segments that are programmed
- binary: complete file, address column is byte offset in file

Options:
  -h, --help            show this help message and exit
  -o DESTINATION, --output=DESTINATION
                        write result to given file
  --debug               print debug messages
  -v, --verbose         print more details
  -i TYPE, --input-format=TYPE
                        input format name (titext, ihex, bin, hex, elf)

File format handlers
====================

Overview
--------
The file format handler modules each provides a load and/or save function on
module level.

.. function:: load(filelike)

    :param filelike: A file like object that is used to write the data.
    :return: :class:`msp430.memory.Memory` instance with the contents loaded from the fike like object.

    Read from a file like object and fill in the contents to a memory object.
    The file like should typically be a file opened for reading in binary
    mode.

.. function:: save(memory, filelike)

    :param memory: :class:`msp430.memory.Memory` instance with the contents loaded from the fike like object.
    :param filelike: A file like object that is used to write the data.

    Write the contents of the memory object to the given file like object. This
    should typically be a file opened for writing in binary mode.

Handlers
--------
``msp430.memory.bin``

    .. module:: msp430.memory.bin

    Load and save binary data. Note that this is not practical for MSP430 binaries
    as they usually are not one block and do not start at address null. The binary
    format can not keep track of addresses.

``msp430.memory.elf``

    ELF object file reader (typical file extension ``.elf``). There is
    currently no support for writing this type.

``msp430.memory.hexdump``

    Read and write hex dumps.

``msp430.memory.titext``

    Read and write TI-text format files (often named ``.txt``).

``msp430.memory.intelhex``

    Read and write Intel-HEX format files (often named ``.a43``).

API
===

``msp430.memory``
-----------------
.. module:: msp430.memory

.. class:: DataStream(object)

    An iterator for addressed bytes. It yields all the bytes of a
    :class:`Memory` instance in ascending order. It allows peeking at the
    current position by reading the :attr:`address` attribute. ``None`` signals
    that there are no more bytes (and :meth:`next()` would raise
    :exc:`StopIteration`).

    .. method:: __init__(self, memory)

        Initialize the iterator. The data from the given memory instance is
        streamed.

    .. method:: next()

        Gets next tuple (address, byte) from the iterator.

    .. attribute:: address

        The address of the byte that will be returned by :meth:`next()`.


.. function:: stream_merge(\*streams)

    :param streams: Any number of :class:`DataStream` instances.

    Merge multiple streams of addressed bytes. If data is overlapping, take
    it from the later stream in the list.


.. class:: Segment(object)

    Store a string or list with memory contents (bytes) along with its start
    address.

    .. method:: __init__(startaddress = 0, data=None)

        :param startaddress: Address of 1st byte in data.
        :param data: Byte string.

        Initialize a new segment that starts at given address, containing the
        given data.

    .. method:: __getitem__(index)

        :param index: Index of byte to get.
        :return: A byte string with one byte.
        :raises IndexError: offset > length of data

        Read a byte from the segment. The offset is 0 for the 1st byte in the
        block.

    .. method:: __len__()

        Return the number of bytes in the segment.

    .. method:: __cmp__(other)

        Compare two segments. Implemented to support sorting a list of segments
        by address.

.. class:: Memory(object)

    Represent memory contents.

    .. method:: __init__()

        Initialize an empty memory object.

    .. method:: append(segment)

        :param segment: A :class:`Segment` instance.

        Append a segment to the internal list. Note that there is no check for
        overlapping data.

    .. method:: __getitem__(index)

        :return: :class:`Segment` instance
        :raises IndexError: index > number of segments

        Get a segment from the internal list.

    .. method:: __len__()

        :return: Number of segments in the internal list.


    .. method:: get_range(fromadr, toadr, fill='\xff')

        :param fromadr: Start address (including).
        :param toadr: End address (including).
        :param fill: Fill value (a byte).
        :return: A byte string covering the given memory range.

        Get a range of bytes from the memory. Unavailable values are filled
        with ``fill`` (default 0xff).

    .. method:: get(address, size)

        :param address: Start address of block to read.
        :param size: Size of the of block to read.
        :return: A byte string covering the given memory range.
        :exception ValueError: unavailable addresses are tried to read.

        Get a range of bytes from the memory.

     .. method:: set(address, contents)

        :param address: Start address of block to read.
        :param contents: Bytes to write to the memory.
        :exception ValueError: Writing to an undefined memory location.

        Write a range of bytes to the memory. A segment covering the address
        range to be written has to be existent. A :exc:`ValueError` is raised
        if not all data could be written (attention: a part of the data may
        have been written!). The contents may span multiple (existing)
        segments.

    .. method:: merge(other)

        :param other: A Memory instance, its contents is copied to this instance.

        Merge an other memory object into this one. The data is merged: in case
        of overlapping, the data from ``other`` is used. The segments are
        recreated so that consecutive blocks of bytes are each in one segment.


.. function:: load(filename, fileobj=None, format=None)

    :param filename: Name of the file to open
    :param fileobj: None to let this function open the file or an open, seekable file object (typically opened in binary mode).
    :param format: File format name, ``None`` for auto detection.
    :return: Memory object.

    Return a Memory object with the contents of a file.
    File type is determined from extension and/or inspection of content.


.. function:: save(memory, fileobj, format='titext')

    :param fileobj: A writeable file like object (typically opened in binary mode).
    :param format: File format name.

    Save given memory object to file like object.


``msp430.listing``
-----------------
.. module:: msp430.listing

This module provides parser for listing/map files of the IAR and mspgcc C
compilers. This can be used in tools that need to know the addresses of
variables or functions. E.g. to create a checksum patch application.

Sub-modules:

- ``msp430.listing.iar``
- ``msp430.listing.mspgcc``

Each module provides such a function:

.. function:: label_address_map(filename)

    :param filename: Name of a listing or map file.
    :return: A dictionary mapping labels (key) to addresses (values/int).

