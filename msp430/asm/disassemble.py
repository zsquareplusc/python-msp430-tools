#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2001-2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Disassembler for TI MSP430(X)
"""

import sys
import struct
import msp430.memory
import msp430.asm.peripherals

INSN_WIDTH = 7          # instruction width in chars (args follow)

regnames = ['PC',  'SP',  'SR',  'R3',
            'R4',  'R5',  'R6',  'R7',
            'R8',  'R9',  'R10', 'R11',
            'R12', 'R13', 'R14', 'R15']


def addressMode(bytemode, asrc = None, ad = None, src = None, dest = None):
    x = y = ''
    c = 0
    # source first
    if asrc is not None:
        if src == 2 and asrc > 1: # R3/CG2
            x = "#%d" % (None,None,4,8)[asrc]
        elif src == 3:  # CG3
            if asrc == 3:
                if bytemode:
                    x = "#0xff"
                else:
                    x = "#0xffff"
            else:
                x = "#%d" % (0,1,2)[asrc]
        else:
            if asrc == 0:   # register mode
                x = regnames[src]
            elif asrc == 1:   # pc rel
                if src == 0:
                    x = '0x%(x)04x'
                    c += 1  # read
                elif src == 2: # abs
                    x = '&0x%(x)04x'
                    c += 1  # read
                else:           # indexed
                    x = '0x%%(x)04x(%s)' % regnames[src]
                    c += 1  # read
            elif asrc == 2:   # indirect
                x = '@%s' % regnames[src]
            elif asrc == 3:
                if src == 0:    # immediate
                    x = bytemode and '#0x%(x)02x' or '#0x%(x)04x'
                else:           # indirect auto increment
                    x = '@%s+' % regnames[src]
            else:
                raise ValueError("addressing mode error")
    # dest
    if ad is not None:
        if ad == 0:
            y = '%s' % regnames[dest]
            if dest == 0 and asrc != 1:
                c += 1  # modifying PC gives one cycle penalty
        else:
            if dest == 0:   # PC relative
                #~ y = '%(y)s'
                y = '0x%(y)04x'
                c += 2  # read modify write
            elif dest == 2: # abs
                y = '&0x%(y)04x'
                #~ y = '&0x%(y)04x'
                c += 2  # read modify write
            else:           # indexed
                y = '%%(y)s(%s)' % regnames[dest]
                #~ y = '0x%%(y)04x(%s)' % regnames[dest]
                c += 2  # read modify write

    return x,y,c


singleOperandInstructions = {
    0x00: ('rrc',  0),
    0x01: ('swpb', 0),
    0x02: ('rra',  0),
    0x03: ('sxt',  0),
    0x04: ('push', 1),    # write of stack -> 2
    0x05: ('call', 1),    # write of stack -> 2, modify PC -> 1
    0x06: ('reti', 3),    # pop SR -> 1, pop PC -> 1, modify PC -> 1
}

doubleOperandInstructions = {
    0x4: 'mov',
    0x5: 'add',
    0x6: 'addc',
    0x7: 'subc',
    0x8: 'sub',
    0x9: 'cmp',
    0xa: 'dadd',
    0xb: 'bit',
    0xc: 'bic',
    0xd: 'bis',
    0xe: 'xor',
    0xf: 'and',
}

jumpInstructions = {
    0x0: 'jnz', # jne
    0x1: 'jz',  # jeq
    0x2: 'jnc',
    0x3: 'jc',
    0x4: 'jn',
    0x5: 'jge',
    0x6: 'jl',
    0x7: 'jmp',
}


def words(byte_stream):
    """A generator that delivers a stream of 16 bit numbers, given a stream of bytes"""
    low = None
    for b in byte_stream:
        if low is not None:
            yield low + (b << 8)
            low = None
        else:
            low = b
    if low is not None:
        yield low


class NamedSymbols(object):
    """Handle a collection of peripheral register names and associated bit names"""
    def __init__(self):
        self.peripherals = None

    def load(self, name):
        self.peripherals = msp430.asm.peripherals.load_internal(name)

    def symbol_from_adr(self, opt):
        """try to find a symbol name if the argument points to an absolute address"""
        if opt[0:1] == '&' and self.peripherals is not None:
            adr = int(opt[1:], 0)
            if adr in self.peripherals.registers_by_address:
                return '&%s' % (self.peripherals.registers_by_address[adr]['__name__'], )
        return opt

    def symbols_for_bits(self, arg, opt):
        """for known targets, convert immediate values to a list of OR'ed bits"""
        if opt[0:1] == '&' and self.peripherals is not None:
            reg = opt[1:]
            if arg[0:1] == '#' and reg in self.peripherals.registers_by_name:
                value = int(arg[1:], 0)
                result = []
                if '__bits__' in self.peripherals.registers_by_name[reg]:
                    for mask, name in sorted(self.peripherals.registers_by_name[reg]['__bits__'].items()):
                        if value & mask:
                            value &= ~mask          # clear this bit
                            result.append(name)
                # if there are bits left, append them to the result, so that nothing gets lost
                if value:
                    # look for named values
                    if value in self.peripherals.registers_by_name[reg]['__values__']:
                        result.append(self.peripherals.registers_by_name[reg]['__values__'][value])
                    else:
                        result.append('0x%x' % value)
                return '#%s' % '|'.join(result)
        return arg


