#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Christopher Wilson <cwilson@cdwilson.us>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

import time
from optparse import OptionGroup
from msp430.bsl.target import SerialBSLTarget


class TelosBTarget(SerialBSLTarget):
    """\
    Telos B target
    
    The Telos B wireless sensor mote has an onboard ADG715 I2C switch that
    controls the TCK and RST signals on the MCU. This switch is normally
    disabled, preventing TCK or RST from being accidentally driven low by
    the BSL hardware.
           _________     __________
          | ADG715  |   | MSP430
          |         |   | ..
    DTR-->| SDA     |   | ..
    RTS-->| SCL     |   | ..
          |         |   | ..
          |-S8--//--|   | .. 
          |   ...   |   | ..
      .---|-S1--//--|---| TCK
      |---|-S0--//--|---| RST
      |   |_________|   |__________
     _|_
     \_/ <--GND
    
    The Telos B schematic can be downloaded from
    http://webs.cs.berkeley.edu/tos/hardware/telos/telos-revb-2004-09-27.pdf
    
    I2C code adapted from tos-bsl found at
    http://code.google.com/p/tinyos-main/
    """
    
    def __init__(self):
        SerialBSLTarget.__init__(self)
        self.i2c_switch_addr = 0x90
        self.i2c_control_delay = 0
        self.invertSCL = False
        self.invertSDA = False
        self.swapSCLSDA = False

    def add_extra_options(self):
        SerialBSLTarget.add_extra_options(self)

        # by default, use 38400 baud
        if self.parser.has_option("--speed"):
            option = self.parser.get_option("--speed")
            option.default = 38400
            option.help = "change baud rate (default %s)" % option.default
            group = self.parser.get_option_group("--speed")
            self.parser.remove_option("--speed")
            group.add_option(option)
        
        group = OptionGroup(self.parser, "I2C switch settings")

        group.add_option("--invert-scl",
                dest="invert_scl",
                action="store_true",
                help="invert I2C switch SCL line",
                default=False)

        group.add_option("--invert-sda",
                dest="invert_sda",
                action="store_true",
                help="invert I2C switch SDA line",
                default=False)
        
        group.add_option("--swap-scl-sda",
                dest="swap_scl_sda",
                action="store_true",
                help="swap I2C switch SCL and SDA lines",
                default=False)

        self.parser.add_option_group(group)

    def parse_extra_options(self):
        SerialBSLTarget.parse_extra_options(self)
        
        if self.options.invert_scl:
            self.invertSCL = True
        
        if self.options.invert_sda:
            self.invertSDA = True
        
        if self.options.swap_scl_sda:
            self.swapSCLSDA = True

    def set_SCL(self, level):
        """\
        Controls SCL pin (0: VCC; 1: GND; unless inverted flag is set)
        """
        
        # invert signal if configured
        if self.invertSCL:
            level = not level
        # set pin level
        if self.swapSCLSDA:
            self.serial.setDTR(not level)
        else:
            self.serial.setRTS(not level)
        time.sleep(self.i2c_control_delay)
            

    def set_SDA(self, level):
        """\
        Controls SDA pin (0: VCC; 1: GND; unless inverted flag is set)
        """
        
        # invert signal if configured
        if self.invertSDA:
            level = not level
        # set pin level
        if self.swapSCLSDA:
            self.serial.setRTS(not level)
        else:
            self.serial.setDTR(not level)
        time.sleep(self.i2c_control_delay)

    def i2c_start(self):
        """Bit bang start sequence on I2C bus"""
        
        self.set_SDA(True)
        self.set_SCL(True)
        self.set_SDA(False)

    def i2c_stop(self):
        """Bit bang stop sequence on I2C bus"""
        
        self.set_SDA(False)
        self.set_SCL(True)
        self.set_SDA(True)

    def i2c_write_bit(self, bit):
        """Bit bang a single bit on I2C bus"""
        
        self.set_SCL(False)
        self.set_SDA(bit)
        self.set_SCL(True)
        self.set_SCL(False)

    def i2c_write_byte(self, byte):
        """Bit bang a single byte on I2C bus"""
        
        self.i2c_write_bit(byte & 0x80);
        self.i2c_write_bit(byte & 0x40);
        self.i2c_write_bit(byte & 0x20);
        self.i2c_write_bit(byte & 0x10);
        self.i2c_write_bit(byte & 0x08);
        self.i2c_write_bit(byte & 0x04);
        self.i2c_write_bit(byte & 0x02);
        self.i2c_write_bit(byte & 0x01);
        self.i2c_write_bit(0);  # "acknowledge"

    def i2c_write_cmd(self, addr, cmdbyte):
        """Bit bang cmdbyte to slave addr on I2C bus"""
        
        self.i2c_start()
        self.i2c_write_byte(addr)
        self.i2c_write_byte(cmdbyte)
        self.i2c_stop()
    
    def i2c_switch_write_cmd(self, cmdbyte):
        """Bit bang cmdbyte to I2C switch"""
        
        self.i2c_write_cmd(self.i2c_switch_addr, cmdbyte)
        time.sleep(self.control_delay)
    
    def i2c_switch_write_bsl_sequence(self, sequence):
        """\
        Write a sequence (array) of state tuples (RST, TEST) to the BSL pins
        """
        
        for RST, TEST in sequence:
            if not self.invertRST:
                RST ^= 1
            if not self.invertTEST:
                TEST ^= 1
            if self.swapResetTest:
                S0 = TEST
                S1 = RST << 1
            else:
                S0 = RST
                S1 = TEST << 1
            self.i2c_switch_write_cmd(S0|S1)
    
    def start_bsl(self):
        """\
        Start the ROM-BSL using the pulse pattern on TEST and RST.
        """

        self.logger.info('ROM-BSL start pulse pattern')
        
        # enabling switch port x connects that port to GND
        # i.e. setting bit x in the cmdbyte drives that pin to GND

        # "BSL entry sequence at dedicated JTAG pins"
        # rst !s0: 0 0 0 0 1 1
        # tck !s1: 1 0 1 0 0 1
        #   s0|s1: 1 3 1 3 2 0

        # "BSL entry sequence at shared JTAG pins"
        # rst !s0: 0 0 0 0 1 1
        # tck !s1: 0 1 0 1 1 0
        #   s0|s1: 3 1 3 1 0 2
        
        bsl_entry_sequence = [
            # (rst, test)
            (0, 1),
            (0, 0),
            (0, 1),
            (0, 0),
            (1, 0),
            (1, 1),
        ]
        
        self.i2c_switch_write_bsl_sequence(bsl_entry_sequence)
        
        time.sleep(0.250)        # give MSP430's oscillator time to stabilize

        self.serial.flushInput() # clear buffers

    def reset(self):
        """Reset the device."""
        
        self.logger.info('Reset device')

        # "Reset sequence"
        # rst !s0: 0 1 1
        # tck !s1: 0 0 1
        #   s0|s1: 3 2 0
        
        reset_sequence = [
            # (rst, test)
            (0, 0),
            (1, 0),
            (1, 1),
        ]
        
        self.i2c_switch_write_bsl_sequence(reset_sequence)


def main():
    # run the main application
    bsl_target = TelosBTarget()
    bsl_target.main()

if __name__ == '__main__':
    main()
