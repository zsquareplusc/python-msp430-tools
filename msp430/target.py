#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2002-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
This module defines a default target that represents a MSP430 device. It
defines some common operations and the basics of a command line frontend using
these functions. Separate implementations, using subclassing, then provide JTAG
or BSL connectivity.

Common operations that will work with all connection types are:
- segment erase
- erase infomem - reads device type 1st
- mass erase
- main erase
- download file
- verify by file
- erase check by file
- upload
- upload by file
"""

import sys
import time
import logging
import struct
from msp430 import memory

from optparse import OptionParser, OptionGroup, IndentedHelpFormatter

# MCU types
# use strings as ID so that they can be used in outputs too
F1x = "F1x family"
F2x = "F2x family"
F4x = "F4x family"

# known device list
DEVICEIDS = {
#    CPUID   BSLVER family
    (0x1132, None): F1x,      # F1122, F1132
    (0x1232, None): F1x,      # F1222, F1232
    (0xf112, None): F1x,      # F11x, F11x1, F11x1A
    (0xf123, 0x0140): F1x,    # F21x1
    (0xf123, None): F1x,      # F122, F123X
    (0xf143, None): F1x,      # F14x
    (0xf149, None): F1x,      # F13x, F14x(1)
    (0xf169, None): F1x,      # F16x
    (0xf16c, None): F1x,      # F161x
    (0xf227, None): F2x,      # F22xx
    (0xf26f, None): F2x,
    (0xf413, None): F4x,
    (0xf427, None): F4x,      # FE42x, FW42x, F41(5,7), F42x0
    (0xf439, None): F4x,      # FG43x
    (0xf449, None): F4x,      # F43x, F44x
    (0xf46f, None): F4x,      # FG46xx
}

def identify_device(device_id, bsl_version):
    try:
        try:
            return DEVICEIDS[device_id, bsl_version]
        except KeyError:
            return DEVICEIDS[device_id, None]
    except KeyError:
        if device_id >> 8 == 0x1f: return F1x
        if device_id >> 8 == 0x2f: return F2x
        if device_id >> 8 == 0x4f: return F4x
        raise KeyError('device type not known %04x/%04x' % (device_id, bsl_version))


class UnsupportedMCUFamily(Exception):
    """This exception is raised when the CPU family is not compatible"""

# i don't like how texts are re-wrapped and paragraphs are joined. get rid
# of that "bug"
class Formatter(IndentedHelpFormatter):
    def _format_text(self, text):
        paragraphs = text.split('\n\n')
        return '\n\n'.join(IndentedHelpFormatter._format_text(self, p) for p in paragraphs)


def parseAddressRange(text):
    """parse a single address or an address range and return a tuple."""
    if '-' in text:
        adr1, adr2 = text.split('-', 1)
        try:
            adr1 = int(adr1, 0)
        except ValueError:
            raise ValueError("Address range start address must be a valid number in dec, hex or octal")
        try:
            adr2 = int(adr2, 0)
        except ValueError:
            raise ValueError("Address range end address must be a valid number in dec, hex or octal")
        return (adr1, adr2)
    elif '/' in text:
        adr1, size = text.split('/', 1)
        try:
            adr1 = int(adr1, 0)
        except ValueError:
            raise ValueError("Address range start address must be a valid number in dec, hex or octal")
        multiplier = 1
        if size.endswith('k'):
            size = size[:-1]
            multiplier = 1024
        try:
            size = int(size, 0) * multiplier
        except ValueError:
            raise ValueError("Address range size must be a valid number in dec, hex or octal")
        return (adr1, adr1 + size - 1)
    else:
        try:
            adr = int(text, 0)
            return (adr, None)
        except ValueError:
            raise ValueError("Address must be a valid number in dec, hex or octal or a range adr1-adr2")


class Target(object):
    """Abstract target class, defining a minimal set of methods."""

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # the following methods need to be implemented in a subclass
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def memory_read(self, address, length):
        """Read from memory."""
        raise NotImplementedError("Memory read functionality not supported")

    def memory_write(self, address, data):
        """Write to memory."""
        raise NotImplementedError("Memory write functionality not supported")

    def mass_erase(self):
        """Clear all Flash memory."""
        raise NotImplementedError("Mass erase functionality not supported")

    def main_erase(self):
        """Clear main Flash memory (excl. infomem)."""
        raise NotImplementedError("Main erase functionality not supported")

    def erase(self, address):
        """Erase Flash segment containing the given address."""
        raise NotImplementedError("Segment erase functionality not supported")

    def execute(self, address):
        """Start executing code on the target."""
        raise NotImplementedError("Execute functionality not supported")

    def version(self):
        """The 16 bytes of the ROM that contain chip and BSL info are returned."""
        raise NotImplementedError("Reading version not supported")

    def reset(self):
        """Reset the device."""
        raise NotImplementedError("Reset functionality not supported")

    def add_extra_options(self):
        """The user class can add items to self.parser"""
    def parse_extra_options(self):
        """The user class can process self.options it added"""
    def open_connection(self):
        """Open the connection"""
    def close_connection(self):
        """Close the connection"""

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # supporting functions
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self):
        self.upload_data = None
        self.action_list = []
        self.verbose = 0
        self.debug = False
        self.debug = True   # XXX


    def flash_segment_size(self, address):
        """Determine the Flash segment size"""
        # XXX make it device family aware
        if address < 0x1000:
            modulo = 64
        elif address < 0x1100:
            modulo = 256
        else:
            modulo = 512
        return modulo

    def get_mcu_family(self):
        device_id, bsl_version = struct.unpack(">H8xH4x", self.version())
        family = identify_device(device_id, bsl_version)
        if self.verbose > 2:
            sys.stderr.write("MCU: %s (%04x)\n" % (family, device_id))
        return family

    def erase_infomem(self):
        if self.verbose > 2:
            sys.stderr.write("Erase infomem: check MCU type\n")
        mcu_family = self.get_mcu_family()
        if mcu_family == F1x:
            if self.verbose > 1:
                sys.stderr.write("Erase infomem: F1xx 0x1000, 2*128B\n")
            self.erase(0x1000)
            self.erase(0x1080)
        elif mcu_family == F2x:
            if self.verbose > 1:
                sys.stderr.write("Erase infomem: F2xx 0x1000, 4*64B\n")
            self.erase(0x1000)
            self.erase(0x1040)
            self.erase(0x1080)
            self.erase(0x10c0)
        elif mcu_family == F4x:
            if self.verbose > 1:
                sys.stderr.write("Erase infomem: F4xx 0x1000, 2*128B\n")
            self.erase(0x1000)
            self.erase(0x1080)
        else:
            raise UnsupportedMCUFamily('%02x not supported' % mcu_family)
        if self.verbose:
            sys.stderr.write('Erase infomem: done\n')

    def upload(self, start, end):
        """upload given memory range and store it in upload_data"""
        size = 1 + end - start
        if self.verbose > 1:
            sys.stderr.write("Upload 0x%04x %d bytes\n" % (start, size))
        self.upload_data.append(memory.Segment(start, self.memory_read(start, size)))

    def upload_by_file(self):
        """upload memory areas also contained in self.download_data"""
        for segment in self.download_data:
            if self.verbose > 1:
                sys.stderr.write("Upload 0x%04x %d bytes\n" % (segment.startaddress, len(segment.data)))
            data = self.memory_read(segment.startaddress, len(segment.data))
            self.upload_data.append(memory.Segment(segment.startaddress, data))
        if self.verbose:
            sys.stderr.write('Upload by file: done\n')

    def program_file(self, download_data=None, quiet=False):
        """\
        download data from self.download_data or the optional parameter.
        status messages on stderr are printed unless the quiet parameter is
        true (this can e.g. used to download helper code)
        """
        if self.verbose and not quiet:
            sys.stderr.write('Programming...\n')
        if download_data is None:
            download_data = self.download_data
        for segment in download_data:
            if self.verbose > 1 and not quiet:
                sys.stderr.write("Write segment at 0x%04x %d bytes\n" % (segment.startaddress, len(segment.data)))
            data = segment.data
            # pad length if odd number of bytes
            if len(data) & 1:
                data += '\xff'
            self.memory_write(segment.startaddress, data)
        if self.verbose and not quiet:
            sys.stderr.write('Programming: OK\n')

    def verify_by_file(self):
        """upload and compare to self.download_data"""
        if self.verbose:
            sys.stderr.write('Verify by file...\n')
        for segment in self.download_data:
            if self.verbose > 1:
                sys.stderr.write("Verify segment at 0x%04x %d bytes\n" % (segment.startaddress, len(segment.data)))
            data = self.memory_read(segment.startaddress, len(segment.data))
            if data != segment.data:
                raise Exception("verify failed at 0x%04x" % (segment.startaddress,))
            # XXX show hex DIFF
        if self.verbose:
            sys.stderr.write('Verify by file: OK\n')

    def erase_check_by_file(self):
        """upload address ranges used in self.download_data and check if memory erased (0xff)"""
        if self.verbose:
            sys.stderr.write('Erase check by file...\n')
        for segment in self.download_data:
            if self.verbose > 1:
                sys.stderr.write("Erase check segment at 0x%04x %d bytes\n" % (segment.startaddress, len(segment.data)))
            data = self.memory_read(segment.startaddress, len(segment.data))
            if data != '\xff'*len(segment.data):
                raise Exception("erase check failed at 0x%04x" % (segment.startaddress,))
            # XXX show hex DIFF
        if self.verbose:
            sys.stderr.write('Erase check by file: OK\n')

    def erase_by_file(self):
        """\
        Erase Flash segments that will be used by the data in self.download_data.
        """
        if self.verbose:
            sys.stderr.write('Erase by file...\n')
        for segment in self.download_data:
            address = segment.startaddress
            # mask address to get to segment start
            address -= address % self.flash_segment_size(address)
            end_address = segment.startaddress + len(segment.data) - 1
            if self.verbose > 1:
                sys.stderr.write("Erase segments at 0x%04x-0x%04x\n" % (address, end_address))
            while address <= end_address:
                self.erase(address)
                address += self.flash_segment_size(address)
        if self.verbose:
            sys.stderr.write('Erase by file: OK\n')


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # command line interface implementation
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def create_option_parser(self):
        """create OptionParser with default options"""
        self.parser = OptionParser(usage="%prog [OPTIONS] [FILE [FILE...]]", formatter=Formatter())

        self.parser.add_option("--debug",
                help="print debug messages and tracebacks (development mode)",
                dest="debug",
                default=False,
                action='store_true')

        self.parser.add_option("-v", "--verbose",
                help="show more messages (can be given multiple times)",
                dest="verbose",
                default=1,
                action='count')

        self.parser.add_option("-q", "--quiet",
                help="suppress all messages",
                dest="verbose",
                action='store_const',
                const=0)

        self.parser.add_option("--time",
                help="measure time",
                dest="time",
                action="store_true",
                default=False)

        self.parser.add_option("-S", "--progress",
                dest="progress",
                help="show progress while programming",
                default=False,
                action='store_true')

        group = OptionGroup(self.parser, "Data input", """\
