@echo off
cd /d "C:\Users\DELL\rag_system"
echo ========================================
echo   🧠 ENTERPRISE RAG SYSTEM
echo ========================================
echo.
echo 📌 Starting Backend + Frontend...
echo.

start "Backend Server" cmd /k "venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak >nul
start "Frontend Server" cmd /k "venv\Scripts\activate && streamlit run app/frontend.py"

echo.
echo ========================================
echo   ✅ SERVICES STARTED!
echo ========================================
echo.
echo 📌 Backend: http://127.0.0.1:8000
echo 📌 Frontend: http://127.0.0.1:8501
echo.
echo 📌 Close both windows to stop services
echo.
pause