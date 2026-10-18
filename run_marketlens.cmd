@echo off
setlocal

rem These unavailable values are inherited in this development environment.
rem Clear only this exact stale endpoint for the MarketLens process; leave any
rem other authorized proxy configuration untouched.
if /I "%HTTP_PROXY%"=="http://127.0.0.1:9" set "HTTP_PROXY="
if /I "%HTTPS_PROXY%"=="http://127.0.0.1:9" set "HTTPS_PROXY="
if /I "%ALL_PROXY%"=="http://127.0.0.1:9" set "ALL_PROXY="

if not exist ".venv\Scripts\python.exe" (
    echo Project virtual environment not found. Create it with: python -m venv .venv
    endlocal & exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py %*
set "MARKETLENS_EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %MARKETLENS_EXIT_CODE%
