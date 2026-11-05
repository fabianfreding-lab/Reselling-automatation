@echo off
setlocal
cd /d "%~dp0"
set "PLAGG_PY=.venv312\Scripts\python.exe"
if exist "%PLAGG_PY%" goto check_python
where py >nul 2>&1
if errorlevel 1 goto missing_launcher
echo Installerar eller kontrollerar Python 3.12 via Python Install Manager...
rem Request installation explicitly: missing-runtime launcher errors may return success.
rem CALL also returns here if the launcher is supplied as a command-file shim.
call py install 3.12
rem A legacy launcher may lack the install subcommand but still have Python 3.12.
echo Skapar appens separata Python 3.12-miljo...
call py -3.12 -m venv .venv312
if errorlevel 1 goto missing_python
if not exist "%PLAGG_PY%" goto missing_python
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
echo Python 3.12 eller den virtuella miljon kunde inte installeras.
echo Oppna Kommandotolken och kor: py install 3.12
echo Starta sedan denna fil igen. Vid installationsfel, skicka feltexten ovan.
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
