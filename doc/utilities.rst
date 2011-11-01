===========
 Utilities
===========

``msp430.memory.convert``
=========================

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
=========================
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
==========================
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
=========================
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

