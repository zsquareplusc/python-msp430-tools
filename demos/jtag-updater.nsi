;This NSIS installer script creates an application rather than an installer
;It extracts msp430-jtag to a temp location and runs it with a supplied
;binary (intel hex recomended, elf should work too) and flashes a MSP430
;processor connected at the parallel port JTAG adapter
;
;the giveio driver is loaded if needed or used and kept if already loaded.
;
;Requirements:
;NSIS and pyjtag needs to be installed.
;tested with NSIS 2.0b3 and install-pyjtag-20040102.exe
;
;(C)2004 Chris Liechti <cliechti@gmx.net>
;
;Python style license. In short, you can use this product in commercial
;and non-commercial applications, modify it, redistribute it.


!define GIVEIO $1       ;flag

;User options, project specific
!define IMAGE_DIR       "..\..\examples\leds"   ;location of the image file
!define IMAGE           "leds.a43"              ;name of the image file
!define JTAGOPTIONS     "-e"                    ;options to msp430-jtag
!define MSPGCCBIN       "C:\mspgcc\bin"         ;location of msp430-jtag
OutFile                 "updater.exe"           ;The file to write the installer to
Name                    "Firmware updater"      ;The name of the installer
LicenseData             "readme.txt"            ;readme file
!define COPYRIGHT       "JTAG Firmware Updater (C)2004 Chris Liechti <cliechti@gmx.net>"
;Icon                    "icon.ico"              ;custom installer icon

;Other Definitions, usualy not needed to change
!include "Sections.nsh"                 ;section flags definitions
ShowInstDetails show                    ;display log texts
InstType /COMPONENTSONLYONCUSTOM        ;no install type selection
InstallDir "$TEMP\jtag_updater"         ;The default installation directory
LicenseText "Readme" "Next >"           ;Texts on the dialogs
SubCaption 0 ": Readme"                 ;License Agreement page title
SubCaption 3 ": Download"               ;Installing Files page title

;Order of pages, other pages are not shown
Page license                            ;used as readme page
Page instfiles                          ;where the work is done

Section "Download Firmware" mand_sec_exp
    SectionIn 1
    DetailPrint "${COPYRIGHT}"
    
    ; see if giveio driver is needed and load it
    Call LoadGiveio
    Pop $0
    IntCmp $0 0 0 giveio_err giveio_err ;if not 0 -> error
    
    ; wait until the user says we're ready
    MessageBox MB_YESNO|MB_ICONEXCLAMATION \
                'Connect target the parallel port JTAG adapter.$\n\
                Press Yes to update the product or No to abort.'\
                IDYES do_download
    DetailPrint "User aborted."
    Abort
do_download:
    DetailPrint "Download..."
    ClearErrors
    nsExec::ExecToLog '"$INSTDIR\msp430-jtag" ${JTAGOPTIONS} "$INSTDIR\${IMAGE}"'
    Pop $0
    IntCmp $0 0 ext_ok
;ext_err:
    DetailPrint "An error occoured, could not write target."
    MessageBox MB_OK|MB_ICONSTOP "An error occoured, could not write target.$\nAborted."
    DetailPrint "Aborted"
    Abort
giveio_err:
    DetailPrint "Could not load parallel port driver giveio."
    MessageBox MB_OK|MB_ICONSTOP "Could not load parallel port driver giveio.$\nAborted."
    DetailPrint "Aborted"
    Abort
ext_ok:
SectionEnd


Function .onInit
    ;set up working directory
    ;$PLUGINSDIR will automatically be removed when the installer closes
    
    SetOutPath "$INSTDIR"
    File "${IMAGE_DIR}\${IMAGE}"
    File "${MSPGCCBIN}\msp430-jtag.exe"
    File "${MSPGCCBIN}\..\giveio\giveio.sys"
    File "${MSPGCCBIN}\..\giveio\loaddrv.exe"
    File "${MSPGCCBIN}\HIL.dll"
    File "${MSPGCCBIN}\python23.dll"
    File "${MSPGCCBIN}\MSP430mspgcc.dll"
    SetOutPath "$INSTDIR\lib"
    File "${MSPGCCBIN}\lib\shared-jtag.zip"
    ;~ File "${MSPGCCBIN}\lib\_parjtag.pyd"
    File "${MSPGCCBIN}\lib\_ctypes.pyd"
    File "${MSPGCCBIN}\lib\_sre.pyd"
    SetOutPath "$INSTDIR"
FunctionEnd

Function .onInstFailed
    Call UnloadGiveio
    Call Cleanup
FunctionEnd

Function .onInstSuccess
    Call UnloadGiveio
    Call Cleanup
FunctionEnd

Function .onUserAbort
    Call UnloadGiveio
    Call Cleanup
FunctionEnd

Function Cleanup
    ;Clean up working directory
    RMDir /r "$INSTDIR"
FunctionEnd


;helper functions

Function IsNT
  ; NT means anything based on NT - NT, 2000, or XP
  Push $0
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" CurrentVersion
  StrCmp $0 "" 0 IsNT_yes
  ; we are not running on NT.
  Pop $0
  Push 0
  Return
IsNT_yes:
    ; NT!!!
    Pop $0
    Push 1
FunctionEnd


Function LoadGiveio
    ; load giveio driver if needed (on NT platforms)
    ; result of load if it was laoded is flagged in the ${GIVEIO} variable
    ; its not touched if its already loaded
    Push "giveio error"                 ;assume failure
    
    Call IsNT                           ;check if NT based OS
    Pop $0                              ;get return value
    StrCmp $0 1 need_giveio             ;function retuns 1->NT else win9x
    Goto skip_giveio                    ;no need to load giveio on Win9x
need_giveio:
    DetailPrint "giveio required."
    ClearErrors
    ExecWait '"$INSTDIR\loaddrv" status giveio' $0
    IntCmp $0 0 got_giveio
    DetailPrint "giveio not found. trying to load driver..."

    nsExec::ExecToLog '$INSTDIR\loaddrv.exe install giveio $INSTDIR\giveio.sys'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 2 skip_giveio             ;assume its already installed
    IntCmp $0 0 0 giveio_err giveio_err ;if not 0 -> error
    nsExec::ExecToLog '$INSTDIR\loaddrv.exe start giveio'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 0 0 giveio_err giveio_err ;if not 0 -> error
    
    StrCpy ${GIVEIO} 1                  ;remember that we loaded giveio
    Goto skip_giveio
giveio_err:
    DetailPrint "Error while loading giveio service."
    MessageBox MB_OK|MB_ICONSTOP "Error while loading giveio service."
got_giveio:
    DetailPrint "giveio driver detected."
skip_giveio:
    Pop $0                              ;remove old result
    Push 0                              ;change result to "success"
FunctionEnd


Function UnloadGiveio
    ; unload giveio.sys if we have loaded it.
    ; the ${GIVEIO} variable says if we have loaded it.
    StrCmp ${GIVEIO} '' no_giveio       ;skip if giveio wasnt loaded by us
    nsExec::ExecToLog  '$INSTDIR\loaddrv.exe stop giveio'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 0 0 giveio_err giveio_err ;if not 0 -> error
    nsExec::ExecToLog '$INSTDIR\loaddrv.exe remove giveio'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 0 0 giveio_err giveio_err ;if not 0 -> error
    Goto giveio_ok
giveio_err:
    DetailPrint "Error while uninstalling giveio service."
    MessageBox MB_OK|MB_ICONSTOP "Error while uninstalling giveio service."
    Goto giveio_ok                      ;continue anyway
no_giveio:
    ;DetailPrint "giveio wasn't loaded"
giveio_ok:
FunctionEnd


