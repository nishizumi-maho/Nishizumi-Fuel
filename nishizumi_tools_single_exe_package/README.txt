Nishizumi Tools - Single EXE package

What changed
- Launcher version is now v7
- The launcher now builds into one EXE only: NishizumiTools.exe
- FuelMonitor, Pit Calibrator, TireWear, and Traction are all launched from inside that same EXE
- The custom icon is used for the EXE and for the launcher tray icon
- Closing the launcher can hide it to the system tray instead of exiting
- The launcher checks GitHub Releases for updates every 6 hours

How to build
1. Open this folder on Windows.
2. Run build_all.bat
3. The final file will be in dist\NishizumiTools.exe

Notes
- The launcher can still open and close each app individually.
- App data is still saved in %APPDATA%\NishizumiTools
- The individual Python files stay in this source package so PyInstaller can bundle them into the single EXE
