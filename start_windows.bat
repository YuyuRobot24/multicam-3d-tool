@echo off
setlocal
cd /d "%~dp0"
if exist ".conda-env\python.exe" (
  set "PATH=%~dp0.conda-env;%~dp0.conda-env\Library\bin;%~dp0.conda-env\Scripts;%PATH%"
  ".conda-env\python.exe" app.py
  if errorlevel 1 goto fail
  exit /b 0
)
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto fail
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe app.py
if errorlevel 1 goto fail
exit /b 0
:fail
pause
exit /b 1
