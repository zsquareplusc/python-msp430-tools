# example make file for the led demo

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# setting up the environment
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# set python path in case we're running from the original
# source repository
PYTHONPATH = ../../..
export PYTHONPATH

# set the assembler
AS = python -m msp430.asm.as
ASFLAGS = -x -v

# set up the linker
LD = python -m msp430.asm.ld
LDFLAGS = -v --mcu MSP430F5529

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# the rules used to build
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: clean all

all: clean led.txt
	cat led.txt


led.o4: led.S
led.txt: led.o4
	${LD} ${LDFLAGS} -o $@ $^

clean:
	rm -f led.txt led.o4

# pattern rule for the assembler
%o4: %S
	${AS} ${ASFLAGS} -o $@ $<

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# additional download rules
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: download-jtag download-bsl download-gdb
download-jtag: led.txt
	python -m msp430.jtag.target -e -l /opt/mspgcc/lib $^ --no-close -r
download-bsl: led.txt
	python -m msp430.bsl5.uart -e $^
download-usb: led.txt
	python -m msp430.bsl5.hid -e $^
download-gdb: led.txt
	python -m msp430.gdb.target -e $^
