#!/usr/bin/env python
# $Id: msp430-downloader.py,v 1.8 2006/04/11 18:35:23 cliechti Exp $
"""
Simple tool to download to a MSP430.

This one uses some dialog boxes, which makes it suitable for linking
file extensions to this program, so that a double click in the 
windoze exploder downloads the file.

(C) 2004 cliechti@gmx.net
"""

import os, sys
import EasyDialogs
import mspgcc.jtag, mspgcc.memory
from StringIO import StringIO
import traceback

name = 'msp430-downloader' #os.path.basename(os.path.splitext(sys.argv[0])[0])

if len(sys.argv) < 2:
    #~ EasyDialogs.Message("%s: Need a filename" % name)
    #~ sys.exit(1)
    filename = EasyDialogs.AskFileForOpen(
        windowTitle = "Select MSP430 binary for download",
        typeList=['*', 'elf', 'a43']
    )
    if filename is None:
        sys.exit(0)
else:
    filename = sys.argv[1]
lpt = '1'


#redirect console output
sys.stdout = sys.stderr = StringIO()

if EasyDialogs.AskYesNoCancel(
    "MSP430 downloader\n\nDownload '%s' using the JTAG interface?" % (filename,),
    cancel=""
) != 1:
    sys.exit(1)

#~ answer = EasyDialogs.AskYesNoCancel("Use JTAG or BSL?", 
    #~ default=1,yes="BSL", no="JTAG")
#~ if answer == 0: #NO -> JTAG
#~ elif answer == 1: #YES -> BSL
#~ else:   #CANCEL

class ProgressJTAG(msp430.jtag.JTAG):
    def progess_update(self, count, total):
        self.bar.set(100*count/total)

try:
    jtagobj = ProgressJTAG()
    jtagobj.showprogess = True
    jtagobj.bar = EasyDialogs.ProgressBar('Programming %r...' % filename, 100)
    showError = 0
    try:
        jtagobj.data = mspgcc.memory.Memory()   #prepare downloaded data
        jtagobj.data.loadFile(filename)         #autodetect filetype
        jtagobj.bar.label('Connecting...')
        jtagobj.open(lpt)                       #try to open port
        jtagobj.connect()                       #try to connect to target
        try:
            jtagobj.bar.label('Erasing...')
            answer = EasyDialogs.AskYesNoCancel("Choose erase mode",
                default=1, yes="ALL", no="Main only")
            if answer == 0: #NO
                jtagobj.actionMainErase()
            elif answer == 1: #YES
                jtagobj.actionMassErase()
            else:   #CANCEL
                sys.exit(0)
            showError = 1
            jtagobj.bar.label('Programming...')
            jtagobj.actionProgram()
        finally:
            if sys.exc_info()[:1]:              #if there is an exception pending
                jtagobj.verbose = 0             #do not write any more messages
            jtagobj.reset(1, 1)                 #reset and release target
            jtagobj.close()                     #Release communication port
    finally:
        del jtagobj.bar                         #close progress bar
except IOError, e:
    if showError:
        EasyDialogs.Message('An error occoured: "%s"\n\nMessages:\n%s' % (e, sys.stdout.getvalue()))
    else:
        EasyDialogs.Message("%s: Can't Connect to target" % name)
except (SystemExit, KeyboardInterrupt):
    raise
except Exception, e:
    #~ s = StringIO()
    #~ traceback.print_exc(file=s)
    #~ print s.getvalue()
    #~ EasyDialogs.Message(s.getvalue())
    EasyDialogs.Message('An error occoured: %s\nMessages:\n%s' % (e, sys.stdout.getvalue()))
else:
    messages = sys.stdout.getvalue()
    if messages:
        EasyDialogs.Message('Messages:\n%s\nSuccess!' % (messages,))