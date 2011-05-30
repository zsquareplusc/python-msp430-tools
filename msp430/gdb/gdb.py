#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2002-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Interface to GDB server suing a TCP/IP connection.

It can be used to talk to e.g. msp430-gdbproxy or mspdebug.
"""

from struct import pack, unpack
import socket
import threading
import Queue

class GDBException(Exception):
    """Generic protocol errors"""

class GDBRemoteTimeout(GDBException):
    """If target does not answer"""

class GDBRemoteTooManyFailures(GDBException):
    """If target does not answer"""

class GDBUnknownCommandError(GDBException):
    """If target does not know this command"""

class GDBRemoteError(GDBException):
    """Target answered with 'E' (error) packet"""
    def __init__(self, errorcode, message):
        GDBException.__init__(self, message)
        self.errorcode = errorcode

    def getErrorCode(self):
        return self.errorcode



HEXDIGITS = '0123456789abcdefABCDEF'
IDLE, DATA, CRC1, CRC2 = ' ', '$', '1', '2'
WAITING, SUCCESS, FAILURE = 0, 1, 2

# breakpoint/watchpoint types:
BRK_SOFTWARE            = 0
BRK_HARDWARE            = 1
BRK_WRITEWATCH          = 2
BRK_READWATCH           = 3
BRK_ACCESSWATCH         = 4

STOP_SIGNAL = 'signal'
STOP_THREAD = 'thread'
STOP_EXITED = 'exited'


class ClientSocketConnector(threading.Thread):
    """\
    Make a connection through a TCP/IP socket. This version connects to a
    server (i.e. is a client).
    """

    def __init__(self, host_port):
        """
        The host/port tuple from the parameter is used to open a TCP/IP
        connection. It is passed to socket.connect().
        """
        threading.Thread.__init__(self)
        self.setDaemon(True)   # we don't want to block on exit
        self._alive = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(host_port)
        self.socket.settimeout(5)
        self.start()

    def write(self, text):
        """Just send everything"""
        self.socket.sendall(text)

    def close(self):
        """Close connection."""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self._alive = False

    def run(self):
        """\
        Implement an efficient read loop for sockets.
        """
        while self._alive:
            try:
                text = self.socket.recv(1024)
            except socket.timeout:
                pass
            except socket.error:
                break   # socket error -> terminate
            else:
                if not text: break  # EOF -> terminate
                self.handle_partial_data(text)
        self._alive = False


# dummy decoder, not changing the message
def identity(x): return x

# decoder for Stop Reply Packets
def decodeStopReplyPackets(message):
    #~ print "decodeStopReplyPackets"
    if message[0:1] == 'S':
        #abort with signal
        return STOP_SIGNAL, int(message[1:], 16)
    elif message[0:1] == 'T':
        signal = int(message[1:3], 16)
        if message[-1] == ';':
            extra = message[3:-1].split(';')
        else:
            extra = message[3:].split(';')
        return STOP_THREAD, signal, extra
    elif message[0:1] == 'W' or message[0:1] == 'X':
        #abort with signal
        return STOP_EXITED, int(message[1:], 16)
    else:
        raise GDBException("unknown Stop Reply Packet")

def hex2registers(message):
    return list(unpack('<HHHHHHHHHHHHHHHH', bytes(message).decode('hex')))

def decodeRegister(message):
    return unpack('<H', bytes(message).decode('hex'))[0]

def encodeRegister(value):
    return bytes(pack('<H', value).encode('hex'))


class GDBClient(ClientSocketConnector):
    def __init__(self, *args, **kwargs):
        ClientSocketConnector.__init__(self, *args, **kwargs)
        self.packet = []
        self.recv_mode = IDLE
        self.acknowledged = None
        self.errorcounter = 0   # count NACKS
        self.decoder = None
        self._lock = threading.Lock()
        self.answer = Queue.Queue()

    def handle_partial_data(self, data):
        #~ print data
        for character in data:
            if character == '+':
                #~ print "ACK"    #XXX DEBUG
                self.acknowledged = SUCCESS
                #~ self.answer.put(None)
            elif character == '-':
                #~ print "NACK"    #XXX DEBUG
                self.errorcounter += 1
                self.answer.put(GDBRemoteError('Checksum error'))
            elif character == '$':
                del self.packet[:]
                self.recv_mode = DATA
            elif character == '#':
                self.recv_mode = CRC1
            else:
                if self.recv_mode == DATA:              # save data in packet
                    self.packet.append(character)
                elif self.recv_mode == CRC1:            # get checksum 1
                    if character in HEXDIGITS:
                        self.c1 = character
                        self.recv_mode = CRC2
                elif self.recv_mode == CRC2:            # get checksum 2
                    if character in HEXDIGITS:
                        c2 = character
                        checksum = 0
                        for character in self.packet:
                            checksum = (checksum + ord(character)) & 0xff
                        if int(self.c1 + c2, 16) == checksum:
                            self.write('+')
                            self.handle_packet(''.join(self.packet))
                            del self.packet[:]
                            self.recv_mode = IDLE
                        else:
                            self.write('-')

    def handle_packet(self, packet):
        #~ print 'handle_packet(%r) decoder=%r' % (packet, self.decoder)
        if packet == '':
            self.answer.put(GDBUnknownCommandError("Unknown command"))
        elif packet[0:1] == 'E':
            errorcode = int(packet[1:],16)
            self.answer.put(GDBRemoteError(errorcode, "Target responded with error code %d" % errorcode))
        elif packet[0:2] == 'OK':
            self.answer.put(None)
        elif packet[0:1] == 'o' or packet[0:1] == 'O':
            message = packet[1:]
            if len(message) & 1:
                print "Odd length 'o' message - cutting off last character"     #XXX hack
                message = message[:-1]
            self.output(message.decode('hex'))
        else:
            self.answer.put(packet.decode('hex'))
            #~ else:
                #~ print "unwanted packet: %r" % packet            #XXX ugly

    # --- callbacks ---

    def output(self, message):
        """called on 'o' (output) packages"""
        print "REMOTE>", message

    # --- commands ---
    def set_extended(self):
        """! -- extended mode
        expected answer '' or 'OK'"""
        return self._remote_command('!')

    def last_signal(self):
        """? -- last signal
        expected answer Stop Reply Packets"""
        return self._remote_command('?', decoder=decodeStopReplyPackets)

    def cont(self, startaddress=None, nowait=False):
        """caddr -- continue
        expected answer Stop Reply Packets"""
        return self._remote_command('c%s' % (
                startaddress is not None and '%x' % startaddress or ''
            ), decoder=decodeStopReplyPackets, nowait=nowait, timeout=None
        )

    def cont_with_signal(self, signal, startaddress=None):
        """Csig;addr -- continue with signal
        expected answer Stop Reply Packets"""
        return self._remote_command('C%02x%s' % (
                signal,
                startaddress is not None and ';%x' % startaddress or ''
            ), decoder=decodeStopReplyPackets
        )

    #~ def gdbDetach(self):
        #~ """D -- detach
        #~ no answer"""
        #~ return self._remote_command('D')

    def read_registers(self):
        """g -- read registers
        expected answer 'XX...' or 'ENN'"""
        return self._remote_command('g', decoder=hex2registers)

    def write_registers(self, registers):
        """GXX... -- write registers
        expected answer 'OK' or 'ENN'"""
        return self._remote_command('G%s' % ''.join([encodeRegister(r) for r in registers]))

    def cycle_step(self, cycles, startaddress=None):
        """iaddr,nnn -- cycle step (draft)
        expected answer 'OK' or 'ENN'"""
        return self._remote_command('i%s,%x' % (startaddress is not None and '%x' % startaddress or '', cycles))

    def read_memory(self, startaddress, size):
        """maddr,length -- read memory
        expected answer 'XX...' or 'Enn'"""
        return self._remote_command('m%x,%x' % (startaddress, size))

    def write_memory(self, startaddress, data):
        """maddr,length -- read memory
        expected answer 'OK' or 'Enn'"""
        return self._remote_command('M%x,%x:%s' % (startaddress, len(data), bytes(data).encode('hex')))

    def read_register(self, regnum):
        """pn... -- read reg (reserved)
        expected answer 'XX...' or 'Enn'"""
        return self._remote_command('p%x' % (regnum), decoder=decodeRegister)

    def write_register(self, regnum, value):
        """Pn...=r... -- write register
        expected answer 'OK' or 'Enn'"""
        return self._remote_command('P%x=%s' % (regnum, encodeRegister(value)))

    def query(self, query, nowait=False):
        """query -- general query
        expected answer 'OK' or 'Enn' or ''"""
        return self._remote_command('q%s' % (query,), nowait=nowait)

    def set(self, name, value):
        """Qvar=val -- general set
        expected answer 'OK' or 'Enn' or ''"""
        return self._remote_command('Q%s=%s' % (name, value))

    #~ def gdbRemoteRestart(self):
        #~ """RXX -- remote restart
        #~ no answer expected"""
        #~ return self._remote_command('Q%s=%s' % (querry, value))

    def step(self, startaddress = None):
        """saddr -- step
        expected answer Stop Reply Packets"""
        return self._remote_command('s%s' % (
                startaddress is not None and '%x' % startaddress or ''
            ), decoder=decodeStopReplyPackets
        )

    def step_with_signal(self, signal, startaddress=None):
        """Ssig;addr -- step with signal
        expected answer Stop Reply Packets"""
        return self._remote_command('S%02x%s' % (
                signal,
                startaddress is not None and ';%x' % startaddress or ''
            ), decoder=decodeStopReplyPackets
        )

    def write_memory_binary(self, startaddress, data):
        """maddr,data -- write memory
        expected answer 'OK' or 'Enn'"""
        def escape(s):
            res = []
            for c in s:
                if c in ('$', '#', '\x7d'):
                    res.extend(['\x7d', chr(ord(c) ^ 0x20)])
                else:
                    res.append(c)
            return ''.join(res)
        return self._remote_command('X%x,%x:%s' % (startaddress, len(data), escape(data)))

    def remove_breakpoint(self, type, address, length):
        """zt,addr,length -- remove break or watchpoint (draft)
        expected answer 'OK' 'Enn' or ''"""
        return self._remote_command('z%x,%x,%x' % (type, address, length))

    def set_breakpoint(self, type, address, length):
        """Zt,addr,length -- insert break or watchpoint (draft)
        expected answer 'OK' 'Enn' or ''"""
        return self._remote_command('Z%x,%x,%x' % (type, address, length))

    def monitor(self, command, nowait=False):
        """pass commands to the target interpreter
        expected answer 'OK' or 'Enn' or ''"""
        return self.query('Rcmd,%s' % bytes(command).encode('hex'), nowait=nowait)


    # ---
    def interrupt(self):
        """send Control+C.
        may be used to stop the target if it is running (e.g. after a 'c' command).
        no effect on a stopped target."""
        self.write('\x03')

    # --- internal helper ---
    def _remote_command(self, cmd, decoder=identity, timeout=3, nowait=False):
        self._lock.acquire()
        try:
            # clear queue
            while self.answer.qsize():
                self.answer.get_nowait()
            # send new commnad
            checksum = 0
            for character in cmd:
                checksum = (checksum + ord(character)) & 0xff
            message = '$%s#%02x' % (cmd, checksum)
            self.write(message)

            if nowait:
                return

            ans = self.answer.get(timeout=timeout)
            if isinstance(ans, Exception):
                raise ans
            else:
                return decoder(ans)
        except Queue.Empty:
            raise GDBRemoteTimeout('no answer to command received within time')
        finally:
            self._lock.release()


# ----- test code only below this line -----
if __name__ == '__main__':
    gdb = GDBClient(('', 2000))
    gdb.monitor('help')
    import time; time.sleep(5)
