@echo off
REM Activate virtual environment for Windows
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated!
echo Python path: %VIRTUAL_ENV%\Scripts\python.exe
echo.
echo You can now run:
echo   python bot.py
echo   python -m pytest
echo   python -m black .
echo   python -m ruff check .
echo   python -m mypy .
echo   python -m safety check
echo   python -m bandit -r app/
echo.
cmd /k
