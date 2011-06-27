#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
X-Protocol command class for serial devices.

The X-Protocol simple:
- line based
  - line ends with '\n', '\r' shall be ignored
- master/slave. PC always initiates communication
- a command can have many lines as response
- the first character of the line serves as command or response indicator
- 'xOK' or 'xERR <optional message>' indicate the end of a command

This implementation provides a class that connects through the serial port.
Commands can be sent with the method ``command``. It returns all lines output
by the device as list when it was 'xOK' (result is excluding this). In case of
an 'xERR' response, an exception is raised containing the message from the
device. All lines read until the error occurred are attached to the exception.

Typical usages for commands:
- 'd' set debug mode: 'd0' / 'd1'
- 'e' set echo mode: 'e0' / 'e1'

Typical usages for answers:
- 'i' for integer. e.g. 'i123' or 'i0x123'
- 's' for a string. e.g. 'sHello'
- 'o' for output message. The message is intended to be shown to the user,
   e.g. 'oHello World'

Example::

        PC              Device                  Note
      ======            ======                  ====
      oHello --------->                         a command that
             <--------- oHello                  sends the message back
             <--------- xOK

      m1     --------->                         a command that does some measurement
             <--------- i123                    and returns an integer
             <--------- xOK

      r      --------->                         an invalid command
             <--------- xERR unknown command    yields an error
"""

import serial
import codecs

class XProtocolError(Exception):
    pass

class XProtocol(object):
    def __init__(self, port, baudrate=2400):
        self.serial = serial.Serial()
        self.serial.port = port
        self.serial.baudrate = baudrate
        self.serial.timeout = 3

    def open(self):
        self.serial.open()

    def close(self):
        self.serial.close()

    def command(self, cmd):
        self.serial.write('%s\n' % cmd)
        lines = []
        chars = []
        while True:
            c = self.serial.read(1)
            if not c: raise XProtocolError('Timeout', lines)
            if c == '\r':
                pass
            elif c == '\n':
                line = ''.join(chars)
                del chars[:]
                if not line:
                    pass
                elif line[0] == 'x':
                    if line.startswith('xOK'):
                        return lines
                    else:
                        raise XProtocolError(''.join(line), lines)
                else:
                    lines.append(line)
            else:
                chars.append(c)

    def decode(self, lines):
        result = []
        for line in lines:
            if not line:
                pass
            elif line[0] == 'i':
                result.append(int(line[1:], 0))
            elif line[0] == 'h':
                result.append(line[1:].decode('hex'))
            elif line[0] == 's':
                result.append(codecs.escape_decode(line[1:])[0])
            elif line[0] == 'o':
                sys.stdout.write(line[1:])
            else:
                raise ValueError('unknown line type: %r' % (line,))
        return result


if __name__ == '__main__':
    import sys
    import time
    import unittest
    x = XProtocol('/dev/ttyACM0', 2400)
    #~ x = XProtocol('/dev/ttyACM0', 9600)
    x.open()

    class TestDecoder(unittest.TestCase):
        def test_int(self):
            self.failUnlessEqual(x.decode(['i123']), [123])
            self.failUnlessEqual(x.decode(['i0x123']), [0x123])
            self.failUnlessEqual(x.decode(['i1', 'i2', 'i3']), [1,2,3])
        def test_str(self):
            self.failUnlessEqual(x.decode(['sHello']), ['Hello'])
            self.failUnlessEqual(x.decode(['s\\n']), ['\n'])
        def test_unknown(self):
            self.failUnlessRaises(ValueError, x.decode, ['r'])

    class TestCommands(unittest.TestCase):
        def test_echo(self):
            self.failUnlessEqual(x.command('oHello'), ['oHello'])
        def test_error(self):
            self.failUnlessRaises(XProtocolError, x.command, 'error')
        def test_load(self):
            test_duration = 5.0  # [seconds]
            t_end = time.time() + test_duration
            n = 0
            while time.time() < t_end:
                self.failUnlessEqual(x.command('oHello'), ['oHello'])
                n += 1
            print '\n~%d echo commands/second' % (n/test_duration)

    sys.argv[1:] = ['-v']
    unittest.main()
    #~ x.close()
