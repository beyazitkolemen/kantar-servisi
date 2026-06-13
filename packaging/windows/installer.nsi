Unicode True
SetCompressor /SOLID lzma
RequestExecutionLevel user

!include "MUI2.nsh"
!include "LogicLib.nsh"

!ifndef APP_VERSION
  !define APP_VERSION "0.0.0"
!endif
!ifndef APP_VERSION4
  !define APP_VERSION4 "0.0.0.0"
!endif
!ifndef SOURCE_DIR
  !error "SOURCE_DIR tanimlanmadi"
!endif
!ifndef OUTPUT_DIR
  !error "OUTPUT_DIR tanimlanmadi"
!endif

!define APP_NAME "Kantar Servisi"
!define APP_EXE "KantarServisi.exe"
!define APP_ID "KantarServisi"
!define APP_PUBLISHER "LISDEP"
!define APP_URL "https://github.com/beyazitkolemen/kantar-servisi"
!define APP_DOWNLOAD_URL "https://github.com/beyazitkolemen/kantar-servisi/tree/main/downloads"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "${OUTPUT_DIR}/Kantar-Servisi-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\Kantar Servisi"
InstallDirRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\App Paths\${APP_EXE}" ""
BrandingText "LISDEP"
Icon "../../.build-assets/app.ico"
UninstallIcon "../../.build-assets/app.ico"
VIProductVersion "${APP_VERSION4}"
VIAddVersionKey /LANG=1055 "ProductName" "${APP_NAME}"
VIAddVersionKey /LANG=1055 "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey /LANG=1055 "FileDescription" "${APP_NAME} Windows Kurulumu"
VIAddVersionKey /LANG=1055 "FileVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1055 "ProductVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1055 "LegalCopyright" "Copyright (c) 2026 LISDEP"

!define MUI_ABORTWARNING
!define MUI_ICON "../../.build-assets/app.ico"
!define MUI_UNICON "../../.build-assets/app.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "../../.build-assets/wizard-large.bmp"
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_PARAMETERS "--open-panel"
!define MUI_FINISHPAGE_RUN_TEXT "Kantar Servisini baslat"
!define MUI_FINISHPAGE_LINK "GitHub indirme klasorunu ac"
!define MUI_FINISHPAGE_LINK_LOCATION "${APP_DOWNLOAD_URL}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "Turkish"
!insertmacro MUI_LANGUAGE "English"

Section "Kantar Servisi (zorunlu)" MainSection
  SectionIn RO
  SetShellVarContext current
  SetOutPath "$INSTDIR"

  nsExec::ExecToStack 'taskkill /F /IM ${APP_EXE}'
  Pop $0
  Pop $1

  RMDir /r "$INSTDIR"
  CreateDirectory "$INSTDIR"
  SetOutPath "$INSTDIR"
  File /r "${SOURCE_DIR}\*"

  CreateDirectory "$SMPROGRAMS\Kantar Servisi"
  CreateShortcut "$SMPROGRAMS\Kantar Servisi\Kantar Servisi.lnk" "$INSTDIR\${APP_EXE}" "--open-panel" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\Kantar Servisi\Yonetim Paneli.lnk" "$INSTDIR\${APP_EXE}" "--open-panel" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\Kantar Servisi\Log Klasoru.lnk" "$INSTDIR\${APP_EXE}" "--open-logs" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\Kantar Servisi\Tanilama Raporu.lnk" "$INSTDIR\${APP_EXE}" "--diagnostics" "$INSTDIR\${APP_EXE}"

  WriteUninstaller "$INSTDIR\KantarServisi-Kaldir.exe"
  CreateShortcut "$SMPROGRAMS\Kantar Servisi\Kantar Servisini Kaldir.lnk" "$INSTDIR\KantarServisi-Kaldir.exe"

  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\App Paths\${APP_EXE}" "" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\App Paths\${APP_EXE}" "Path" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "URLInfoAbout" "${APP_URL}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "URLUpdateInfo" "${APP_DOWNLOAD_URL}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "UninstallString" '"$INSTDIR\KantarServisi-Kaldir.exe"'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}" "NoRepair" 1
SectionEnd

Section /o "Masaustu kisayolu" DesktopSection
  SetShellVarContext current
  CreateShortcut "$DESKTOP\Kantar Servisi.lnk" "$INSTDIR\${APP_EXE}" "--open-panel" "$INSTDIR\${APP_EXE}"
SectionEnd

Section /o "Windows acilisinda baslat" StartupSection
  SetShellVarContext current
  CreateShortcut "$SMSTARTUP\Kantar Servisi.lnk" "$INSTDIR\${APP_EXE}" "--minimized" "$INSTDIR\${APP_EXE}"
SectionEnd

LangString DESC_MainSection ${LANG_TURKISH} "Kantar Servisi uygulamasi ve gerekli Windows calisma zamani."
LangString DESC_MainSection ${LANG_ENGLISH} "Kantar Servisi application and required Windows runtime."
LangString DESC_DesktopSection ${LANG_TURKISH} "Masaustune Kantar Servisi kisayolu ekler."
LangString DESC_DesktopSection ${LANG_ENGLISH} "Adds a Kantar Servisi desktop shortcut."
LangString DESC_StartupSection ${LANG_TURKISH} "Kantar Servisini Windows oturumu acildiginda sistem tepsisinde baslatir."
LangString DESC_StartupSection ${LANG_ENGLISH} "Starts Kantar Servisi in the system tray when Windows signs in."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${MainSection} $(DESC_MainSection)
  !insertmacro MUI_DESCRIPTION_TEXT ${DesktopSection} $(DESC_DesktopSection)
  !insertmacro MUI_DESCRIPTION_TEXT ${StartupSection} $(DESC_StartupSection)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
  SetShellVarContext current
  nsExec::ExecToStack 'taskkill /F /IM ${APP_EXE}'
  Pop $0
  Pop $1

  Delete "$DESKTOP\Kantar Servisi.lnk"
  Delete "$SMSTARTUP\Kantar Servisi.lnk"
  RMDir /r "$SMPROGRAMS\Kantar Servisi"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\App Paths\${APP_EXE}"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_ID}"
  RMDir /r "$INSTDIR"
SectionEnd