class Instruction:
    """\
    this class used to represent an MSP430 assembler instruction.
    emulated instructions are handled on class instantiation.
    It also saves the address the instruction started, the words used to
    decode the instruction and the number of cycles the CPU would have used.
    """
    def __init__(self, address, name, address_mode='', src=None, dst=None, used_words=None, cycles=0, named_symbols=None):
        self.address = address
        self.name = name
        self.address_mode = address_mode
        self.src = src
        self.dst = dst
        self.used_words = used_words
        self.cycles = cycles
        self.named_symbols = named_symbols

        # transformations of emulated instructions
        new_name = None
        if self.name in ('add', 'addx'):
            ex = 'x' if (self.name[-1] == 'x') else ''
            if self.src == '#1':
                new_name = 'inc' + ex
            elif self.src == '#2':
                new_name = 'incd' + ex
            elif self.src == self.dst:
                new_name = 'rla' + ex
        elif self.name in ('addc', 'addcx'):
            ex = 'x' if (self.name[-1] == 'x') else ''
            if self.src == '#0':
                new_name = 'adc' + ex
            elif self.src == self.dst:
                new_name = 'rlc' + ex
        elif self.name == 'dadd' and self.src == '#0':
            new_name = 'dadc'
        elif self.name == 'daddx' and self.src == '#0':
            new_name = 'dadcx'
        elif self.name in ('sub', 'subx'):
            ex = 'x' if (self.name[-1] == 'x') else ''
            if self.src == '#1':
                new_name = 'dec' + ex
            elif self.src == '#2':
                new_name = 'decd' + ex
        elif self.name == 'subc' and self.src == '#0':
            new_name = 'sbc'
        elif self.name == 'subcx' and self.src == '#0':
            new_name = 'sbcx'
        elif self.name == 'xor' and self.src == '#-1':
            new_name = 'inv'
        elif self.name == 'xorx' and self.src == '#-1':
            new_name = 'invx'
        elif self.name in ('mov', 'movx'):
            ex = 'x' if (self.name[-1] == 'x') else ''
            if self.src == '#0':
                if self.dst == 'R3':
                    new_name = 'nop'
                    self.dst = None
                else:
                    new_name = 'clr' + ex
            elif self.src == '@SP+':
                if self.dst == 'PC':
                    new_name = 'ret' + ex
                    self.dst = None
                else:
                    new_name = 'pop' + ex
            elif self.dst == 'PC':
                new_name = 'br'
                self.dst = self.src
        elif self.name == 'bic' and self.dst == 'SR':
            if self.src == '#8':
                new_name = 'dint'
                self.dst = None
            elif self.src == '#1':
                new_name = 'clrc'
                self.dst = None
            elif self.src == '#4':
                new_name = 'clrn'
                self.dst = None
            elif self.src == '#2':
                new_name = 'clrz'
                self.dst = None
        elif self.name == 'bis' and self.dst == 'SR':
            if self.src == '#8':
                new_name = 'eint'
                self.dst = None
            elif self.src == '#1':
                new_name = 'setc'
                self.dst = None
            elif self.src == '#4':
                new_name = 'setn'
                self.dst = None
            elif self.src == '#2':
                new_name = 'setz'
                self.dst = None
        elif self.name == 'cmp' and self.src == '#0':
            new_name = 'tst'
        elif self.name == 'cmpx' and self.src == '#0':
            new_name = 'tstx'
        elif self.name == 'suba' and self.src == '#2':
            new_name = 'decda'
        elif self.name == 'adda' and self.src == '#2':
            new_name = 'incda'
        elif self.name == 'cmpa' and self.src == '#0':
            new_name = 'tsta'
        elif self.name == 'mova' and self.src == '#0':
            new_name = 'clra'
        elif self.name == 'mova' and self.src == '@SP+' and self.dst == 'PC':
            new_name = 'reta'
            self.dst = None
        elif self.name == 'mova' and self.dst == 'PC':
            new_name = 'bra'
            self.dst = self.src
        # emulated insns have no src
        if new_name is not None:
            self.name = new_name
            self.src = None

        # try to replace values by symbols
        if self.named_symbols is not None:
            if self.dst:
                self.dst = self.named_symbols.symbol_from_adr(self.dst)
            if self.src:
                self.src = self.named_symbols.symbol_from_adr(self.src)
                self.src = self.named_symbols.symbols_for_bits(self.src, self.dst)

    def __str__(self):
        if self.src is not None and self.dst is not None:
            return ("%%-%ds %%s, %%s" % INSN_WIDTH) % ("%s%s" % (self.name, self.address_mode), self.src, self.dst)
        elif self.dst is not None:
            return ("%%-%ds %%s" % INSN_WIDTH) % ( "%s%s" % (self.name, self.address_mode), self.dst)
        else:
            return ("%%-%ds" % INSN_WIDTH) % (self.name,)

    def str_width_label(self, label):
        if not self.jumps(): raise ValueError('only possible with jump insns')
        if self.dst is not None and self.dst[0:1] == '#' and self.src is None:
            return ("%%-%ds #%%s" % INSN_WIDTH) % (self.name, label)
        raise ValueError('only possible with dst only insns')

    def jumps(self):
        """return true if this instructions jumps (modifies the PC)"""
        return (self.name == 'call' or self.dst == 'PC') and (self.dst[0] == '#')       # XXX relative address mode missing

    def targetAddress(self, address):
        """only valid for instructions that jump; return the target address of the jump"""
        if self.name == 'call' or self.name == 'br':
            if self.dst[0] == '#':
                return int(self.dst[1:], 0)
            else:
                return address + int(self.dst, 0)
        else:
            raise ValueError('not a branching instruction')

    def ends_a_block(self):
        """helper for a nice output. return true if execution does not continue
        after this instruction."""
        return self.name in ('ret', 'reti', 'br', 'bra')


