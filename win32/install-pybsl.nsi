; This creates an installer for the msp430-bsl.exe
; using NSIS.sf.net version 2.0

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

!define MUI_PRODUCT "MSPGCC BSL"
!define MUI_VERSION "20040108"

!define MUI_NAME "MSPGCC install-pybsl ${MUI_VERSION}"

!define MUI_WELCOMEPAGE
!define MUI_LICENSEPAGE
!define MUI_COMPONENTSPAGE
!define MUI_DIRECTORYPAGE
!define MUI_FINISHPAGE
  !define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\docs\README-pybsl.txt"
  !define MUI_FINISHPAGE_NOREBOOTSUPPORT
!define MUI_ABORTWARNING
  
!define MUI_UNINSTALLER
!define MUI_UNCONFIRMPAGE
;!define MUI_SPECIALBITMAP "${NSISDIR}\Contrib\Icons\modern-wizard.bmp"
!define MUI_SPECIALBITMAP "..\..\packaging\msp430-image.bmp"
;!define MUI_UI "${NSISDIR}\Contrib\UIs\modern_headerbmp.exe"
!define MUI_UI "${NSISDIR}\Contrib\UIs\modern.exe"


OutFile "install-pybsl-${MUI_VERSION}.exe"

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
  LangString DESC_SecBSL ${LANG_ENGLISH} "Command line BSL programmer."

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


Section "msp430-bsl (required)" SecBSL
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    File /r ..\bin
    SetOutPath "$INSTDIR\docs"
    File /oname=LICENSE-msp430-bsl.txt      "..\license.txt"
    File "..\README-msp430-bsl.txt"
    SetOutPath "$INSTDIR"

    ; Write the installation path into the registry
    WriteRegStr HKLM SOFTWARE\mspgcc "rootdir" "$INSTDIR"
    ; Write the uninstall keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\mspgcc-pybsl" "DisplayName" "mspgcc pybsl (remove only)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\mspgcc-pybsl" "UninstallString" '"$INSTDIR\uninstall-pybsl.exe"'
    WriteUninstaller "uninstall-pybsl.exe"
SectionEnd

; special uninstall section.
Section "Uninstall"
    ; remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\mspgcc-pybsl"
    ;~ DeleteRegKey HKLM SOFTWARE\mspgcc
    ; remove files
    Delete "$INSTDIR\bin\msp430-bsl.exe"
    ;~ Delete $INSTDIR\bin\HIL.dll
    ;~ Delete $INSTDIR\bin\MSP430mspgcc.dll
    ;XXX python22.dll is left installed as it is used by pybsl and other tools
    Delete "$INSTDIR\docs\LICENSE-pybsl.txt"
    Delete "$INSTDIR\docs\README-msp430-bsl.txt"
    ; giveio
    ; MUST REMOVE UNINSTALLER, too
    Delete "$INSTDIR\uninstall-pybsl.exe"
SectionEnd

;Display the Finish header
;Insert this macro after the sections if you are not using a finish page
!insertmacro MUI_SECTIONS_FINISHHEADER

;--------------------------------
;Descriptions

!insertmacro MUI_FUNCTIONS_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecBSL} $(DESC_SecBSL)
!insertmacro MUI_FUNCTIONS_DESCRIPTION_END

;--------------------------------