File format is auto detected, unless --input-format is used.
Preferred file extensions are ".txt" for TI-Text format, ".a43" or ".hex" for
Intel HEX. ELF files can also be loaded.

Multiple files can be given on the command line, all are merged before the
download starts. "-" reads from stdin.
    """)

        group.add_option("-i", "--input-format",
                dest="input_format",
                help="input format name (%s)" % (', '.join(memory.load_formats),),
                default=None,
                metavar="TYPE")

        self.parser.add_option_group(group)


        group = OptionGroup(self.parser, "Flash erase", """\
Multiple --erase options are allowed. It is also possible to use address
ranges such as 0xf000-0xf0ff or 0xf000/4k.

NOTE: SegmentA on F2xx is NOT erased with --mass-erase, that must be
done separately with --erase=0x10c0 or --info-erase".
""")
        group.add_option("-e", "--mass-erase",
                dest="do_mass_erase",
                help="mass erase (clear all flash memory)",
                default=False,
                action='store_true')

        group.add_option("-m", "--main-erase",
                dest="do_main_erase",
                help="erase main flash memory only",
                default=False,
                action='store_true')

        group.add_option("--info-erase",
                dest="do_info_erase",
                help="erase info flash memory only (0x1000-0x10ff)",
                default=False,
                action='store_true')

        group.add_option("-b", "--erase-by-file",
                dest="do_erase_by_file",
                help="erase only Flash segments where new data is downloaded",
                default=False,
                action='store_true')

        group.add_option("--erase",
                dest="erase_list",
                help="selectively erase segment at the specified address or address range",
                default=[],
                action='append',
                metavar="ADDRESS")

        self.parser.add_option_group(group)

        group = OptionGroup(self.parser, "Program flow specifiers", """\
