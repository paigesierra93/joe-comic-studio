@echo off
cd /d "%~dp0"
echo Starting Maya's Empire...
echo.
REM Point to the portable Python
.\python_brain\python\python.exe -m streamlit run bank_app.py
pause
