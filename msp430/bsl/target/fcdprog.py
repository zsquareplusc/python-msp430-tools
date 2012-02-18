#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Christopher Wilson <cwilson@cdwilson.us>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

from msp430.bsl.target import SerialBSLTarget


class FCDProgTarget(SerialBSLTarget):
    """\
    Flying Camp Design MSP430 BSL Programmer target
    
    http://www.flyingcampdesign.com
    """
    
    def __init__(self):
        SerialBSLTarget.__init__(self)

    def add_extra_options(self):
        SerialBSLTarget.add_extra_options(self)

        # by default, invert TEST/TCK
        if self.parser.has_option("--invert-test"):
            option = self.parser.get_option("--invert-test")
            option.action = "store_false"
            option.default = True
            option.help = "do not invert RTS line (default inverted)"
            group = self.parser.get_option_group("--invert-test")
            self.parser.remove_option("--invert-test")
            group.add_option(option)

        # by default, invert RST
        if self.parser.has_option("--invert-reset"):
            option = self.parser.get_option("--invert-reset")
            option.action = "store_false"
            option.default = True
            option.help = "do not invert DTR line (default inverted)"
            group = self.parser.get_option_group("--invert-reset")
            self.parser.remove_option("--invert-reset")
            group.add_option(option)

        # by default, swap TEST/TCK and RST
        if self.parser.has_option("--swap-reset-test"):
            option = self.parser.get_option("--swap-reset-test")
            option.action = "store_false"
            option.default = True
            option.help = "do not exchange RST and TEST signals (DTR/RTS) (default swapped)"
            group = self.parser.get_option_group("--swap-reset-test")
            self.parser.remove_option("--swap-reset-test")
            group.add_option(option)

        # by default, use 38400 baud
        if self.parser.has_option("--speed"):
            option = self.parser.get_option("--speed")
            option.default = 38400
            option.help = "change baud rate (default %s)" % option.default
            group = self.parser.get_option_group("--speed")
            self.parser.remove_option("--speed")
            group.add_option(option)


def main():
    # run the main application
    bsl_target = FCDProgTarget()
    bsl_target.main()

if __name__ == '__main__':
    main()
