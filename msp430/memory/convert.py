#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2004-2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""\
Simple converter for hex files.

data can be read from stdin and output on stdout:
usage: cat file.txt | convert - >out.a43
usage: convert file.txt >out.a43
usage: convert file.txt -o out.a43
"""


def main():
    import msp430.commandline_helper

    class ConvertTool(msp430.commandline_helper.CommandLineTool):
        description = """\
Simple hex file conversion tool.

It is also possible to specify multiple input files and create a single,
merged output.
"""

        def configure_parser(self):
            self.parser_add_input(nargs='*')
            self.parser_add_output()

        def run(self, args):
            if not args.SRC:
                # if no files are given, read from stdin
                args.FILE = [msp430.commandline_helper.BinaryFileType('r')('-')]
                # default to TI-Text if no format is given
                if args.input_format is None:
                    args.input_format = 'titext'

            # get input
            data = msp430.memory.Memory()
            for fileobj in args.SRC:
                data.merge(msp430.memory.load(fileobj.name, fileobj, args.input_format))

            # write ihex file
            msp430.memory.save(data, args.output, args.output_format)

    ConvertTool().main()

if __name__ == '__main__':
    main()
