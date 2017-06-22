# example make file for the led demo

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# setting up the environment
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# set python path in case we're running from the original
# source repository
PYTHONPATH = ../../..
export PYTHONPATH

PY = python

# set the assembler
AS = $(PY) -m msp430.asm.as
ASFLAGS = -x -v

# set up the linker
LD = $(PY) -m msp430.asm.ld
LDFLAGS = -v --mcu MSP430F5529

RM = $(PY) -m msp430.shell.command rm -f

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
	${RM} led.txt led.o4

# pattern rule for the assembler
%o4: %S
	${AS} ${ASFLAGS} -o $@ $<

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# additional download rules
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: download-jtag download-bsl download-gdb
download-jtag: led.txt
	$(PY) -m msp430.jtag.target -e -l /opt/mspgcc/lib $^ --no-close -r
download-bsl: led.txt
	$(PY) -m msp430.bsl5.uart -e $^
download-usb: led.txt
	$(PY) -m msp430.bsl5.hid -e $^
download-gdb: led.txt
	$(PY) -m msp430.gdb.target -e $^