class JumpInstruction(Instruction):
    """represent jump instructions"""
    def __init__(self, address, name, offset, used_words=None, cycles=0, named_symbols=None):
        Instruction.__init__(self, address, name, 0, None, None, used_words, cycles, named_symbols)
        self.offset = offset

    def jumps(self):
        """return true because this instructions jumps (modifies the PC)"""
        return True

    def targetAddress(self, address):
        """return the target address of the jump"""
        return address + self.offset

    def __str__(self):
        return ("%%-%ds %%+d" % INSN_WIDTH) % (self.name, self.offset)

    def str_width_label(self, label):
        return ("%%-%ds %%s" % INSN_WIDTH) % (self.name, label)

    def ends_a_block(self):
        """helper for a nice output. return true if execution does not continue
        after this instruction."""
        return self.name == 'jmp'


class MSP430Disassembler(object):

    def __init__(self, memory, msp430x=False, named_symbols=None):
        self.memory = memory
        self.msp430x = msp430x
        self.named_symbols = named_symbols
        self.cycles = 0
        self.used_words = []
        self.instructions = []
        self.labels = {}
        self.label_num = 1
        self.next_word = None
        self.address = None
        self.first_address = None
        if self.msp430x:
            self.adr_fmt = "0x%08x"
        else:
            self.adr_fmt = "0x%04x" 

    def restart(self, address):
        """reset internal state. used to restart decoding on each segment"""
        self.address = address
        self.cycles = 0
        self.used_words = []
        self.first_address = None
        self.instructions = []


    def _save_instruction(self, insn):
        """store decoded instruction, prepare for next one"""
        self.instructions.append(insn)
        self.cycles = 0
        self.used_words = []
        self.first_address = None

    def jump_instruction(self, name, offset):
        """save a jump instruction"""
        self._save_instruction(JumpInstruction(
                self.first_address,
                name,
                offset,
                used_words=self.used_words,
                cycles=self.cycles,
                named_symbols=self.named_symbols))

    def instruction(self, name, address_mode='', src=None, dst=None):
        """save a non-jump instruction"""
        self._save_instruction(Instruction(
                self.first_address,
                name,
                address_mode,
                src=src,
                dst=dst,
                used_words=self.used_words,
                cycles=self.cycles,
                named_symbols=self.named_symbols))

    def word(self):
        """get next 16 bits from instruction stream"""
        if self.first_address is None:
            self.first_address = self.address
        word = self.next_word()
        self.cycles += 1
        self.address += 2
        self.used_words.append(word)
        return word

    def process_word(self, extension_word=None):
        """\
        disassemble one instruction from a stream of words.
        """
        opcode = self.word()
        x = y = None
        src_hi = 0
        dst_hi = 0
        # single operand
        if ((opcode & 0xf000) == 0x1000 and
                ((opcode >> 7) & 0x1f in singleOperandInstructions)
        ):
            bytemode = (opcode >> 6) & 1
            asrc = (opcode >> 4) & 3
            src = opcode & 0xf
            x,y,c = addressMode(bytemode, asrc=asrc, src=src)
            name, addcyles = singleOperandInstructions[(opcode >> 7) & 0x1f]
            self.cycles += c + addcyles # some functions have additional cycles (push etc)
            if extension_word is not None:
                name += 'x'
                al = (extension_word >> 6) & 1
                if asrc == 0:    # register mode
                    n = extension_word & 0xf
                    zc = (extension_word >> 8) & 1
                    self.cycles += 1 + n
                else:           # non register mode
                    dst_hi = extension_word & 0xf
                    #~ src_hi = (extension_word >> 7) & 0xf
            else:
                al = 1
            if al:
                if bytemode:
                    address_mode = '.b'
                else:
                    address_mode = ''
            else:
                if bytemode:
                    address_mode = '.a'
                else:
                    address_mode = '.illegal'
            if not (src == 2 or src == 3):
                if asrc == 0:
                    if src == 0: self.cycles += 1 # destination PC adds one
                    if name == 'push': self.cycles += 2
                    if name == 'call': self.cycles += 2
                elif asrc == 1 or asrc == 2:
                    self.cycles += 1
                elif asrc == 3:
                    self.cycles += 1
                    if name == 'call': self.cycles += 1
            else: # this happens for immediate values provided by the constant generators
                if name == 'push': self.cycles += 2 - 1
                if name == 'call': self.cycles += 3

            if '%' in x:
                x = x % {'x': (src_hi << 16) | self.word()}
            if name == 'reti':
                self.instruction(name)
            else:
                self.instruction(name, address_mode, dst=x)

        # double operand
        elif (opcode >> 12) & 0xf in doubleOperandInstructions:
            bytemode = (opcode >> 6) & 1
            adst = (opcode >> 7) & 1
            asrc = (opcode >> 4) & 3
            x,y,c = addressMode(
                    bytemode,
                    src=(opcode >> 8) & 0xf,
                    ad=adst,
                    asrc=asrc,
                    dest=opcode & 0xf)
            name = doubleOperandInstructions[(opcode >> 12) & 0xf]
            self.cycles += c
            if extension_word is not None:
                name += 'x'
                al = (extension_word >> 6) & 1
                if asrc == 0 and adst == 0:    # register mode
                    n = extension_word & 0xf
                    zc = (extension_word >> 8) & 1
                    self.cycles += 1 + n
                else:           # non register mode
                    dst_hi = extension_word & 0xf
                    src_hi = (extension_word >> 7) & 0xf
            else:
                al = 1
            if al:
                if bytemode:
                    address_mode = '.b'
                else:
                    address_mode = ''
            else:
                if bytemode:
                    address_mode = '.a'
                else:
                    address_mode = '.illegal'
            if '%' in x:
                x = x % {'x': (src_hi << 16) | self.word()}
            if '%' in y:
                y = y % {'y': (dst_hi << 16) | self.word()}
            self.instruction(name, address_mode, src=x, dst=y)

        # jump instructions
        elif ((opcode & 0xe000) == 0x2000 and
                ((opcode >> 10) & 0x7 in jumpInstructions)):
            name = jumpInstructions[(opcode >> 10) & 0x7]
            offset = ((opcode & 0x3ff) << 1)
            if offset & 0x400:  # negative?
                offset = -((~offset + 1) & 0x7ff)
            self.cycles += 1 # jumps always have 2 cycles
            self.jump_instruction(name, offset)

        # extended instructions
        elif self.msp430x and (opcode & 0xf000) == 0x0000:
            src = (opcode >> 8) & 0xf
            dst = opcode & 0xf
            insnid = (opcode >> 4) & 0xf
            #~ print insnid
            if insnid == 0:
                if dst == 0: self.cycles += 2
                self.instruction(
                        'mova',
                        src='@%s' % regnames[src],
                        dst=regnames[dst])
            elif insnid == 1:
                if dst == 0: self.cycles += 2
                self.instruction(
                        'mova',
                        src='@%s+' % regnames[src],
                        dst=regnames[dst])
            elif insnid == 2:
                if dst == 0: self.cycles += 2
                address_low = self.word()
                self.instruction(
                        'mova',
                        src='&0x%08x' % ((src<<16) | address_low),
                        dst=regnames[dst])
            elif insnid == 3:
                if dst == 0: self.cycles += 2
                offset = self.word()
                self.instruction(
                        'mova',
                        src='0x%04x(%s)' % (offset, regnames[src]),
                        dst=regnames[dst])

            elif insnid == 4:
                if dst == 0: self.cycles += 2
                insnid_r = (opcode >> 8) & 0x3
                n = (opcode >> 10) & 0x3
                self.cycles += n
                if insnid_r == 0:
                    self.instruction('rrcm.a', src='#%d' % (n,), dst=regnames[dst])
                elif insnid_r == 1:
                    self.instruction('rram.a', src='#%d' % (n,), dst=regnames[dst])
                elif insnid_r == 2:
                    self.instruction('rlam.a', src='#%d' % (n,), dst=regnames[dst])
                elif insnid_r == 3:
                    self.instruction('rrum.a', src='#%d' % (n,), dst=regnames[dst])
            elif insnid == 5:
                if dst == 0: self.cycles += 2
                insnid_r = (opcode >> 8) & 0x3
                n = (opcode >> 10) & 0x3
                self.cycles += n
                if insnid_r == 0:
                    self.instruction('rrcm.w', src='#%d' % (n,), dst=regnames[dst])
                elif insnid_r == 1:
                    self.instruction('rram.w', src='#%d' % (n,), dst=regnames[dst])
                elif insnid_r == 2:
                    self.instruction('rlam.w', src='#%d' % (n,), dst=regnames[dst])
                elif insnid_r == 3:
                    self.instruction('rrum.w', src='#%d' % (n,), dst=regnames[dst])

            elif insnid == 6:
                if dst == 0: self.cycles += 2
                address_low = self.word()
                self.instruction('mova',
                        src=regnames[src],
                        dst='&0x%08x' % ((dst<<16) | address_low))
            elif insnid == 7:
                offset = self.word()
                self.instruction('mova',
                        src=regnames[src],
                        dst='%04x(%s)' % (offset, regnames[dst]))
            elif insnid == 8:
                if dst == 0: self.cycles += 2
                value_low = self.word()
                self.instruction('mova',
                        src='#0x%08x' % ((src<<16) | value_low),
                        dst=regnames[dst])
            elif insnid == 9:
                value_low = self.word()
                self.instruction('cmpa',
                        src='#0x%08x' % ((src<<16) | value_low),
                        dst=regnames[dst])
            elif insnid == 10:
                if dst == 0: self.cycles += 2
                value_low = self.word()
                self.instruction('adda',
                        src='#0x%08x' % ((src<<16) | value_low),
                        dst=regnames[dst])
            elif insnid == 11:
                if dst == 0: self.cycles += 2
                value_low = self.word()
                self.instruction('suba',
                        src='#0x%08x' % ((src<<16) | value_low),
                        dst=regnames[dst])
            elif insnid == 12:
                if dst == 0: self.cycles += 2
                self.instruction('mova',
                        src=regnames[src],
                        dst=regnames[dst])
            elif insnid == 13:
                self.instruction('cmpa',
                        src=regnames[src],
                        dst=regnames[dst])
            elif insnid == 14:
                if dst == 0: self.cycles += 2
                self.instruction('adda',
                        src=regnames[src],
                        dst=regnames[dst])
            elif insnid == 15:
                if dst == 0: self.cycles += 2
                self.instruction('suba',
                        src=regnames[src],
                        dst=regnames[dst])

        # extended instructions 2
        elif self.msp430x and (opcode & 0xf800) == 0x1000:
            dst = opcode & 0xf
            if opcode == 0b0001001100000000:
                self.instruction('reti')
            elif opcode & 0xff00 == 0b0001001100000000:
                call_mode = (opcode >> 4) & 0xf
                if call_mode == 4:
                    self.instruction('calla', dst=regnames[dst])
                elif call_mode == 5:
                    offset = self.word()
                    self.instruction('calla', dst='0x%04x(%s)' % (offset, regnames[dst]))
                elif call_mode == 6:
                    self.instruction('calla', dst='@%s' % regnames[dst])
                elif call_mode == 7:
                    self.instruction('calla', dst='@%s+' % regnames[dst])
                elif call_mode == 8:
                    address_low = self.word()
                    self.instruction('calla', dst='&0x%08x' % ((dst << 16) | address_low))
                elif call_mode == 9:
                    address_low = self.word()
                    self.instruction('calla', dst='0x%08x' % ((dst << 16) | address_low))
                elif call_mode == 11:
                    value_low = self.word()
                    self.instruction('calla', dst='#0x%08x' % ((dst << 16) | value_low))
            elif opcode & 0xff00 == 0b0001010000000000:
                n = (opcode >> 4) & 0xf
                self.instruction('pushm.a', src='#%d' % n, dst=regnames[dst])
            elif opcode & 0xff00 == 0b0001010100000000:
                n = (opcode >> 4) & 0xf
                self.instruction('pushm.w', src='#%d' % n, dst=regnames[dst])
            elif opcode & 0xff00 == 0b0001011000000000:
                n = (opcode >> 4) & 0xf
                self.instruction('pop.a', src='#%d' % n, dst=regnames[dst])
            elif opcode & 0xff00 == 0b0001011100000000:
                n = (opcode >> 4) & 0xf
                self.instruction('pop.w', src='#%d' % n, dst=regnames[dst])

        # extension word
        elif self.msp430x and (opcode & 0xf800) == 0x1800:
            self.process_word(extension_word=opcode)
            return

        # unknown instruction
        if self.used_words: # if an instruction was set it would be the empty list
            self.instruction('illegal-insn-0x%04x' % opcode)


    def disassemble(self, output, source_only=False):
        """Iterate through the segments and disassemble, output at the end"""
        lines = []
        for segment in sorted(self.memory.segments):
            self.restart(segment.startaddress)
            self.next_word = words(segment.data).next
            lines.append((None, "; Segment starting at 0x%08x:" % (segment.startaddress,), '\n'))
            try:
                while True:
                    self.process_word()
            except StopIteration:
                pass

            for insn in self.instructions:
                bytes = ' '.join(['%04x' % x for x in insn.used_words])
                instext = str(insn)
                # does this instruction jump? if so, get a label for the jump target
                if insn.jumps():
                    l_adr = insn.targetAddress(insn.address + 2)
                    if l_adr not in self.labels:
                        # create a new label
                        label = '.L%04d' % self.label_num
                        self.label_num += 1
                        self.labels[l_adr] = label
                    # update note with information about the values
                    if isinstance(insn, JumpInstruction):
                        instext = insn.str_width_label(self.labels[l_adr])
                        note = ' %+d --> %s' % (insn.offset, self.adr_fmt % l_adr)
                    else:
                        instext = insn.str_width_label(self.labels[l_adr])
                        note = ' --> %s' % (self.adr_fmt % l_adr, )
                else:
                    note = ''
                # save generated line
                lines.append((
                        insn.address,
                        "%s:  %-19s" % (self.adr_fmt % insn.address, bytes),
                        "%-36s ; ca. %d cycle%s%s\n" % (instext, insn.cycles, 's' if insn.cycles != 1 else '', note)))
                # after unconditional jumps, make an empty line
                if insn.ends_a_block():
                    lines.append((None, '', '\n'))

        # now output all the lines, put the labels where they belong
        unused_labels = dict(self.labels)        # work on a copy
        for address, prefix, suffix in lines:
            if address in unused_labels:
                label = "%s:" % unused_labels[address]
                del unused_labels[address]  # remove used label
            else:
                label = ''
            # render lines with labels
            if source_only:
                if address is None:
                    output.write("%s %-7s %s" % (prefix, label, suffix))
                else:
                    output.write("%-7s %s" % (label, suffix))
            else:
                output.write("%s %-7s %s" % (prefix, label, suffix))
        # if there are labels left, print them in a list
        if unused_labels:
            output.write("\nLabels that could not be placed:\n")
            for address, label in unused_labels.items():
                output.write("    %s = 0x%04x\n" % (label, address))


