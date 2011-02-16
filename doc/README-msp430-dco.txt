msp430-dco
===========

MSP430 clock calibration utility.


Features
--------

- can handle F1xx, F2xx and F4xx devices, with or without external
  Rsel resistor
- measure calibration values for a given frequency
- restore calibration values of F2xx devices
- selectable clock tolerance
- can write measured values to the target flash, output C code or #defines


Requirements
------------
- Linux, BSD, Un*x or Windows PC
- Python 2.5 or newer
- Parallel JTAG hardware with an MSP430 device connected
  (currently only the parallel port adapter with the MSP430mspgcc library
  is supported)


Short introduction
------------------
This software uses the JTAG hardware that comes with the FET kits. It is
connected to the parallel port.

The program can be started by typing ``msp430-dco`` when installed correctly
If it's used from the source directory use ``python -m msp430.jtag.dco``.


Usage: msp430.jtag.dco [options] frequency

MSP430 clock calibration utility V1.1

This tool can measure the internal oscillator of F1xx, F2xx and F4xx devices,
display the supported frequencies, or run a software FLL to find the settings
for a specified frequency.

The target device has to be connected to the JTAG interface.

Examples:
  See min and max clock speeds:
    dco.py --measure

  Get clock settings for 2.0MHz +/-1%:
    dco.py --tolerance=0.01 2.0e6

  Write clock calibration for 1.5MHz to the information memory at 0x1000:
    dco.py 1.5e6 BCSCTL1@0x1000 DCOCTL@0x1000

Use it at your own risk. No guarantee that the values are correct.

Options:
  -h, --help            show this help message and exit
  -o FILE, --output=FILE
                        write result to given file
  --dcor                use external resistor
  -d, --debug           print debug messages
  -l LPT, --lpt=LPT     set the parallel port
  -m, --measure         measure min and max clock settings and exit
  -c, --calibrate       Restore calibration values on F2xx devices
  -t TOLERANCE, --tolerance=TOLERANCE
                        set the clock tolerance as factor. e.g. 0.01 means 1%
                        (default=0.005)
  --define              output #defines instead of assignments
  --erase=ERASE         erase flash page at given address. Use with care!


Variables
---------

Arguments in the form ``variable@address`` are used to write the corresponding
values to the target device.
Variable names are case insensitive, addresses can be specified in decimal,
octal or hexadecimal format.

The available variables depend on the target type and executed operation.
All variables that are written all caps in the table below are in
``unsigned char`` format, others in ``unsigned short`` format. The later
should be written to even addresses only, as the code reading these values
could have problems otherwise.

Frequencies are in kHz.

    +-------------+------+-------------------------------------------------+
    | *Operation* | *MCU*| *Variables*                                     |
    +-------------+------+-------------------------------------------------+
    | frequency   | F1xx | BCSCTL1 BCSCTL2 DCOCTL freq                     |
    +             +------+-------------------------------------------------+
    |             | F2xx | BCSCTL1 BCSCTL2 DCOCTL freq                     |
    +             +------+-------------------------------------------------+
    |             | F4xx | SCFI0 SCFI1 SCFQCTL FLL_CTL0 FLL_CTL1 freq      |
    +-------------+------+-------------------------------------------------+
    | --measure   | F1xx | fmax fmin                                       |
    |             |      | rsel0_fmax rsel0_fmin rsel1_fmax rsel1_fmin     |
    |             |      | rsel2_fmax rsel2_fmin rsel3_fmax rsel3_fmin     |
    |             |      | rsel4_fmax rsel4_fmin rsel5_fmax rsel5_fmin     |
    |             |      | rsel6_fmax rsel6_fmin rsel7_fmax rsel7_fmin     |
    +             +------+-------------------------------------------------+
    |             | F2xx | fmax fmin                                       |
    |             |      | rsel0_fmax rsel0_fmin rsel1_fmax rsel1_fmin     |
    |             |      | rsel2_fmax rsel2_fmin rsel3_fmax rsel3_fmin     |
    |             |      | rsel4_fmax rsel4_fmin rsel5_fmax rsel5_fmin     |
    |             |      | rsel6_fmax rsel6_fmin rsel7_fmax rsel7_fmin     |
    |             |      | rsel8_fmax rsel8_fmin rsel9_fmax rsel9_fmin     |
    |             |      | rsel10_fmax rsel10_fmin rsel11_fmax rsel11_fmin |
    |             |      | rsel12_fmax rsel12_fmin rsel13_fmax rsel13_fmin |
    |             |      | rsel14_fmax rsel14_fmin rsel15_fmax rsel15_fmin |
    +             +------+-------------------------------------------------+
    |             | F4xx | fmax fmin                                       |
    +-------------+------+-------------------------------------------------+
    | --calibrate | F1xx | *not supported*                                 |
    +             +------+-------------------------------------------------+
    |             | F2xx | f16MHz_dcoctl f16MHz_bcsctl1                    |
    |             |      | f12MHz_dcoctl f12MHz_bcsctl1                    |
    |             |      | f8MHz_dcoctl f8MHz_bcsctl1                      |
    |             |      | f1MHz_dcoctl f1MHz_bcsctl1                      |
    +             +------+-------------------------------------------------+
    |             | F4xx | *not supported*                                 |
    +-------------+------+-------------------------------------------------+


When the ``msp430-dco`` tool is run with the ``--debug`` option it provides
an output with all the possible variables and their values.


Examples
--------
``msp430-dco 2.5e6``
    Print the calibration values for 2.5MHz

``msp430-dco 2.5e6 --define``
    Same as above, but format the output as defines usable for C include files.

``msp430-dco 1e6 --erase 0x1000 BCSCTL1@0x1000 DCOCTL@0x1001``
    Measure calibration values for 1MHz, then erase the information memory
    flash page at 0x1000. These values are then written to the flash at
    0x1000 and 0x1001.

    This can be useful in combination with firmware downloads. For example
    make a mass erase, write firmware, then write clock calibration for this
    device::

        msp430-jtag -e my_firmware.elf
        msp430-dco 1e6 BCSCTL1@0x1000 DCOCTL@0x1001

    The firmware can then read the values from the flash and configure the
    Basic Clock System using these values.

``msp430-dco --measure``
    Print frequency ranges of all DCO settings as well as minimal and maximal
    values. (Note: restricted functionality on F4xx devices)

``msp430-dco --calibrate``
    Recalculate the calibration values for 16MHz, 12MHz, 8MHz and 1MHz
    that are available in the information memory at 0x10f8-0x10ff.
    This is only possible for F2xx devices.


Known Issues
------------
The algorithm does not search for the best match, it stops when the frequency
is within the window. Therefore it's not unlikely that the frequency is at the
border of the tolerance window and not in the center.


History
-------
V1.0
    Public release.

V1.1
    Can write values to target flash


References
----------
- Python: http://www.python.org

- Texas Instruments MSP430 homepage, links to data sheets and application
  notes: http://www.ti.com/msp430

