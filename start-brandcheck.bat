@echo off
setlocal
set "ROOT=%~dp0"
if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -3 -m venv "%ROOT%backend\.venv"
  if errorlevel 1 python -m venv "%ROOT%backend\.venv"
)
if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
  echo Could not create the Python environment. Install Python 3.11+ and try again.
  pause
  exit /b 1
)
echo Installing/checking backend dependencies. This needs internet the first time.
"%ROOT%backend\.venv\Scripts\python.exe" -m pip install -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (echo Backend dependency install failed.& pause & exit /b 1)
if not exist "%ROOT%backend\.env" copy "%ROOT%backend\.env.example" "%ROOT%backend\.env" >nul
start "BrandCheck Backend" cmd /k "cd /d ""%ROOT%backend"" && ""%ROOT%backend\.venv\Scripts\python.exe"" -m uvicorn main:app --reload"
if not exist "%ROOT%frontend\node_modules" (
  echo Installing frontend dependencies. This needs internet the first time.
  pushd "%ROOT%frontend"
  call npm install
  if errorlevel 1 (popd & echo Frontend dependency install failed. Ensure Node.js 20+ and internet are available. & pause & exit /b 1)
  popd
)
start "BrandCheck Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm run dev"
echo Backend and frontend terminal windows have been opened.
echo Open http://127.0.0.1:5173 in your browser.
pause
