# example make file

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

all: clean demo.titext
#	$(CAT) demo.titext

clean:
	$(RM) demo.titext *.o4 demo.s-cpp demo.S \
	      startup.s-cpp \
	      intvec.s-cpp io.forth \
	      write.s-cpp putchar.S timer_a_uart_rx.S

# dependencies
demo.forth: io.forth

# linking final program
demo.titext: startup.o4 demo.o4 intvec.o4 write.o4 putchar.o4 timer_a_uart_rx.o4
	$(LD) $(LDFLAGS) -o $@ $^


# files generated from templates / other files
startup.s-cpp:
	$(LIB) -o $@ asm/startup.S
write.s-cpp:
	$(LIB) -o $@ asm/write.S
putchar.S:
	$(LIB) -o $@ asm/timer_a_uart/putchar_outmod.S
timer_a_uart_rx.S:
	$(LIB) -o $@ asm/timer_a_uart/receive_interrupt.S


io.forth:
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

download-jtag: demo.titext
	python -m msp430.jtag.target -e -l /opt/mspgcc/lib $^ --no-close -r

download-bsl: demo.titext
	python -m msp430.bsl.target -e $^

download-gdb: demo.titext
	python -m msp430.gdb.target -e $^

download-mspdebug: demo.titext
	mspdebug rf2500 "prog $^" exit

