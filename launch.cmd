@echo off
setlocal
cd /d "%~dp0"

echo === Multi-Agent Research Assistant launcher ===

where uv >nul 2>&1
if errorlevel 1 (
    echo uv not found, installing it now...
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

echo Installing/updating dependencies...
uv sync
if errorlevel 1 (
    echo.
    echo Dependency install failed. See errors above.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        echo No .env found - copying .env.example as a starting point.
        copy /y ".env.example" ".env" >nul
        echo Edit .env with your API keys if OPENAI_API_KEY / AGNES_API_KEY are not already set system-wide.
    )
)

echo Starting the app at http://localhost:8521 ...
uv run streamlit run app.py

pause
