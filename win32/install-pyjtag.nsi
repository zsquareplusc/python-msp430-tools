; This creates an installer for the msp430-jtag.exe
; using NSIS.sf.net version 2.0

!define MSPGCC        "C:\mspgcc"         ;location of mspgcc


!define SF_SELECTED   1
!define SF_SUBSEC     2
!define SF_SUBSECEND  4
!define SF_BOLD       8
!define SF_RO         16
!define SF_EXPAND     32

!define SECTION_OFF   0xFFFFFFFE

LicenseData ..\license.txt

SetOverwrite on
SetCompressor bzip2

ShowInstDetails show

ShowUninstDetails show

SetDateSave on

; -------------
!include "MUI.nsh"

!define MUI_PRODUCT "MSPGCC JTAG"
!define MUI_VERSION "20040108"

!define MUI_NAME "MSPGCC install-pyjtag ${MUI_VERSION}"

!define MUI_WELCOMEPAGE
!define MUI_LICENSEPAGE
!define MUI_COMPONENTSPAGE
!define MUI_DIRECTORYPAGE
!define MUI_FINISHPAGE
  !define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\docs\README-pyjtag.txt"
  !define MUI_FINISHPAGE_NOREBOOTSUPPORT
!define MUI_ABORTWARNING
  
!define MUI_UNINSTALLER
!define MUI_UNCONFIRMPAGE
;!define MUI_SPECIALBITMAP "${NSISDIR}\Contrib\Icons\modern-wizard.bmp"
!define MUI_SPECIALBITMAP "..\..\packaging\msp430-image.bmp"
;!define MUI_UI "${NSISDIR}\Contrib\UIs\modern_headerbmp.exe"
!define MUI_UI "${NSISDIR}\Contrib\UIs\modern.exe"

OutFile "install-pyjtag-${MUI_VERSION}.exe"

;Modern UI System

;!insertmacro MUI_SYSTEM
;--------------------------------
;Language Strings

; The default installation directory
InstallDir $PROGRAMFILES\mspgcc
; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM SOFTWARE\mspgcc "rootdir"

  ;Descriptions
  LangString DESC_SecJTAG ${LANG_ENGLISH} "Command line JTAG programmer."
  LangString DESC_SecGiveio ${LANG_ENGLISH} "IO support, required only on Win NT, 2k, XP."

!define MUI_TEXT_WELCOME_INFO_TEXT "This wizard will guide you through the installation of MSPGCC.\r\n\r\n\
    MSPGCC is a port of the GNU tools for the Texas Instruments MSP430 family of ultra-low power MCUs. It \
    provides a full development and debugging environment for assembly and C language programming. \r\n\r\n\
    This software is free and unrestricted for use in the development of any kind of software for \
    the MSP430 processors. All current processor models are supported. \
    \r\n\r\n\r\n"

!insertmacro MUI_LANGUAGE "English"

; -------------
;Reserve Files
  
;!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS
;!insertmacro MUI_RESERVEFILE_SPECIALINI
!insertmacro MUI_RESERVEFILE_SPECIALBITMAP
; -------------


Section "msp430-jtag (required)" SecJTAG
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    File /r ..\bin
    SetOutPath "$INSTDIR\docs"
    File /oname=LICENSE-pyjtag.txt      ..\license.txt
    File ..\README-msp430-jtag.txt
    SetOutPath "$INSTDIR"
    ;~ File /oname=bin\jtag.py                  jtag.py

    ; Write the installation path into the registry
    WriteRegStr HKLM SOFTWARE\mspgcc "rootdir" "$INSTDIR"
    ; Write the uninstall keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\mspgcc-pyjtag" "DisplayName" "mspgcc pyjtag (remove only)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\mspgcc-pyjtag" "UninstallString" '"$INSTDIR\uninstall-pyjtag.exe"'
    WriteUninstaller "uninstall-pyjtag.exe"
SectionEnd

Section "giveio (needed on Win NT/2k/XP, but NOT on 9x/ME)" SecGiveio
    SetOutPath "$INSTDIR\bin"
    File ${MSPGCC}\giveio\giveio.sys
    File ${MSPGCC}\giveio\loaddrv.exe
    SetOutPath "$INSTDIR"
    nsExec::ExecToLog '$INSTDIR\bin\loaddrv.exe install giveio $INSTDIR\bin\giveio.sys'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 2 ext_here                ;assume its alredy installed
    IntCmp $0 0 0 ext_err ext_err       ;if not 0 -> error
    nsExec::ExecToLog '$INSTDIR\bin\loaddrv.exe start giveio'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 0 0 ext_err ext_err       ;if not 0 -> error
    nsExec::ExecToLog '$INSTDIR\bin\loaddrv.exe starttype giveio auto'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 0 0 ext_err ext_err       ;if not 0 -> error
    WriteRegStr HKLM SOFTWARE\mspgcc "giveio" "started"
    Goto ext_ok
ext_err:
    DetailPrint "Error while installing and starting giveio"
    MessageBox MB_OK|MB_ICONSTOP "Error while installing and starting giveio"
    Goto ext_ok
ext_here:
    DetailPrint "Installing giveio gave an error, assuming its already installed"
ext_ok:
SectionEnd

; special uninstall section.
Section "Uninstall"
    ; remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\mspgcc-pyjtag"
    ;~ DeleteRegKey HKLM SOFTWARE\mspgcc
    ; remove files
    Delete "$INSTDIR\bin\msp430-jtag.exe"
    Delete "$INSTDIR\bin\_parjtag.pyd"
    Delete "$INSTDIR\bin\jtag.py"
    ;~ Delete $INSTDIR\bin\HIL.dll
    ;~ Delete $INSTDIR\bin\MSP430mspgcc.dll
    ;XXX python22.dll is left installed as it is used by pybsl and other tools
    Delete "$INSTDIR\docs\LICENSE-pyjtag.txt"
    Delete "$INSTDIR\docs\README-pyjtag.txt"
    ; giveio
    ; if it was started by us, stop it
    ReadRegStr $0 HKLM SOFTWARE\mspgcc "giveio"
    StrCmp $0 '' no_giveio
    nsExec::ExecToLog  '$INSTDIR\bin\loaddrv.exe stop giveio'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 0 0 giveio_err giveio_err ;if not 0 -> error
    nsExec::ExecToLog '$INSTDIR\bin\loaddrv.exe remove giveio'
    Pop $0                              ;return value/error/timeout
    IntCmp $0 0 0 giveio_err giveio_err ;if not 0 -> error
    Goto no_giveio
giveio_err:
    DetailPrint "Error while uninstalling giveio service"
    MessageBox MB_OK|MB_ICONSTOP "Error while uninstalling giveio service"
no_giveio:
    Delete loaddrv.exe
    Delete giveio.sys
    ; MUST REMOVE UNINSTALLER, too
    Delete "$INSTDIR\uninstall-pyjtag.exe"
SectionEnd

;Display the Finish header
;Insert this macro after the sections if you are not using a finish page
!insertmacro MUI_SECTIONS_FINISHHEADER

;--------------------------------
;Descriptions

!insertmacro MUI_FUNCTIONS_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecJTAG} $(DESC_SecJTAG)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecGiveio} $(DESC_SecGiveio)
!insertmacro MUI_FUNCTIONS_DESCRIPTION_END

;--------------------------------
