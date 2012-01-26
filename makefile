
all:
	@echo "Nothing to do."
	@echo "Use setup.py to build and or install the python module."
	@echo "Make targets: doc-html doc-pdf doc-clean"

install:
	python setup.py install


# Sphinx docs
doc-html:
	cd doc; $(MAKE) html

doc-pdf:
	cd doc; $(MAKE) latex
	cd doc/_build/latex; $(MAKE)

doc-clean:
	cd doc; $(MAKE) clean

# This watches the file for changes and triggers rebuilds automatically on edits.
doc-auto:
	python -m msp430.shell.watch doc/*.rst -x "make doc-html"

.PHONY: FORCE