debug = False

def inner_main():
    from optparse import OptionParser
    parser = OptionParser(usage="""\
%prog [options] [SOURCE...]

MSP430(X) disassembler.
""")

    parser.add_option("-o", "--output",
            dest="output",
            help="write result to given file",
            metavar="DESTINATION")

    parser.add_option("--debug",
            dest="debug",
            help="print debug messages",
            default=False,
            action='store_true')

    parser.add_option("-v", "--verbose",
            dest="verbose",
            help="print more details",
            default=False,
            action='store_true')

    parser.add_option("-i", "--input-format",
            dest="input_format",
            help="input format name (%s)" % (', '.join(msp430.memory.load_formats),),
            default=None,
            metavar="TYPE")

    parser.add_option("-x", "--msp430x",
            action = "store_true",
            dest = "msp430x",
            default = False,
            help = "Enable MSP430X instruction set")

    parser.add_option("--source",
            dest="source",
            default = False,
            action='store_true',
            help="omit hex dump, just output assembler source")

    parser.add_option("--symbols",
            dest="symbols",
            help="read register names for given architecture (e.g. F1xx)",
            metavar="NAME")

    (options, args) = parser.parse_args()

    if not args:
        parser.error("missing object file name")

    if options.input_format is not None and options.input_format not in msp430.memory.load_formats:
        parser.error('Input format %s not supported.' % (options.input_format))

    global debug
    debug = options.debug

    if options.symbols is not None:
        named_symbols = NamedSymbols()
        named_symbols.load(options.symbols)
    else:
        named_symbols = None

    output = sys.stdout
    if options.output:
        output = open(options.output, 'wb')

    for filename in args:
        if filename == '-':                 # get data from stdin
            fileobj = sys.stdin
            filename = '<stdin>'
        else:
            try:
                fileobj = open(filename, "rb")  # or from a file
            except IOError, e:
                sys.stderr.write('disassemble: %s: File not found\n' % (filename,))
                sys.exit(1)
        mem = msp430.memory.load(filename, fileobj, options.input_format)

        if options.verbose:
            output.write('%s (%d segments):\n' % (filename, len(mem)))

        dis = MSP430Disassembler(mem, msp430x=options.msp430x, named_symbols=named_symbols)
        dis.disassemble(output, options.source)


def main():
    try:
        inner_main()
    except SystemExit:
        raise                                   # let pass exit() calls
    except KeyboardInterrupt:
        if debug: raise                         # show full trace in debug mode
        sys.stderr.write("User abort.\n")       # short messy in user mode
        sys.exit(1)                             # set error level for script usage
    except Exception as msg:                    # every Exception is caught and displayed
        if debug: raise                         # show full trace in debug mode
        sys.stderr.write("\nAn error occurred:\n%s\n" % msg) # short messy in user mode
        sys.exit(1)                             # set error level for script usage

if __name__ == '__main__':
    main()
