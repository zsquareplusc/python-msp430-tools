# $Id: makefile,v 1.2 2004/03/01 02:36:37 cliechti Exp $

PREFIX := /usr/local/msp430/bin

all:
	@echo "Nothing to do. "make install" will install the tools."

install:
	python setup.py install
	mkdir -p $(PREFIX)
	install msp430-bsl.py $(PREFIX)/msp430-bsl
	install msp430-jtag.py $(PREFIX)/msp430-jtag


#generate test files
testfiles: fill60k.a43 fill48k.a43 fill32k.a43 fill16k.a43 fill8k.a43 fill4k.a43

fill60k.a43:
	python gen-ihex.py 60 >$@
fill48k.a43:
	python gen-ihex.py 48 >$@
fill32k.a43:
	python gen-ihex.py 32 >$@
fill16k.a43:
	python gen-ihex.py 16 >$@
fill8k.a43:
	python gen-ihex.py 8 >$@
fill4k.a43:
	python gen-ihex.py 4 >$@
