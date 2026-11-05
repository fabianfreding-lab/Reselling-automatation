@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto error
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
.venv\Scripts\python.exe app.py
pause
exit /b
:error
echo Installationen misslyckades. Kontrollera Python 3.12+ och internetanslutning.
pause
