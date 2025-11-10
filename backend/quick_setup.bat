@echo off
echo Quick setup for ezyZip backend...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install essential packages
echo Installing essential packages...
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install python-multipart==0.0.6
pip install pydantic==2.5.0
pip install python-dotenv==1.0.0

echo.
echo Testing server startup...
python -c "import main; print('✅ All imports successful!')"

echo.
echo Installation complete! You can now run:
echo uvicorn main:app --reload
pause 