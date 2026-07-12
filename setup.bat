@echo off
echo ========================================
echo   🧠 ENTERPRISE RAG SYSTEM - SETUP
echo ========================================
echo.

echo 📌 Creating virtual environment...
python -m venv venv

echo.
echo 📌 Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 📌 Installing dependencies...
pip install -r requirements.txt

echo.
echo 📌 Creating uploads directory...
mkdir uploads 2>nul

echo.
echo ========================================
echo   ✅ SETUP COMPLETE!
echo ========================================
echo.
echo 📌 To run the project, double-click:
echo    run_project.bat
echo.
pause