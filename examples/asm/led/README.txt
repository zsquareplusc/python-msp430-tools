LED
===

Minimalistic assembler program that can be used to test the assembler and
download tools.

This version uses the peripherals (WDT, PORT1) of a 1xx, 2xx, 4xx or
ValueLine device (not compatiple with 5xx/6xx).


Function
--------
This one toggles the pin P1.0.


Building
--------
Assembling and linking::

    python -m msp430.asm.as -o led.o4 led.S
    python -m msp430.asm.ld --mcu MSP430G2121 -o led.titxt led.o4


Usage
-----
This is like the LED flashing example that comes preprogrammed on some of the
eval boards from TI. The eval boards from TI typically have a LED connected to
the pin P1.0.

Download::

    python -m msp430.bsl.target -e led.txt

The download could also be made with msp430.jtag.target or msp430.gdb.target