All these options work against the file(s) provided on the command line.
Program flow specifiers default to "-P" if a file is given.

"-P" usually verifies the programmed data, "-V" adds an additional
verification through uploading the written data for a 1:1 compare.

No default action is taken if "-P", "-V" or "-E" is given, say specifying
only "-V" does a "check by file" of a programmed device without programming.

Don't forget to erase ("-e", "-b" or "-m") before programming flash!
""")
        group.add_option("-E", "--erase-check",
                dest="do_erase_check",
                help="erase check by file",
                default=False,
                action='store_true')

        group.add_option("-P", "--program",
                dest="do_program",
                help="program file",
                default=False,
                action='store_true')

        group.add_option("-V", "--verify",
                dest="do_verify",
                help="verify by file",
                default=False,
                action='store_true')

        group.add_option("-U", "--upload-by-file",
                dest="do_upload_by_file",
                help="upload the memory that is present in the given file(s)",
                default=False,
                action='store_true')

        self.parser.add_option_group(group)


        group = OptionGroup(self.parser, "Data upload", """\
This can be used to read out the device memory.
It is possible to use address ranges such as 0xf000-0xf0ff or 0xf000/256, 0xfc00/1k.

Multiple --upload options are allowed.
""")

        group.add_option("-u", "--upload",
                dest="upload_list",
                metavar="ADDRESS",
                help='upload a data block, can be passed multiple times',
                default=[],
                action='append')

        group.add_option("-o", "--output",
                dest="output",
                help="write uploaded data to given file",
                metavar="DESTINATION")

        group.add_option("-f", "--output-format",
                dest="output_format",
                help="output format name (%s), default:%%default" % (', '.join(memory.save_formats),),
                default="hex",
                metavar="TYPE")

        self.parser.add_option_group(group)

        group = OptionGroup(self.parser, "Do before exit")

        group.add_option("-x", "--execute",
                dest="do_run",
                metavar="ADDRESS",
                type="int",
                help='start program execution at specified address, might only be useful in conjunction with --wait',
                default=None,
                action='store')

        group.add_option("-r", "--reset",
                dest="do_reset",
                help="perform a normal device reset that will start the program that is specified in the reset interrupt vector",
                default=False,
                action='store_true')

        group.add_option("-w", "--wait",
                dest="do_wait",
                help="wait for <ENTER> before closing the port",
                default=False,
                action='store_true')

        group.add_option("--no-close",
                dest="no_close",
                help="do not close port on exit",
                default=False,
                action='store_true')

        self.parser.add_option_group(group)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def add_action(self, function, *args, **kwargs):
        """Store a function to be called and parameters in the list of actions"""
        self.action_list.append((function, args, kwargs))


    def remove_action(self, function):
        """Remove a function from the list of actions"""
        for entry in self.action_list:
            if entry[0] == function:
                self.action_list.remove(entry)
                break
        else:
            raise IndexError('not found in action list')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def parse_args(self):
        (self.options, self.args) = None, []  # parse_args may terminate...
        (self.options, self.args) = self.parser.parse_args()

        self.debug = self.options.debug
        self.verbose = self.options.verbose

        if self.verbose > 3 :
            level = logging.DEBUG
        elif self.verbose > 2:
            level = logging.INFO
        else:
            level = logging.WARN
        logging.basicConfig(level=level)

        if self.verbose > 1:   # debug infos
            sys.stderr.write("Debug is %s\n" % self.options.debug)
            sys.stderr.write("Verbosity level set to %d\n" % self.options.verbose)
            #~ sys.stderr.write("logging module level set to %s\n" % (level,))
            sys.stderr.write("Python version: %s\n" % sys.version)

        if self.options.input_format is not None and self.options.input_format not in memory.load_formats:
            self.parser.error('Input format %s not supported.' % (self.options.input_format))

        if self.options.output_format not in memory.save_formats:
            self.parser.error('Output format %s not supported.' % (self.options.output_format))

        # sanity check of options
        if self.options.do_run is not None and self.options.do_reset:
            if self.verbose:
                sys.stderr.write("Warning: option --reset ignored as --go is specified!\n")
            self.options.do_reset = False

        if self.options.upload_list and self.options.do_reset:
            if self.verbose:
                sys.stderr.write("Warning: option --reset ignored as --upload is specified!\n")
            self.options.do_reset = False

        if self.options.upload_list and self.options.do_wait:
            if self.verbose:
                sys.stderr.write("Warning: option --wait ignored as --upload is specified!\n")
            self.options.do_wait = False

        # create a list of functions an arguments
        if self.options.do_mass_erase:
            self.add_action(self.mass_erase)
        if self.options.do_main_erase:
            self.add_action(self.main_erase)
        if self.options.do_erase_by_file:
            self.add_action(self.erase_by_file)
        if self.options.do_info_erase:
            self.add_action(self.erase_infomem)
        for a in self.options.erase_list:
            try:
                adr, adr2 = parseAddressRange(a)
                if adr2 is not None:
                    while adr <= adr2:
                        if not (0x1000 <= adr <= 0xffff):
                            self.parser.error("Start address for --erase is not within Flash memory: 0x%04x" % (adr,))
                        elif adr < 0x1100:
                            modulo = 64     # F2xx XXX: on F1xx/F4xx are segments erased twice
                        elif adr < 0x1200:
                            modulo = 256
                        else:
                            modulo = 512
                        adr = adr - (adr % modulo)
                        self.add_action(self.erase, adr)
                        adr = adr + modulo
                else:
                    self.add_action(self.erase, adr)
            except ValueError, e:
                self.parser.error("--erase: %s" % e)

        default_action = True
        if self.options.do_erase_check:
            self.add_action(self.erase_check_by_file)
            default_action = False
        if self.options.do_program:
            self.add_action(self.program_file)
            default_action = False
        if self.options.do_verify:
            self.add_action(self.verify_by_file)
            default_action = False
        if self.options.do_upload_by_file:
            self.add_action(self.upload_by_file)
            default_action = False


        # as default action (no other given by user), program if a file is given
        if default_action and self.args:
            self.add_action(self.program_file)

        for a in self.options.upload_list:
            try:
                start, end = parseAddressRange(a)
                if end is None:
                    end = start + 15
                self.add_action(self.upload, start, end)
            except ValueError, e:
                self.parser.error("--upload: %s" % e)

        if self.options.do_reset:
            self.add_action(self.reset)

        if self.options.upload_list or self.options.do_upload_by_file:
            self.upload_data = memory.Memory()

        if self.options.do_run:
            self.add_action(self.execute, self.options.do_run)
        else:
            # XXX reset otherwise, independently of -r option. imitate old behavior
            self.add_action(self.reset)

        # prepare output
        if self.options.output is None:
            self.output = sys.stdout
            if sys.platform == "win32":
                # ensure that the console is in binary mode
                import os, msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        else:
            self.output = open(self.options.output, 'wb')

        # prepare data to download / load files
        self.download_data = memory.Memory()                  # prepare downloaded data
        for filename in self.args:
            if filename == '-':
                data = memory.load(
                        '<stdin>',
                        sys.stdin,
                        format=self.options.input_format or "titext")
            else:
                data = memory.load(
                        filename,
                        format=self.options.input_format)
            self.download_data.merge(data)


    def do_the_work(self):
        """\
        Do the actual work, such as upload and download.
        """
        # debug messages
        if self.verbose > 1:
            # show a nice list of scheduled actions
            sys.stderr.write("action list:\n")
            for f, args, kwargs in self.action_list:
                params = ','.join([repr(x) for x in args] + ['%s=%r' % x for x in kwargs.items()])
                try:
                    sys.stderr.write("   %s(%s)\n" % (f.func_name, params))
                except AttributeError:
                    sys.stderr.write("   %r (%s)\n" % (f, params))
            if not self.action_list:
                sys.stderr.write("   <no actions>\n")
            sys.stderr.flush()

        self.open_connection()
        # work through action list
        for f, args, kwargs in self.action_list:
            f(*args, **kwargs)

        # output uploaded data
        if self.upload_data is not None:
            memory.save(self.upload_data, self.output, self.options.output_format)

        if self.options.do_wait:                        # wait at the end if desired
            if self.verbose:
                sys.stderr.write("Press <ENTER> ...\n") # display a prompt
                sys.stderr.flush()
            raw_input()                                 # wait for newline


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def main(self):
        """Main command line entry"""
        start_time = None
        abort_due_to_error = False
        try:
            self.create_option_parser()
            self.add_extra_options()
            self.parse_args()
            abort_due_to_error = True
            self.parse_extra_options()
            if self.options.time:
                start_time = time.time()
            self.do_the_work()
            abort_due_to_error = False
        except SystemExit:
            abort_due_to_error = False                      # lets assume they are not becuase of an internal error
            raise                                           # let pass exit() calls
        except KeyboardInterrupt:
            if self.debug: raise                            # show full trace in debug mode
            sys.stderr.write("\nAbort on user request.\n")  # short message in user mode
            sys.exit(1)                                     # set error level for script usage
        except Exception, msg:                              # every Exception is caught and displayed
            if self.debug: raise                            # show full trace in debug mode
            sys.stderr.write("\nAn error occurred:\n%s\n" % msg) # short message in user mode
            sys.exit(1)                                     # set error level for script usage
        finally:
            if abort_due_to_error:
                sys.stderr.write("Cleaning up after error...\n")
            if self.options is not None and not self.options.no_close:
                try:
                    self.close_connection()                     # release communication port
                except Exception, msg:                              # every Exception is caught and displayed
                    if self.debug: raise                            # show full trace in debug mode
                    sys.stderr.write("\nAn error occurred during shutdown:\n%s\n" % msg) # short message in user mode
            elif self.verbose:
                sys.stderr.write("WARNING: port is left open (--no-close)\n")
            if start_time is not None:
                end_time = time.time()
                sys.stderr.write("Time: %.1f s\n" % (end_time - start_time))


# ----- test code only below this line -----
if __name__ == '__main__':
    t = Target()
    t.main()

