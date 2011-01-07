;This NSIS installer script creates an application rather than an installer
;It extracts msp430-bsl to a temp location and runs it with a supplied
;binary (intel hex recomended, elf should work too) and flashes a MSP430
;processor connected at the parallel port JTAG adapter
;
;Requirements:
;NSIS and pybsl needs to be installed.
;tested with NSIS 2.0b3 and install-pybsl-20040102.exe
;
;The COM port selection is configured in the ini file.
;
;(C)2004 Chris Liechti <cliechti@gmx.net>
;
;Python style license. In short, you can use this product in commercial
;and non-commercial applications, modify it, redistribute it.


;User options, project specific
!define IMAGE_DIR       "..\..\examples\leds"   ;location of the image file
!define IMAGE           "leds.a43"              ;name of the image file
!define BSLOPTIONS      "-e"                    ;options to msp430-bsl
!define MSPGCCBIN       "C:\mspgcc\bin"         ;location of msp430-bsl
OutFile                 "updater.exe"           ;The file to write the installer to
Name                    "Firmware updater"      ;The name of the installer
LicenseData             "readme.txt"            ;readme file
!define COPYRIGHT       "BSL Firmware Updater (C)2004 Chris Liechti <cliechti@gmx.net>"
!define BSLHINTS        "Make sure that the 'BSL update' jumper is set.$\n"
;Icon                    "icon.ico"              ;custom installer icon

;Other Definitions, usualy not needed to change
!include "Sections.nsh"                 ;section flags definitions
ShowInstDetails show                    ;display log texts
InstType /COMPONENTSONLYONCUSTOM        ;no install type selection
InstallDir "$TEMP\bsl_updater"          ;The default installation directory
LicenseText "Readme" "Next >"           ;Texts on the dialogs
SubCaption 0 ": Readme"                 ;License Agreement page title
SubCaption 3 ": Download"               ;Installing Files page title
ReserveFile "${NSISDIR}\Plugins\InstallOptions.dll"
ReserveFile "bsl-updater.ini"

!define PORT    $7

;Order of pages, other pages are not shown
Page license                            ;used as readme page
Page custom SetCustom                   ;Custom page. InstallOptions gets called in SetCustom.
Page instfiles                          ;where the work is done

Section "Download Firmware" mand_sec_exp
    SectionIn 1
    DetailPrint "${COPYRIGHT}"
    
    ;Get Install Options dialog user input
    ReadINIStr ${PORT} "$PLUGINSDIR\bsl-updater.ini" "Field 2" "State"

    ; wait until the user says we're ready
    MessageBox MB_YESNO|MB_ICONEXCLAMATION \
                "Connect target the serial port ${PORT}.$\n${BSLHINTS}$\n\
                Press Yes to update the product or No to abort."\
                IDYES do_download
    DetailPrint "User aborted."
    Abort
do_download:
    DetailPrint "Download on ${PORT}..."
    ClearErrors
    nsExec::ExecToLog '"$INSTDIR\msp430-bsl" ${BSLOPTIONS} -c ${PORT} "$INSTDIR\${IMAGE}"'
    Pop $0
    IntCmp $0 0 ext_ok
;ext_err:
    DetailPrint "An error occoured, could not write target."
    MessageBox MB_OK|MB_ICONSTOP "An error occoured, could not write target.$\nAborted."
    DetailPrint "Aborted"
    Abort
ext_ok:
SectionEnd


Function .onInit
    ;set up working directory
    ;$PLUGINSDIR will automatically be removed when the installer closes
    InitPluginsDir
    File /oname=$PLUGINSDIR\bsl-updater.ini "bsl-updater.ini"
    
    SetOutPath "$INSTDIR"
    File "${IMAGE_DIR}\${IMAGE}"
    File "${MSPGCCBIN}\msp430-bsl.exe"
    File "${MSPGCCBIN}\python23.dll"
    SetOutPath "$INSTDIR\lib"
    File "${MSPGCCBIN}\lib\_sre.pyd"
    File "${MSPGCCBIN}\lib\PyWinTypes23.dll"
    File "${MSPGCCBIN}\lib\shared-bsl.zip"
    File "${MSPGCCBIN}\lib\select.pyd"
    File "${MSPGCCBIN}\lib\win32event.pyd"
    File "${MSPGCCBIN}\lib\win32file.pyd"
    SetOutPath "$INSTDIR"
FunctionEnd

Function .onInstFailed
    Call Cleanup
FunctionEnd

Function .onInstSuccess
    Call Cleanup
FunctionEnd

Function .onUserAbort
    Call Cleanup
FunctionEnd

Function Cleanup
    ;Clean up working directory
    RMDir /r "$INSTDIR"
FunctionEnd

;helpers
Function SetCustom
    ;Display the InstallOptions dialog
    Push $R0
        InstallOptions::dialog "$PLUGINSDIR\bsl-updater.ini"
        Pop $R0
    Pop $R0
FunctionEnd
