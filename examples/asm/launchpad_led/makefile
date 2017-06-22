# example make file for the led demo

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# setting up the environment
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# set Python path in case we're running from the original
# source repository
PYTHONPATH = ../../..
export PYTHONPATH

# options
ASFLAGS = -v
LDFLAGS = -v --mcu MSP430G2231 --symbols MSP430G2231

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# commands
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
PY = python
AS = $(PY) -m msp430.asm.as
LD = $(PY) -m msp430.asm.ld
RM = $(PY) -m msp430.shell.command rm -f
CAT = $(PY) -m msp430.shell.command cat

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# the rules used to build
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: clean all

all: clean led.titext
	$(CAT) led.titext

clean:
	$(RM) led.titext led.o4


led.o4: led.S
led.titext: led.o4
	$(LD) $(LDFLAGS) -o $@ $^

# pattern rule for the assembler
%o4: %S
	$(AS) $(ASFLAGS) -o $@ $<

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# additional download rules
#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
.PHONY: download-jtag download-bsl download-gdb

download-jtag: led.titext
	$(PY) -m msp430.jtag.target -e -l /opt/mspgcc/lib $^ --no-close -r

download-bsl: led.titext
	$(PY) -m msp430.bsl.target -e $^

download-gdb: led.titext
	$(PY) -m msp430.gdb.target -e $^

download-mspdebug: led.titext
	mspdebug rf2500 "prog $^" exit
