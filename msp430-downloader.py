"""
Simple tool to download stuff to a MSP430.

This one uses some dialog boxes, which makes it suitable for linking
file extensions to this program, so that a double click in the 
winoze exploder downloads the file.

(C) 2004 cliechti@gmx.net
"""

import os, sys
import EasyDialogs
import msp430.jtag, msp430.memory
from StringIO import StringIO
import traceback

name = 'msp430-downloader' #os.path.basename(os.path.splitext(sys.argv[0])[0])

if len(sys.argv) < 2:
    EasyDialogs.Message("%s: Need a filename" % name)
    sys.exit(1)
filename = sys.argv[1]
lpt = '1'



if EasyDialogs.AskYesNoCancel(
    "Download '%s' with JTAG?" % filename,
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
    try:
        jtagobj.data = msp430.memory.Memory()   #prepare downloaded data
        jtagobj.data.loadFile(filename)         #autodetect filetyoe
        jtagobj.bar.label('Connecting...')
        jtagobj.connect(lpt)                    #try to open port
        try:
            jtagobj.bar.label('Erasing...')
            #~ jtagobj.actionMainErase()
            jtagobj.actionMassErase()
            jtagobj.bar.label('Programming...')
            jtagobj.actionProgram()
        finally:
            jtagobj.reset(1, 1)                 #reset and release target
            jtagobj.close()                     #Release communication port
    finally:
        del jtagobj.bar
except IOError:
    EasyDialogs.Message("%s: Can't Connect to target" % name)
except:
    s = StringIO()
    traceback.print_exc(file=s)
    print s.getvalue()
    EasyDialogs.Message(s.getvalue())
