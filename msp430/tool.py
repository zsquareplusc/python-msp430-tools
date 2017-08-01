#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# command line stub
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2011-2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause

import sys

COMMANDS = {
    'jtag': 'msp430.jtag.target',
    'dco': 'msp430.jtag.dco',
    'gdb': 'msp430.gdb.target',
    'bsl': 'msp430.bsl.target',
    'bsl5.uart': 'msp430.bsl5.uart',
    'bsl5.hid': 'msp430.bsl5.hid',
    'hexdump': 'msp430.memory.hexdump',
    'compare': 'msp430.memory.compare',
    'convert': 'msp430.memory.convert',
    'generate': 'msp430.memory.generate',
    'cmd': 'msp430.shell.command',
    'watch': 'msp430.shell.watch',
    'as': 'msp430.asm.as',
    'ld': 'msp430.asm.ld',
    'cpp': 'msp430.asm.cpp',
    'dis': 'msp430.asm.disassemble',
}


def usage_error():
    sys.stderr.write(
        'Command line stub for python-msp430-tools\n'
        'USAGE: {prog} COMMAND [args]\n'
        'Supported COMMANDs are:\n'
        '{tools}'
        '\n'.format(
            prog=sys.argv[0],
            tools='\n'.join('- {}'.format(x) for x in sorted(COMMANDS.keys()))))
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        usage_error()
    else:
        command = sys.argv.pop(1)
        # patch argv so that help texts are correct
        sys.argv[0] = '{} {}'.format(sys.argv[0], command)
        try:
            module_name = COMMANDS[command]
        except KeyError:
            # unsupported command
            usage_error()
        else:
            __import__(module_name)
            module = sys.modules[module_name]
            #~ sys.stderr.write('running main() from %r\n' % module)
            module.main()

if __name__ == '__main__':
    main()
