@echo off
setlocal
cd /d "%~dp0"
set "PLAGG_PY=.venv312\Scripts\python.exe"
if exist "%PLAGG_PY%" goto check_python
where py >nul 2>&1
if errorlevel 1 goto missing_launcher
echo Forbereder Python 3.12 for Plaggverket...
py -3.12 -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))"
if not errorlevel 1 goto create_venv
rem Python Install Manager can install the selected runtime with signature verification.
py install 3.12
if errorlevel 1 goto missing_python
:create_venv
py -3.12 -m venv .venv312
if errorlevel 1 goto error
:check_python
"%PLAGG_PY%" -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))"
if errorlevel 1 goto wrong_venv
echo Installerar appens kostnadsfria beroenden...
"%PLAGG_PY%" -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto error
echo.
echo Oppna http://127.0.0.1:5000 i webblasaren nar servern har startat.
echo Lat detta fonster vara oppet medan du anvander appen.
"%PLAGG_PY%" app.py
if errorlevel 1 goto error
pause
exit /b 0
:missing_launcher
echo Python-startaren py saknas. Installera Python 3.12 fran https://www.python.org/downloads/windows/
goto stop_error
:missing_python
echo Python 3.12 kunde inte installeras. Installera Python 3.12 fran https://www.python.org/downloads/windows/
goto stop_error
:wrong_venv
echo Mappen .venv312 innehaller inte en fungerande Python 3.12-miljo.
echo Byt namn pa endast .venv312 och kor startfilen igen. Bevara alltid mappen data.
goto stop_error
:error
echo.
echo Starten misslyckades. Ta en bild av feltexten ovan sa att felet kan undersokas.
:stop_error
pause
exit /b 1
