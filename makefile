# $Id: makefile,v 1.1 2004/02/29 23:06:36 cliechti Exp $

PREFIX := /usr/local/msp430/bin

all:
	@echo "Nothing to do. "make install" will install the tools."

install:
	python setup.py install
	mkdir -p $(PREFIX)
	install msp430-bsl.py $(PREFIX)/msp430-bsl
	install msp430-jtag.py $(PREFIX)/msp430-jtag
