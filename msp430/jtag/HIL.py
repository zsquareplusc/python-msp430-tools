#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Python bindings to the functions in the MSP430 JTAG HIL
(Hardware Interface Library)
 
Requires Python 2+, ctypes and HIL.dll/libHIL.so
"""

import ctypes

HIL = ctypes.windll.HIL

Initialize          = HIL.HIL_Initialize
Initialize.argtypes = [ctypes.c_char_p]
Initialize.restype  = ctypes.c_int
Open                = HIL.HIL_Open
Open.argtypes       = []
Open.restype        = ctypes.c_int
Connect             = HIL.HIL_Connect
Connect.argtypes    = []
Connect.restype     = ctypes.c_int
Release             = HIL.HIL_Release
Release.argtypes    = []
Release.restype     = ctypes.c_int
Close               = HIL.HIL_Close
Close.argtypes      = [ctypes.c_long]
Close.restype       = ctypes.c_int
JTAG_IR             = HIL.HIL_JTAG_IR
JTAG_IR.argtypes    = [ctypes.c_long]
JTAG_IR.restype     = ctypes.c_long
TEST_VPP            = HIL.HIL_TEST_VPP
TEST_VPP.argtypes   = [ctypes.c_long]
TEST_VPP.restype    = ctypes.c_long
JTAG_DR             = HIL.HIL_JTAG_DR
JTAG_DR.argtypes    = [ctypes.c_long, ctypes.c_long]
JTAG_DR.restype     = ctypes.c_long
VCC                 = HIL.HIL_VCC
VCC.argtypes        = [ctypes.c_long]
VCC.restype         = ctypes.c_int
TST                 = HIL.HIL_TST
TST.argtypes        = [ctypes.c_long]
TST.restype         = ctypes.c_int
TCK                 = HIL.HIL_TCK
TCK.argtypes        = [ctypes.c_long]
TCK.restype         = ctypes.c_int
TMS                 = HIL.HIL_TMS
TMS.argtypes        = [ctypes.c_long]
TMS.restype         = ctypes.c_int
TDI                 = HIL.HIL_TDI
TDI.argtypes        = [ctypes.c_long]
TDI.restype         = ctypes.c_int
TCLK                = HIL.HIL_TCLK
TCLK.argtypes       = [ctypes.c_long]
TCLK.restype        = ctypes.c_int
RST                 = HIL.HIL_RST
RST.argtypes        = [ctypes.c_long]
RST.restype         = ctypes.c_int
VPP                 = HIL.HIL_VPP
VPP.argtypes        = [ctypes.c_long]
VPP.restype         = ctypes.c_int
DelayMSec           = HIL.HIL_DelayMSec
DelayMSec.argtypes  = [ctypes.c_ulong]
DelayMSec.restype   = ctypes.c_int
StartTimer          = HIL.HIL_StartTimer
StartTimer.argtypes = []
StartTimer.restype  = ctypes.c_int
ReadTimer           = HIL.HIL_ReadTimer
ReadTimer.argtypes  = []
ReadTimer.restype   = ctypes.c_ulong
StopTimer           = HIL.HIL_StopTimer
StopTimer.argtypes  = []
StopTimer.restype   = ctypes.c_int
ReadTDO             = HIL.HIL_ReadTDO
ReadTDO.argtypes    = []
ReadTDO.restype     = ctypes.c_long

if __name__ == '__main__':
    Initialize('1')
    Connect()
    VCC(3000)
    
    #~ HIL_TST(1)
    #~ HIL_DelayMSec(1000)
    #~ HIL_TST(0)
    
    #~ HIL_TCK(1)
    #~ HIL_TDI(1)
    
    #~ for i in range(3):
        #~ HIL_DelayMSec(100)
        #~ HIL_TMS(1)
        #~ HIL_DelayMSec(100)
        #~ HIL_TMS(0)

    JTAG_DR(0x1234, 16)
    
    Release()
    Close(1)
