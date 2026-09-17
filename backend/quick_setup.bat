@echo off
REM Creates the backend virtual environment and installs dependencies.
cd /d "%~dp0"

if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if not exist .env copy .env.example .env >nul

echo.
echo Checking the app imports and the try-on model...
python -c "import main; print(main.tryon_service.status())"

echo.
echo Done. Start the API with:  uvicorn main:app --reload --port 8000
pause
