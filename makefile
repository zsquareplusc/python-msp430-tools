
PREFIX := /usr/local/msp430/bin

all:
	@echo "Nothing to do. \"make install\" will install the tools."

install:
	python setup.py install
	mkdir -p $(PREFIX)
	install scripts/msp430-convert.py $(PREFIX)/msp430-convert
	install scripts/msp430-compare.py $(PREFIX)/msp430-compare
	install scripts/msp430-hexdump.py $(PREFIX)/msp430-hexdump
	install scripts/msp430-generate.py $(PREFIX)/msp430-generate
	install scripts/msp430-gdb.py $(PREFIX)/msp430-gdb-dl
	install scripts/msp430-bsl.py $(PREFIX)/msp430-bsl
	install scripts/msp430-bsl-legacy.py $(PREFIX)/msp430-bsl-legacy
	install scripts/msp430-jtag.py $(PREFIX)/msp430-jtag
	install scripts/msp430-jtag-legacy.py $(PREFIX)/msp430-jtag-legacy
	install scripts/msp430-ram-usage.py $(PREFIX)/msp430-ram-usage


# Sphinx docs
doc-html:
	cd doc; $(MAKE) html

doc-pdf:
	cd doc; $(MAKE) latex
	cd doc/_build/latex; $(MAKE)

doc-clean:
	cd doc; $(MAKE) clean

doc-auto:
	python -m msp430.shell.watch doc/*.rst -x "make doc-html"

.PHONY: FORCE
