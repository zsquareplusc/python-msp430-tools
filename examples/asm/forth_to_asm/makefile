# example make file for the led demo

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# setting up the environment
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# set Python path in case we're running from the original
# source repository
PYTHONPATH = ../../..
export PYTHONPATH

# options
MCU = msp430g2231
ASFLAGS =
LDFLAGS = -v --mcu $(MCU)
CPPFLAGS = 
FORTHFLAGS = -DMCU=$(MCU)
H2FORTHFLAGS = $(CPPFLAGS)

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# commands
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CPP = python -m msp430.asm.cpp
AS = python -m msp430.asm.as
LD = python -m msp430.asm.ld
FORTH = python -m msp430.asm.forth
H2FORTH = python -m msp430.asm.h2forth
LIB = python -m msp430.asm.lib

RM = python -m msp430.shell.command rm -f
CAT = python -m msp430.shell.command cat
DIS = python -m msp430.asm.disassemble

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# the rules used to build
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: clean all

all: clean led.titext led.S
#	$(CAT) led.titext

clean:
	$(RM) led.titext led.o4 led.s-cpp led.S \
	      startup.o4 startup.s-cpp \
	      intvec16.S intvec16.o4 intvec.s-cpp msp430.forth

# dependencies
led.forth: msp430.forth

# linking final program
led.titext: startup.o4 led.o4 intvec16.o4
	$(LD) $(LDFLAGS) -o $@ $^

# files generated from templates / other files
startup.s-cpp:
	$(LIB) -o $@ asm/startup.S
intvec16.S:
	$(LIB) -o $@ asm/intvec16.S

msp430.forth:
	$(H2FORTH) $(H2FORTHFLAGS) -o $@ $(MCU).h

# pattern rules for the assembler
%o4: %s-cpp
	$(AS) $(ASFLAGS) -o $@ $<

%s-cpp: %S
	${CPP} ${CPPFLAGS} -o $@ $<

%S: %forth
	${FORTH} ${FORTHFLAGS} -o $@ $<
#	$(CAT) $@

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# additional download rules
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: download-jtag download-bsl download-gdb

download-jtag: led.titext
	python -m msp430.jtag.target -e -l /opt/mspgcc/lib $^ --no-close -r

download-bsl: led.titext
	python -m msp430.bsl.target -e $^

download-gdb: led.titext
	python -m msp430.gdb.target -e $^

download-mspdebug: led.titext
	mspdebug rf2500 "prog $^" exit
