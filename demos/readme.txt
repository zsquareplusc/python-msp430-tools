+--------------------------------------------------------+
!  This file is displayed on startup of the installer.   !
!  And is used here as a short description.              !
+--------------------------------------------------------+
whats this
----------

two NSIS scripts, used to build executables that provide a
simple GUI for msp430-jtag or msp430-bsl programmers
not installers in the common sense are created, but
executales that extract the required files, program, and
clean up afterwards.

these exectables can be useful for field updates of msp430
based products.

short instructions
------------------
(there are no long instructions ;-)

- install NSIS (Nullsoft installer creator):
  http://prdownloads.sourceforge.net/nsis/nsis20.exe?download
  it will associate the .nsi ending to its tool. you can then
  rightclick nsi files to run "makensis", which interprets
  these files and build the installer exe.

- install mspgcc, the installer contains the complete
  toolchain but also msp430-jtag and the giveio driver which
  you want:
  http://prdownloads.sourceforge.net/mspgcc/mspgcc-20040602.exe?download

- get the installer project files from here (where this file
  comes from):
  http://cvs.sourceforge.net/viewcvs.py/mspgcc/python/demos/

- copy a .a43 file (intel hex format) to the project directory,
  edit the defines in jtag-updater.nsi, so that it references
  your .a43 and your file descriptions. you must also provide
  a readme.txt in the same directory.

- run makensis on jtag-updater.nsi (right click file in the
  windows explorer, the popup menu should have entries for that)

the resulting executable detects the presence of the giveio
driver (used for parallel port access) and loads (and removes)
it if needed, that way you shouldn't have problems using the
tool on NT/Xp/2k, but the user that runs the exe needs Admin
privileges to install that driver and access the parallel port.

the bsl-* files can be used to build a similar executable for
the serial bootstraploader. the BSL has the advantage that it
works with a simple serial port (incl. USB<->serial converters)
and no special drivers.
the parallel port on some laptops are not compatible with the
JTAG interface and you dont need extra hardware (but serial port
interfacing on in your product)

files
-----

bsl-updater.ini         dialog for the serial port selection,
                        used by bsl-updater.nsi

bsl-updater.nsi         NSIS script to build the msp430-bsl
                        based executable

jtag-updater.nsi        NSIS script to build the msp430-jtag
                        based executable

readme.txt              this help text and also the readme used
                        in the executables built with the scripts
                        from above
