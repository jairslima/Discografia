@echo off
setlocal
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%dist\discografia\discografia.exe" (
  "%SCRIPT_DIR%dist\discografia\discografia.exe" %*
) else (
  python "%SCRIPT_DIR%discografia_app.py" %*
)
endlocal
