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
ASFLAGS = -v

# set up the linker
LD = python -m msp430.asm.ld
LDFLAGS = -v --mcu MSP430G2231 --symbols MSP430G2231

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# the rules used to build
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: clean all

all: clean led.titxt
	cat led.titxt


led.o4: led.S
led.titxt: led.o4
	${LD} ${LDFLAGS} -o $@ $^

clean:
	rm -f led.titxt led.o4

# pattern rule for the assembler
%o4: %S
	${AS} ${ASFLAGS} -o $@ $<

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# additional download rules
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: download-jtag download-bsl download-gdb
download-jtag: led.titxt
	python -m msp430.jtag.target -e -l /opt/mspgcc/lib $^ --no-close -r
download-bsl: led.titxt
	python -m msp430.bsl.target -e $^
download-gdb: led.titxt
	python -m msp430.gdb.target -e $^
download-mspdebug: led.titxt
	mspdebug rf2500 "prog $^" exit
