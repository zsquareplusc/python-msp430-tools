#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2001-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Assembler for TI MSP430.

Inputs are '.s' files. output is '.o4' for 'ld.py'
"""

import re
import sys
import codecs
from msp430.asm.infix2postfix import infix2postfix


# regular expressions used to parse the asm source
re_line_hint = re.compile(r'#[\t ]+(\d+)[\t ]+"(.+)"')

re_comment = re.compile(r'(;|//).*$')

re_asmstatement = re.compile(r'''^
    (((?P<LABEL>\S+):)?)
    ([\t ]*(?P<INSN>\.?\w+)(?P<MODE>\.\w)?
      ([\t ]+(?P<OPERANDS>.*)
      )?
    )?''', re.VERBOSE|re.IGNORECASE|re.UNICODE)

re_expression = re.compile(r'(?P<NAME>\w+?)=(?P<EXPR>.+)', re.UNICODE)

re_operand = re.compile(r'''
        (?P<STRING>         "(?P<STR>[^"\\]*?(\\.[^"\\]*?)*?)"     ) |
        (?P<SPACE>          \s+                         ) |
        (?P<DELIMITER>      ,                           ) |
        (?P<IMMEDIATE>      \#(?P<IMM_VAL>[^,"]+)       ) |
        (?P<ABSOLUTE>       &(?P<ABS_VAL>[^,"]+)        ) |
        (?P<INDEXED>        (?P<IDX_VALUE>[^,"]+)\((?P<IDX_REG>\w+)\)   ) |
        (?P<POST_INC>       @(?P<PI_REG>[^,"]+)\+       ) |
        (?P<INDIRECT>       @(?P<IND_REG>[^,"]+)        ) |
        (?P<SYMBOLIC>       [^,"]+                      ) |
    ''', re.VERBOSE|re.IGNORECASE|re.UNICODE)


regnumbers = {
        'PC':   0,
        'SP':   1,
        'SR':   2,
        'R0':   0,
        'R1':   1,
        'R2':   2,
        'R3':   3,
        'R4':   4,
        'R5':   5,
        'R6':   6,
        'R7':   7,
        'R8':   8,
        'R9':   9,
        'R10':  10,
        'R11':  11,
        'R12':  12,
        'R13':  13,
        'R14':  14,
        'R15':  15,
}


class AssemblerError(Exception):
    """Exception class for errors that occur during assembling."""


class MSP430Assembler(object):
    """MSP430/MSP430X assembler. It outputs instructions for ld.py"""

    def __init__(self, msp430x=False, debug=False):
        """\
        When msp430x is set to True: enable extended instruction set, otherwise
        only the core 16 bit instructions are available.
        """
        self.debug = debug

        # string-function mapping. all assembler instructions are registered in
        # this dictionary
        self.instructions = {}

        # double operand instructions
        for name, (_, doc) in self._doubleopnames.items():
            self.instructions[name] = (2, self.assembleDoubleOperandInstruction, doc)

        # single operand instructions
        for name, (_, doc) in self._singleopnames.items():
            self.instructions[name] = (1, self.assembleSingleOperandInstruction, doc)

        # jump instructions
        for name, (_, doc) in self._jumpopnames.items():
            self.instructions[name] = (1, self.assembleJumpInstruction, doc)

        # if MSP430X support is desired, extend instruction set
        if msp430x:
            # extended double operand instructions
            for name, (_, doc) in self._doubleopnames.items():
                self.instructions["%sX" % name] = (2, self.assembleExtendedDoubleOperandInstruction, doc+' (20 bit)')
            # extended single operand instructions
            self.instructions.update({
                u'POPM':    (2, self.assemblePUSHMPOPM,
                                "Pop multiple registers from stack"),
                u'PUSHM':   (2, self.assemblePUSHMPOPM,
                                "Push multiple registers on stack"),
                u'PUSHX':   (1, self.assembleExtendedSingleOperandInstruction,
                                "Push 20 bit value"),
                u'RRCM':    (2, self.assembleExtendedSingleOperandInstructionR4,
                                "Rotate multiple right through carry (20 bit)"),
                u'RRUM':    (2, self.assembleExtendedSingleOperandInstructionR4,
                                "Rotate multiple right unsigned (C=0) (20 bit)"),
                u'RRAM':    (2, self.assembleExtendedSingleOperandInstructionR4,
                                "Rotate multiple right arithmetically (20 bit)"),
                u'RLAM':    (2, self.assembleExtendedSingleOperandInstructionR4,
                                "Rotate multiple left arithmetically (20 bit)"),
                u'RRCX':    (1, self.assembleExtendedRotate,
                                "Rotate right through carry (20 bit)"),
                u'RRUX':    (1, self.assembleExtendedRotate,
                                "Rotate right unsigned (C=0) (20 bit)"),
                u'RRAX':    (1, self.assembleExtendedRotate,
                                "Rotate right arithmetically (20 bit)"),
                u'SWPBX':   (1, self.assembleExtendedSingleOperandInstruction,
                                "Swap bytes (20 bit)"),
                u'SXTX':    (1, self.assembleExtendedSingleOperandInstruction,
                                "Sign extend (20 bit)"),
            })

        # an other set of instructions is registered by scanning the method
        # names of this class. it includes emulated instructions and pseudo
        # instructions as well as some extended MSP430X instructions
        for method_name in dir(self):
            # decode "pseudo__dot_ORG_1" style names
            if method_name.startswith('insn_'):
                name = method_name[5:-2].replace('_dot_', '.')
                if method_name[-1] == 'N':
                    argc = None # arbitrary length
                else:
                    argc = int(method_name[-1])
                function = getattr(self, method_name)
                self.instructions[name] = (argc, function, function.__doc__)
            # if MSP430X support is desired, extend instruction set
            if msp430x and method_name.startswith('insnx_'):
                name = method_name[6:-2].replace('_dot_', '.')
                if method_name[-1] == 'N':
                    argc = None # arbitrary length
                else:
                    argc = int(method_name[-1])
                function = getattr(self, method_name)
                self.instructions[name] = (argc, function, function.__doc__)


    def argument(self, value):
        """\
        Prepare a parameter for the linker. Expressions are evaluated.
        """
        try:
            return infix2postfix(value, variable_prefix=u'GET-SYMBOL ')
        except ValueError, e:
            raise AssemblerError('invalid expression: %r' % (value,))

    def expand_label(self, label):
        """\
        Processing of label names. Allow calcualted label names with some restrictions.
        Replace {} as in "__vector_{(0x0004)}" => "__vector_4".
        """
        if label is not None:   # easier to use with regexp'es
            if '{' in label:
                label = re.sub(r'({\(?(.*?)\)?)}', lambda x: str(int(x.group(2), 0)), label)
                #~ print "XXX", name
        return label

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _addressing_mode(self, mode):
        """\
        Return a tuple: ("bw" byte mode bit, "al" address length bit).
        """
        if   mode == '.B': return (1, 1)
        elif mode == '.W': return (0, 1)
        elif mode == '':   return (0, 1)
        elif mode == '.A': return (1, 0)
        else:
            raise AssemblerError('Unsupported mode: %r' % (mode,))


    def _buildArg(self, insn, (mode, value, match_obj), constreg=True):
        """\
        Return a tuple:
        (address mode, register number, memory value or None, 0=abs 1=relative to pc)
        """
        value = value.strip()
        if mode == 'IMMEDIATE':
            try:
                n = int(self.argument(match_obj.group('IMM_VAL')), 0)
            except ValueError:
                pass
            else:
                if constreg:    # if we're allowed to do constreg optimization
                    # here we do the constreg optimisation for the MSP430
                    if n == 4 and insn != 'PUSH':   # MSP430 has a push bug....
                        return (2, 2, None, 0)
                    elif n == 8 and insn != 'PUSH': # MSP430 has a push bug....
                        return (3, 2, None, 0)
                    elif n == 0:
                        return (0, 3, None, 0)
                    elif n == 1:
                        return (1, 3, None, 0)
                    elif n == 2:
                        return (2, 3, None, 0)
                    elif n == -1:
                        return (3, 3, None, 0)
            return (3, 0, match_obj.group('IMM_VAL'), 0)

        try:
            if mode == 'ABSOLUTE':
                return (1, 2, match_obj.group('ABS_VAL'), 0)

            if mode == 'INDEXED':
                return (1, regnumbers[match_obj.group('IDX_REG')], match_obj.group('IDX_VALUE'), 0)

            if mode == 'POST_INC':
                return (3, regnumbers[match_obj.group('PI_REG')], None, 0)

            if mode == 'INDIRECT':
                return (2, regnumbers[match_obj.group('IND_REG')], None, 0)

            if mode == 'REGISTER':
                if value.upper() in regnumbers:         # register mode
                    return (0, regnumbers[value.upper()], None, 0)

            if mode == 'SYMBOLIC':
                return (1, 0, value, 1)         # symbolic mode
        except KeyError as e:
            raise AssemblerError('Register name invalid: %s' % e)
        raise AssemblerError('Bad argument type: %s %s' % (mode, value))


    def _name_address_mode(self, asrc, src):
        """\
        Return a description of address mode, passed the two mode bits and a
        register number.
        """
        if asrc == 0:
            return 'register mode'
        elif asrc == 1:  # indexed/absolute mode
            if src == 0:
                return 'symbolic mode'
            elif src == 2:
                return 'absolute mode'
            else:
                return 'indexed mode'
        elif asrc == 2:
            return 'indirect mode'
        elif asrc == 3:
            if src == 0:
                return 'immediate mode'
            else:
                return 'post increment mode'
        raise ValueError('Unknown addressing mode %r' % (asrc,))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    _doubleopnames = {
            u'MOV':  (0x4, "Copy source to destination"),
            u'ADD':  (0x5, "Add source to destination"),
            u'ADDC': (0x6, "Add with carry"),
            u'SUBC': (0x7, "Subtract with carry"),
            u'SUB':  (0x8, "Subtract source from destination"),
            u'CMP':  (0x9, "Compare"),
            u'DADD': (0xa, "Decimal add"),
            u'BIT':  (0xb, "Test bit (Bitwise AND, CC flags only)"),
            u'BIC':  (0xc, "Clear bit (bitwise AND NOT)"),
            u'BIS':  (0xd, "Set bit (bitwise OR)"),
            u'XOR':  (0xe, "Bitwise exclusive OR"),
            u'AND':  (0xf, "Bitwise AND"),
            }

    def _buildDoubleOperand(self, insn_name, bw, asrc, src, adst, dst):
        """Build opcode from arguments."""
        opcode = self._doubleopnames[insn_name][0]
        return opcode<<12 | bw<<6 | asrc<<4 | src<<8 | adst<<7 | dst

    def assembleDoubleOperandInstruction(self, insn, mode, source, destination):
        """Double operand instruction."""
        bw, al = self._addressing_mode(mode)
        if not al: raise AssemblerError('Bad mode (%s) for this instruction: %s%s' % (mode, insn, mode))

        asrc, src, op1, rel1 = self._buildArg(insn, source)
        adst, dst, op2, rel2 = self._buildArg(insn, destination, constreg=False)
        if adst > 1: raise AssemblerError('%s (%r) is not possible as destination.' % (
                self._name_address_mode(adst,dst), destination[1]))
        out = [u'0x%04x 16bit' % self._buildDoubleOperand(insn, bw, asrc, src, adst, dst)]
        if op1:
            if rel1: out.append(u'%s PC - 16bit' % self.argument(op1))
            else:    out.append(u'%s 16bit' % self.argument(op1))
        if op2:
            if rel2: out.append(u'%s PC - 16bit' % self.argument(op2))
            else:    out.append(u'%s 16bit' % self.argument(op2))
        return ' '.join(out)


    def assembleExtendedDoubleOperandInstruction(self, insn, mode, source, destination):
        """Double operand instruction"""
        # 5.5.2.3 Extended Double-Operand (Format I) Instructions
        bw, al = self._addressing_mode(mode)
        asrc, src, op1, rel1 = self._buildArg(insn, source)
        adst, dst, op2, rel2 = self._buildArg(insn, destination, constreg=False)
        if adst > 1: raise AssemblerError('%s (%r) is not possible as destination.' % (
                self._name_address_mode(adst,dst), destination[1]))
        out = []
        # the core instruction
        opcode = self._buildDoubleOperand(insn[:-1], bw, asrc, src, adst, dst)
        zc = 0
        # arguments
        argument1 = argument2 = 0
        # output core instructions and arguments, add extension word depending
        # on operands
        if op1 or op2:
            words = 2
            # put items in reverse on the stack and assemble the values at the
            # end (so that PC can be used to calculate PC relative arguments)
            if op2:
                if rel2:
                    if op1:
                        argument2 = u'%s PC - 6 -' % self.argument(op2)
                    else:
                        argument2 = u'%s PC - 4 -' % self.argument(op2)
                else:
                    argument2 = u'%s' % self.argument(op2)
                words += 1
                out.append(argument2)
            if op1:
                if rel1:
                    if op2:
                        argument1 = u'%s PC - 6 -' % self.argument(op1)
                    else:
                        argument1 = u'%s PC - 4 -' % self.argument(op1)
                else:
                    argument1 = u'%s' % self.argument(op1)
                words += 1
                out.append(argument1)
            out.append(u'0x%04x' % (opcode))
            out.append(u'0x%04x %s 0xf0000 & 9 >> | %s 0xf0000 & 16 >> |' % (
                    0x1800 | al<<6, argument1, argument2))
            # assemble items from stack
            out.append(u' 16bit'*words)
        else:
            out.append(u'0x%04x 16bit' % (0x1800 | zc<<8 | al<<6))
            out.append(u'0x%04x 16bit' % (opcode))
        return u' '.join(out)


    _singleopnames = {
            u'RRC':  (0x0, "Rotate right through carry"),
            u'SWPB': (0x1, "Swap bytes"),
            u'RRA':  (0x2, "Rotate right arithmetically"),
            u'SXT':  (0x3, "Sign extend"),
            u'PUSH': (0x4, "Push source on stack"),
            u'CALL': (0x5, "Call subroutine"),
            #~ 'RETI': (0x6, "Return from interrupt"),
            }

    def _buildSingleOperand(self, insn_name, bw, adst, dst):
        """Build opcode from arguments."""
        opcode = self._singleopnames[insn_name][0]
        return 0x1000 | opcode<<7 | bw<<6 | adst<<4 | dst


    def assembleSingleOperandInstruction(self, insn, mode, destination):
        """Single operand instruction"""
        bw, al = self._addressing_mode(mode)
        if not al:
            raise AssemblerError('Bad mode (%s) for this instruction: %s%s' (mode, insn, mode))

        adst, dst, op, rel = self._buildArg(insn, destination, constreg=False)
        out = [u'0x%04x 16bit' % self._buildSingleOperand(insn, bw, adst, dst)]
        if op:
            if rel: out.append(u'%s PC - 16bit' % self.argument(op))
            else:   out.append(u'%s 16bit' % self.argument(op))
        return u' '.join(out)

    def insn_RETI_0(self, insn, mode):
        """Return from interrupt"""
        return u'0x1300 16bit'

    def assembleExtendedSingleOperandInstruction(self, insn, mode, destination):
        """PUSHX, SXTX, SWPBX"""
        bw, al = self._addressing_mode(mode)
        adst, dst, op, rel = self._buildArg(insn, destination, constreg=False)

        opcode = self._buildSingleOperand(insn[:-1], bw, adst, dst)
        out = []
        if op:
            if rel: argument = u'%s PC - 4 -' % self.argument(op)
            else:   argument = u'%s' % self.argument(op)
            out.append(u'%s' % (argument,))
            out.append(u'0x%04x' % (opcode | dst))
            out.append(u'0x%04x %s 0xf0000 & 16 >> |' % (0x1800 | al<<6, argument))
            out.extend([u'16bit']*3)
        else:
            out.append(u'0x%04x 16bit' % (0x1800 | al<<6))
            out.append(u'0x%04x 16bit' % (opcode | dst))
        return u' '.join(out)


    def assembleExtendedRotate(self, insn, mode, destination):
        """RRUX, RRAX RRCX"""
        bw, al = self._addressing_mode(mode)
        adst, dst, op, rel = self._buildArg(insn, destination, constreg=False)

        if insn == 'RRUX':
            zc = 1
            name = 'RRC'
        elif insn == 'RRCX':
            zc = 0
            name = 'RRC'
        else:     # RRAX
            zc = 0
            name = 'RRA'
        opcode = self._buildSingleOperand(name, bw, adst, dst)

        out = []
        if op:
            if zc:
                raise AssemblerError(u'Destination %s not supported with %s%s' % (destination, insn, mode))
            if rel: argument = u'%s PC - 4 -' % self.argument(op)
            else:   argument = u'%s' % self.argument(op)
            out.append(argument)
            out.append(u'0x%04x' % (opcode))
            out.append(u'0x%04x %s 0xf0000 & 16 >> |' % (0x1800 | al<<6, argument))
            out.extend([u'16bit']*3)
        else:
            out.append(u'0x%04x 16bit' % (0x1800 | zc<<8 | al<<6))
            out.append(u'0x%04x 16bit' % (opcode))
        return u' '.join(out)


    def insnx_MOVA_2(self, insn, mode, source, destination):
        """Move 20 bit value"""
        asrc, src, op1, rel1 = self._buildArg(insn, source, constreg=False)
        adst, dst, op2, rel2 = self._buildArg(insn, destination, constreg=False)

        out = []
        if asrc == 0 and adst == 0:  # register mode - register mode
            out.append(u'0x00c0 %s 8 << | %s | 16bit' % (src, dst))
        elif asrc == 1 and adst == 0:  # indexed/absolute mode - register mode
            if src == 0:    # symbolic mode
                out.append(u' 0x0030 %s 8 << | %s | 16bit' % (src, dst))
                out.append(u'%s PC - 16bit' % (self.argument(op1),))
            elif src == 2:  # absolute mode
                out.append(u'0x0020 %s 0xf0000 & 8 >> | %s | 16bit' % (self.argument(op1), dst))
                out.append(u' %s 16bit' % (self.argument(op1),))
            else:           # indexed mode
                out.append(u'0x0030 %s 8 << | %s | 16bit' % (src, dst))
                out.append(u'%s 16bit' % (self.argument(op1),))
        elif asrc == 2 and adst == 0:  # indirect mode - register mode
            out.append(u'0x0000 %s 8 << | %s | 16bit' % (src, dst))
        elif asrc == 3 and adst == 0:  # immediate/post_inc mods - register mode
            if src == 0:    # immediate mode
                out.append(u'0x0080 %s 0xf0000 & 8 >> | %s | 16bit' % (self.argument(op1), dst))
                out.append(u'%s 16bit' % (self.argument(op1),))
            else:           # post_inc
                out.append(u'0x0010 %s 8 << | %s | 16bit' % (src, dst))
        elif asrc == 0 and adst == 1:  # register mode - indexed mode
            if dst == 0:    # symbolic mode
                out.append(u'0x0070 %s 8 << | %s | 16bit' % (src, dst))
                out.append(u'%s PC - 16bit' % (self.argument(op2),))
            elif dst == 2:  # aboslute mode
                out.append(u'0x0060 %s 8 << | %s 0xf0000 & 16 >> | 16bit' % (src, self.argument(op2)))
                out.append(u'%s 16bit' % (self.argument(op2),))
            else:           # indexed mode
                out.append(u'0x0070 %s 8 << | %s | 16bit' % (src, dst))
                out.append(u'%s 16bit' % (self.argument(op2),))
        if out:
            return u' '.join(out)
        else:
            raise AssemblerError(u'Unsupported addressing modes for MOVA (%s and %s)' % (
                    self._name_address_mode(asrc, src),
                    self._name_address_mode(adst, dst)))


    def assembleExtendedDoubleOperandInstruction2(self, insn, mode, source, destination, reg, imm):
        """Assemble one of the extended address mode instructions"""
        asrc, src, op1, rel1 = self._buildArg(insn, source, constreg=False)
        adst, dst, op2, rel2 = self._buildArg(insn, destination, constreg=False)

        if adst != 0:
            raise AssemblerError(u'%s (%r) is not possible as destination.' % (
                    self._name_address_mode(adst, dst), destination[1]))

        out = []
        if asrc == 0:       # register mode
            out.append(u'0x%04x %s 8 << | %s | 16bit' % (reg, src, dst))
        elif asrc == 3:     # immediate/post_inc modes
            if src == 0:    # immediate mode
                out.append(u'0x%04x %s 0xf0000 & 8 >> | %s | 16bit' % (imm, self.argument(op1), dst))
                out.append(u'%s 16bit' % (self.argument(op1),))
        if out:
            return u' '.join(out)
        else:
            raise AssemblerError(u'%s (%r) is not possible as source.' % (
                self._name_address_mode(asrc, src), source[1]))

    def insnx_ADDA_2(self, insn, mode, source, destination):
        """Add 20-bit source to a 20-bit destination register"""
        return self.assembleExtendedDoubleOperandInstruction2(insn, mode, source, destination, 0x00e0, 0x00a0)

    def insnx_SUBA_2(self, insn, mode, source, destination):
        """Subract 20-bit source from a 20-bit destination register"""
        return self.assembleExtendedDoubleOperandInstruction2(insn, mode, source, destination, 0x00f0, 0x00b0)

    def insnx_CMPA_2(self, insn, mode, source, destination):
        """Compare the 20-bit source with a 20-bit destination register"""
        return self.assembleExtendedDoubleOperandInstruction2(insn, mode, source, destination, 0x00d0, 0x0090)


    def assembleExtendedSingleOperandInstructionR4(self, insn, mode, source, destination):
        """RRCM, RRAM, RLAM, RRUM"""
        asrc, src, op1, rel1 = self._buildArg(insn, source, constreg=False)
        adst, dst, op2, rel2 = self._buildArg(insn, destination, constreg=False)

        if mode == '.a':
            option = 0
        elif mode in ('', '.w'):
            option = 1
        else:
            raise AssemblerError('Unsupported mode (%s) for %s%s' % (mode, insn, mode))

        if adst != 0:
            raise AssemblerError('%s (%r) is not possible as destination.' % (
                    self._name_address_mode(adst, dst), destination[1]))

        out = []
        if asrc == 3:       # immediate/post_inc mods - register mode
            if src == 0:    # immediate mode
                count = int(op1)
                if not 0 <= count <= 3:
                    raise AssemblerError('Repetition count out of range (%d)' % (count,))
                return u'0x%04x 16bit' % (
                        { 'RRCM': 0x0040,
                          'RRAM': 0x0140,
                          'RLAM': 0x0240,
                          'RRUM': 0x0340,
                        }[insn] | (option << 4) | (count<<10) | dst)
        raise AssemblerError(u'%s (%r) is not possible as count.' % (
                self._name_address_mode(asrc, src), source[1]))


    def insnx_CALLA_1(self, insn, mode, target):
        """Call subroutine (20 bit addresses)"""
        if mode:
            raise AssemblerError('Bad mode (%s) for this instruction: %s%s' (mode, insn, mode))

        adst, dst, op, rel = self._buildArg(insn, target, constreg=False)

        out = []
        if adst == 0:       # register mode
            out.append(u'0x%04x 16bit' % (0x1340 | dst))
        elif adst == 1:     # indexed/absolute mode
            if dst == 0:    # relative mode
                out.append(u'%s PC - 2 -' % (self.argument(op),))
                out.append(u'0x%04x %s PC 2 - 0xf0000 & >> 16 | 16bit 16bit' % (0x1390 | dst, self.argument(op)))
            elif dst == 2:  # absolute mode
                out.append(u'0x%04x %s 0xf0000 & >> 16 | 16bit' % (0x1380 | dst, self.argument(op)))
                out.append(u'%s 16bit' % (self.argument(op),))
            else:           # indexed mode
                out.append(u'0x%04x 16bit' % (0x1350 | dst))
                out.append(u'%s 16bit' % (self.argument(op),))
        elif adst == 2:     # indirect mode
            out.append(u'0x%04x 16bit' % (0x1360 | dst))
        elif adst == 3:     # immediate/post_inc mods
            if dst == 0:    # immediate mode
                out.append(u'0x%04x %s 0xf0000 & >> 16 | 16bit' % (0x13b0 | dst, self.argument(op)))
                out.append(u'%s 16bit' % (self.argument(op),))
            else:           # post_inc
                out.append(u'0x%04x 16bit' % (0x1370 | dst))
        return ' '.join(out)


    def assemblePUSHMPOPM(self, insn, mode, repeat, register):
        """PUSHM, POPM"""
        asrc, src, op1, rel1 = self._buildArg(insn, repeat, constreg=False)
        adst, dst, op2, rel2 = self._buildArg(insn, register, constreg=False)

        if mode == '.a':
            option = 0
        elif mode in ('', '.w'):
            option = 1
        else:
            raise AssemblerError(u'Unsupported mode (%s) for %s%s' % (mode, insn, mode))

        if adst != 0:
            raise AssemblerError(u'%s (%r) is not possible as destination.' % (
                    self._name_address_mode(adst, dst), destination[1]))

        out = []
        if asrc == 3:       # immediate/post_inc mods - register mode
            if src == 0:    # immediate mode
                count = int(op1, 0)
                if not 1 <= count <= 16:
                    raise AssemblerError('Repetition count out of range (%d)' % (count,))
                if insn == 'PUSHM':
                    out = [u'0x%04x 16bit' % (0x1400 | (option << 8) | (count<<4) | dst)]
                else:     # POPM
                    out = [u'0x%04x 16bit' % (0x1600 | (option << 8) | (count<<4) | (dst-count-1))]
                return u' '.join(out)
        raise AssemblerError(u'%s (%r) is not possible as count.' % (
                self._name_address_mode(asrc, src), repeat))


    _jumpopnames = {
            u'JNE':  (0x2000, "Jump if not equal (JNZ)"),
            u'JNZ':  (0x2000, "Jump if not zero"),
            u'JEQ':  (0x2400, "Jump if equal (JZ)"),
            u'JZ':   (0x2400, "Jump if zero"),
            u'JLO':  (0x2800, "Jump if lower (unsigned, JNC)"),
            u'JNC':  (0x2800, "Jump if carry is not set"),
            u'JHS':  (0x2c00, "Jump if higher or same (unsigned, JC)"),
            u'JC':   (0x2c00, "Jump if carry is set"),
            u'JN':   (0x3000, "Jump if negative"),
            u'JGE':  (0x3400, "Jump if greater or equal (signed)"),
            u'JL':   (0x3800, "Jump if lower (signed)"),
            u'JMP':  (0x3c00, "Jump unconditionally"),
            }

    def assembleJumpInstruction(self, insn, mode, (t, target, match_obj)):
        """(un)conditional, relative jump"""
        if mode:
            raise AssemblerError(u'Bad mode (%s) for this instruction: %s%s' (mode, insn, mode))
        try:
            opcode = self._jumpopnames[insn][0]
        except KeyError:
            raise AssemblerError(u"Not a valid jump instruction: %r" % (insn,))
        if target[0:1] == '$':
            # relative jumps to current position (PC)
            try:
                distance = int(target[1:], 0)
            except ValueError:
                raise AssemblerError(u"Jump distance is not understood: %r (only $+N / $-N)" % (target,))
        else:
            # jumps to labels, absolute addresses
            distance = u'%s PC - 2 -' % self.argument(target)
        return u'0x%04x %s JMP' % (opcode, distance)


    # These instructions are emulated by using one of the insn above most
    # depend on the constant registers to be efficient.

    def _emulation(self, insn, mode, arg_str):
        return self.assembleDoubleOperandInstruction(insn, mode, *self.tokenize_operands(arg_str))

    def insn_ADC_1(self, insn, mode, arg):
        """Add carry bit to destination"""
        return self._emulation('ADDC', mode, u'#0, %s' % arg[1])

    def insn_DADC_1(self, insn, mode, arg):
        """Add carry bit to destination (decimal mode)"""
        return self._emulation('DADD', mode, u'#0, %s' % arg[1])

    def insn_DEC_1(self, insn, mode, arg):
        """Decrement destination by one"""
        return self._emulation('SUB', mode, u'#1, %s' % arg[1])

    def insn_DECD_1(self, insn, mode, arg):
        """Decrement destination by two"""
        return self._emulation('SUB', mode, u'#2, %s' % arg[1])

    def insn_INC_1(self, insn, mode, arg):
        """Increment destination by one"""
        return self._emulation('ADD', mode, u'#1, %s' % arg[1])

    def insn_INCD_1(self, insn, mode, arg):
        """Increment destination by two"""
        return self._emulation('ADD', mode, u'#2, %s' % arg[1])

    def insn_SBC_1(self, insn, mode, arg):
        """Subtract carry bit from destination"""
        return self._emulation('SUBC', mode, u'#0, %s' % arg[1])

    def insn_INV_1(self, insn, mode, arg):
        """Invert all bits of destination"""
        return self._emulation('XOR', mode, u'#-1, %s' % arg[1])

    def insn_RLA_1(self, insn, mode, arg):
        """Rotate left through arithmetically"""
        return self._emulation('ADD', mode, u'%s, %s' % (arg[1], arg[1]))

    def insn_RLC_1(self, insn, mode, arg):
        """Rotate left through carry"""
        return self._emulation('ADDC', mode, u'%s, %s' % (arg[1], arg[1]))

    def insn_CLR_1(self, insn, mode, arg):
        """Clear (set to 0) destination"""
        return self._emulation('MOV', mode, u'#0, %s' % arg[1])

    def insn_CLRC_0(self, insn, mode):
        """Clear carry bit"""
        return self._emulation('BIC', '', '#1, SR')

    def insn_CLRN_0(self, insn, mode):
        """Clear negative bit"""
        return self._emulation('BIC', '', '#4, SR')

    def insn_CLRZ_0(self, insn, mode):
        """Clear zero bit"""
        return self._emulation('BIC', '', '#2, SR')

    def insn_POP_1(self, insn, mode, arg):
        """Pop element from stack into destination"""
        return self._emulation('MOV', mode, u'@SP+, %s' % arg[1])

    def insn_SETC_0(self, insn, mode):
        """Set carry bit"""
        return self._emulation('BIS', '', '#1, SR')

    def insn_SETN_0(self, insn, mode):
        """Set negative bit"""
        return self._emulation('BIS', '', '#4, SR')

    def insn_SETZ_0(self, insn, mode):
        """Set zero bit"""
        return self._emulation('BIS', '', '#2, SR')

    def insn_TST_1(self, insn, mode, arg):
        """Compare argument against zero"""
        return self._emulation('CMP', mode, u'#0, %s' % arg[1])

    def insn_BR_1(self, insn, mode, arg):
        """Unconditionally jump to given target"""
        return self._emulation('MOV', '', u'%s, PC' % arg[1])

    def insn_DINT_0(self, insn, mode):
        """Clear GIE flag"""
        return self._emulation('BIC', '', '#8, SR')

    def insn_EINT_0(self, insn, mode):
        """Set GIE flag"""
        return self._emulation('BIS', '', '#8, SR')

    def insn_NOP_0(self, insn, mode):
        """No operation (1 cycle)"""
        return self._emulation('MOV', '', 'R3, R3')

    def insn_RET_0(self, insn, mode):
        """Return from subroutine"""
        return self._emulation('MOV', '', '@SP+, PC')


    # extended emulated instructions
    def _x_emulation(self, insn, mode, arg_str):
        return self.assembleExtendedDoubleOperandInstruction(insn, mode, *self.tokenize_operands(arg_str))

    def insnx_ADCX_1(self, insn, mode, arg):
        """Add carry bit to destination (20 bit)"""
        return self._x_emulation('ADDCX', '',  u'#0, %s' % arg[1])

    def insnx_CLRX_1(self, insn, mode, arg):
        """Clear 20 bit"""
        return self._x_emulation('MOVX', '', u'#0, %s' % arg[1])

    def insnx_DADCX_1(self, insn, mode, arg):
        """Add carry bit to destination (20 bit, decimal mode)"""
        return self._x_emulation('DADDC', '', u'#0, %s' % arg[1])

    def insnx_DECX_1(self, insn, mode, arg):
        """Decrement destination by one (20 bit)"""
        return self._x_emulation('SUBX', '', u'#1, %s' % arg[1])

    def insnx_DECDX_1(self, insn, mode, arg):
        """Decrement destination by two (20 bit)"""
        return self._x_emulation('SUBX', '', u'#2, %s' % arg[1])

    def insnx_INCX_1(self, insn, mode, arg):
        """Increment destination by one (20 bit)"""
        return self._x_emulation('ADDX', '', '#1, %s' % arg[1])

    def insnx_INCDX_1(self, insn, mode, arg):
        """Increment destination by two (20 bit)"""
        return self._x_emulation('ADDX', '', u'#2, %s' % arg[1])

    def insnx_INVX_1(self, insn, mode, arg):
        """Invert destination (20 bit)"""
        return self._x_emulation('XORX', '', u'#-1, %s' % arg[1])

    def insnx_RLAX_1(self, insn, mode, arg):
        """Rotate left arithmetically (20 bit)"""
        return self._x_emulation('ADDX', '', u'%s, %s' % (arg[1], arg[1]))

    def insnx_RLCX_1(self, insn, mode, arg):
        """Rotate left through carry (20 bit)"""
        return self._x_emulation('ADDCX', '', u'%s, %s' % (arg[1], arg[1]))

    def insnx_SBCX_1(self, insn, mode, arg):
        """Subtract carry bit (20 bit)"""
        return self._x_emulation('SUBCX', '', u'#0, %s' % arg[1])

    def insnx_TSTX_1(self, insn, mode, arg):
        """Compare destination against 0 (20 bit)"""
        return self._x_emulation('CMPX', '', u'#0, %s' % arg[1])

    def insnx_POPX_1(self, insn, mode, arg):
        """Pop value from stack to destination (20 bit)"""
        return self._x_emulation('MOVX', '', u'@SP+, %s' % arg[1])

    # more emulated instructions

    def insnx_BRA_1(self, insn, mode, arg):
        """Jump unconditionally (20 bit, any address)"""
        return self.insnx_MOVA_2('MOVA', '', *self.tokenize_operands(u'%s, PC' % arg[1]))

    def insnx_CLRA_1(self, insn, mode, arg):
        """Clear 20 bit address resgiter"""
        return self.insnx_MOVA_2('MOVA', '', *self.tokenize_operands(u'#0, %s' % arg[1]))

    def insnx_DECDA_1(self, insn, mode, arg):
        """Decrement destination address register by one"""
        return self.insnx_SUBA_2('SUBA', '', *self.tokenize_operands(u'#2, %s' % arg[1]))

    def insnx_INCDA_1(self, insn, mode, arg):
        """Increment destination address register by two"""
        return self.insnx_ADDA_2('ADDA', '', *self.tokenize_operands(u'#2, %s' % arg[1]))

    def insnx_RETA_0(self, insn, mode):
        """Return from subroutine (when invoked with CALLA)"""
        return self.insnx_MOVA_2('MOVA', '', *self.tokenize_operands(u'@SP+, PC'))

    def insnx_TSTA_1(self, insn, mode, arg):
        """Compare destination address register against 0"""
        return self.insnx_CMPA_2('CMPA', '', *self.tokenize_operands(u'#0, %s' % arg[1]))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insn__dot_TEXT_0(self, insn, mode):
        """Select .text section for output"""
        return 'SEGMENT .text'

    def insn__dot_DATA_0(self, insn, mode):
        """Select .data section for output"""
        return 'SEGMENT .data'

    def insn__dot_BSS_0(self, insn, mode):
        """Select .bss section for output"""
        return 'SEGMENT .bss'

    def insn__dot_SECTION_1(self, insn, mode, name):
        """Select named section for output"""
        if name[0] != 'SYMBOLIC':
            raise AssemblerError('Unsupported argument type: %r' % name[1])
        return u'SEGMENT %s' % (name[1],)

    def insn__dot_SET_2(self, insn, mode, label, value):
        """Define a symbol with a value (can be used at link time)."""
        if label[0] != 'SYMBOLIC':
            raise AssemblerError('Unsupported argument type: %r' % label[1])
        if value[0] != 'SYMBOLIC':
            raise AssemblerError('Unsupported argument type: %r' % value[1])
        return u'%s CONSTANT-SYMBOL %s' % (value[1], label[1])

    def insn__dot_WEAKALIAS_2(self, insn, mode, label, value):
        """\
        Define a symbol with a value (can be used at link time). This is some
        sort of weak definition that can be redefined by other labels or set
        commands.
        """
        if label[0] != 'SYMBOLIC':
            raise AssemblerError('Unsupported argument type: %r' % label[1])
        if value[0] != 'SYMBOLIC':
            raise AssemblerError('Unsupported argument type: %r' % value[1])
        return u'WEAK-ALIAS %s %s' % (label[1], value[1])

    def insn__dot_ASCII_N(self, insn, mode, *args):
        """Insert the given text as bytes."""
        result = []
        for am, value, m in args:
            if am != 'STRING':
                raise AssemblerError('Bad argument (.ASCII only allows strings): %r' % value)
            result.extend([u'%s 8bit' % (ord(x),) for x in codecs.escape_decode(m.group('STR'))[0]])
        return u' '.join(result)

    def insn__dot_ASCIIZ_N(self, insn, mode, *args):
        """Insert the given text as bytes, append null byte"""
        return self.insn__dot_ASCII_N(insn, mode, *args) + ' 0 8bit'

    def insn__dot_BYTE_N(self, insn, mode, *args):
        """Insert the given 8 bit values"""
        result = []
        for am, value, m in args:
            if am != 'SYMBOLIC':
                raise AssemblerError('Bad argument (.BYTE only allows expressions): %r' % value)
            result.append(u'%s 8bit' % (self.argument(value),))
        return u' '.join(result)

    def insn__dot_WORD_N(self, insn, mode, *args):
        """Insert the given 16 bit values"""
        result = []
        for am, value, m in args:
            if am != 'SYMBOLIC':
                raise AssemblerError('Bad argument (.WORD only allows expressions): %r' % value)
            result.append(u'%s 16bit' % (self.argument(value),))
        return u' '.join(result)

    def insn__dot_LONG_N(self, insn, mode, *args):
        """Insert the given 32 bit values"""
        result = []
        for am, value, m in args:
            if am != 'SYMBOLIC':
                raise AssemblerError('Bad argument (.LONG only allows expressions): %r' % value)
            result.append(u'%s 32bit' % (self.argument(value),))
        return u' '.join(result)

    def insn__dot_SKIP_1(self, insn, mode, amount):
        """Skip the given amount of bytes"""
        return u'%s RESERVE' % (self.argument(amount[1]),)

    def insn__dot_EVEN_0(self, insn, mode):
        """Align address pointer to an even address"""
        return '1 ALIGN'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def tokenize_operands(self, arg_str):
        """\
        Split a comma separated argument string into a list of argument
        tuples (address_mode, value, match_obj).
        """
        args = []
        if arg_str:
            pos = 0
            while pos < len(arg_str):
                m = re_operand.match(arg_str, pos)
                if m is None:
                    raise AssemblerError(u'Can not parse argument: %r...' % (
                        arg_str[pos:pos+10],))
                pos = m.end()
                token_type = m.lastgroup
                if token_type is None:
                    raise AssemblerError(u'Can not parse argument: %r...' % (arg_str,))
                elif token_type not in ('DELIMITER', 'SPACE'):
                    token = m.group(token_type)
                    # registers and symbols can not be told appart with a
                    # simple regexp. do the conversion here
                    if token_type == 'SYMBOLIC' and token.upper() in regnumbers:
                        token_type = 'REGISTER'
                    args.append((token_type, token, m))
        return args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def assemble(self, f, filename=None, output=sys.stdout):
        """Build a list of pseudo instructions from the source."""
        c_comment = 0
        lineno = 0
        if filename:
            output.write(u'FILENAME %s\n' % (filename,))   # XXX escape string (whitespace, encoding)
        if self.debug: sys.stderr.write(u'Parsing "%s":\n' % (filename,))

        try:
            while True:
                line = f.readline()
                lineno += 1
                if not line: break              # if end of file

                # catch line/filename hints from the preprocessor
                m = re_line_hint.match(line)
                if m:
                    # get line number minus one because we are pre-incrementing
                    # lineno above and the hint is for the following line
                    lineno = int(m.group(1)) - 1
                    if filename != m.group(2):
                        filename = m.group(2)
                        output.write(u'FILENAME %s\n' % (filename,))   # XXX escape string (whitespace, encoding)
                    continue

                # remove line comments
                line = re_comment.sub('', line)  # cut out single line comments
                line = line.rstrip()            # strip whitespace/EOL
                if not line: continue           # skip empty lines

                # test for expression like lines: "SYMBOL=VALUE"
                g = re_expression.match(line)
                if g:
                    name = self.expand_label(g.group('NAME').strip())
                    if self.debug: sys.stderr.write('%s:%d: %s = %s\n' % (
                            filename,
                            lineno,
                            name,
                            g.group('EXPR').strip()))
                    output.write('%d LINE    %s CONSTANT-SYMBOL %s\n' % (
                            lineno,
                            self.argument(g.group('EXPR').strip()),
                            name,
                            ))
                    continue

                # test for assembler statements: "[LABEL:] INSN [SRC] [DST] [...]
                g = re_asmstatement.match(line)
                if g:
                    #~ print g.groups()
                    label = self.expand_label(g.group(u'LABEL'))
                    insn  = (g.group(u'INSN') or '').upper()
                    mode  = (g.group(u'MODE') or '').upper()
                    arg_str = g.group(u'OPERANDS')
                    args = self.tokenize_operands(arg_str)
                    if self.debug: sys.stderr.write(u'%s:%d: %-16s %-8s %s\n' % (
                            filename,
                            lineno,
                            label is not None and label+u':' or u'',
                            u'%s%s' % (insn, mode),
                            u', '.join(x[1] for x in args)))
                    if label:
                        output.write(u'%d LINE    CREATE-SYMBOL %s\n' % (lineno, label))
                    if insn:
                        if insn in self.instructions:
                            n_args, function, doc = self.instructions[insn]

                            if n_args is not None and len(args) != n_args:
                                raise AssemblerError(
                                        u'Bad number of arguments for %s (found %d, required %d)' % (
                                                insn, len(args), n_args))
                            else:
                                iop = function(insn, mode, *args)
                                if iop:
                                    output.write(u'%d LINE    ' % (lineno,))
                                    output.write(iop)
                                    if self.debug:
                                        # in debug mode add source line as comment
                                        output.write(u' ' * max(0, (60 - len(iop))))
                                        output.write(u' # %s%s %s\n' % (
                                                insn,
                                                mode,
                                                u', '.join(x[1] for x in args)))
                                    else:
                                        output.write('\n')
                        else:
                            raise AssemblerError(u'Syntax Error: unknown instruction %r' % (insn,))
        except AssemblerError as e:
            # annotate exception with location in source file
            e.line = lineno
            e.filename = filename
            e.text = line
            raise e

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():
    from optparse import OptionParser

    parser = OptionParser(usage = '%prog [options] source.S')
    parser.add_option(
            "-x", "--msp430x",
            action = "store_true",
            dest = "msp430x",
            default = False,
            help = "Enable MSP430X instruction set")
    parser.add_option(
            "-o", "--outfile",
            dest = "outfile",
            help = "name of the object file",
            default = None,
            metavar = "FILE")
    parser.add_option(
            "--filename",
            dest = "input_filename",
            help = "Use this filename for input (useful when source is passed on stdin)",
            metavar = "FILE")
    parser.add_option(
            "-v", "--verbose",
            action = "store_true",
            dest = "verbose",
            default = False,
            help = "print status messages to stderr")
    parser.add_option(
            "--debug",
            action = "store_true",
            dest = "debug",
            default = False,
            help = "print debug messages to stderr")
    parser.add_option(
            "-i", "--instructions",
            action = "store_true",
            dest = "list_instructions",
            default = False,
            help = "Show list of supported instructions and exit (see also -x)")

    (options, args) = parser.parse_args()

    assembler = MSP430Assembler(msp430x=options.msp430x, debug=options.debug)

    if options.list_instructions:
        n_pseudo = n_real = 0
        for insn in sorted(assembler.instructions.keys()):
            sys.stdout.write('%-8s %s\n' % (insn, assembler.instructions[insn][2]))
            if insn[0] == '.':
                n_pseudo += 1
            else:
                n_real += 1
        sys.stdout.write('-- %d pseudo (internal) instructions, %d MSP430%s instructions\n' % (
                    n_pseudo, n_real, options.msp430x and 'X' or ''))
        sys.exit(1)

    if not args:
        parser.error("Missing filename.")
    if len(args) > 1:
        parser.error("Only one file at a time allowed.")

    filename = args[0]
    if options.input_filename is None:
        options.input_filename = filename

    if options.outfile is not None:
        out = codecs.open(options.outfile, 'w', 'utf-8')
    else:
        out = codecs.getwriter("utf-8")(sys.stdout)

    # XXX make stderr unicode capable
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr)

    if options.debug:
        sys.stderr.write("%s\n" % (("BEGIN %s" % filename).center(70).replace(' ', '-')))

    try:
        if not filename or filename == '-':
            assembler.assemble(
                    codecs.getreader("utf-8")(sys.stdin),
                    options.input_filename,
                    output=out)
        else:
            try:
                f = codecs.open(filename, 'r', 'utf-8')
                assembler.assemble(f, options.input_filename, output=out)
                f.close()
            except IOError as e:
                sys.stderr.write('as: %s: File not found\n' % (filename,))
                sys.exit(1)
    except AssemblerError as e:
        sys.stderr.write('%s:%s: %s\n' % (e.filename, e.line, e))
        if options.debug:
            if hasattr(e, 'text'):
                sys.stderr.write('%s:%s: input line: %r\n' % (e.filename, e.line, e.text))
        sys.exit(1)


    if options.debug:
        sys.stderr.write("%s\n" % (("END %s" % filename).center(70).replace(' ', '-')))


if __name__ == '__main__':
    main()
