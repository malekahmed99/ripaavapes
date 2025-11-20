@echo off
echo Setting up virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Running tests...
python test_app.py

echo.
echo If tests passed, you can try running the server with:
echo python scanner.py
pause
