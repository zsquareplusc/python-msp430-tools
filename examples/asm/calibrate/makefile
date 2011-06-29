# example make file for the calibrate demo

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# setting up the environment
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# set Python path in case we're running from the original
# source repository
PYTHONPATH = ../../..
export PYTHONPATH

# options
ASFLAGS = 
LDFLAGS = -v --mcu MSP430G2231
#~ LDFLAGS = -v --mcu MSP430G2231 --symbols MSP430G2231
CPPFLAGS = -D_GNU_ASSEMBLER_ -D__ASSEMBLER__ -D__MSP430G2132__

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# commands
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CPP = python -m msp430.asm.cpp
AS = python -m msp430.asm.as
LD = python -m msp430.asm.ld
RM = python -m msp430.shell.command rm -f
CAT = python -m msp430.shell.command cat
DIS = python -m msp430.asm.disassemble

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# the rules used to build
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: clean all

all: clean calibrate.titext
	$(CAT) calibrate.titext

clean:
	$(RM) calibrate.titext calibrate.o4 calibrate.s-cpp


calibrate.o4: calibrate.S
calibrate.titext: calibrate.o4
	$(LD) $(LDFLAGS) -o $@ $^

# pattern rules for the assembler
%o4: %s-cpp
	$(AS) $(ASFLAGS) -o $@ $<

%s-cpp: %S
	${CPP} ${CPPFLAGS} -o $@ $<

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# additional download rules
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: download-jtag download-bsl download-gdb

download-jtag: calibrate.titext
	python -m msp430.jtag.target -p TIUSB -e  $^ --spy-bi-wire

download-bsl: calibrate.titext
	python -m msp430.bsl.target -e $^

download-gdb: calibrate.titext
	python -m msp430.gdb.target -e $^

download-mspdebug: calibrate.titext
	mspdebug rf2500 "prog $^" exit

download: download-jtag