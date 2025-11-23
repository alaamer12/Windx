@echo off
REM Backend API - Postman Collections Test Runner (Windows)
REM This script runs all Postman collections using Newman

setlocal enabledelayedexpansion

REM Configuration
set "POSTMAN_DIR=%~dp0"
set "ENVIRONMENT=%POSTMAN_DIR%Backend-API.Environment.postman_environment.json"
set "REPORT_DIR=%POSTMAN_DIR%reports"

REM Create reports directory
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"

echo ========================================
echo Backend API - Postman Test Runner
echo ========================================
echo.

REM Check if Newman is installed
where newman >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Newman is not installed
    echo Install with: npm install -g newman
    exit /b 1
)

echo [OK] Newman found
echo.

REM Track results
set TOTAL=0
set PASSED=0
set FAILED=0

REM Run collections in order
call :run_collection "Backend-API.Health"
call :run_collection "Backend-API.Authentication"
call :run_collection "Backend-API.Users"
call :run_collection "Backend-API.Dashboard"
call :run_collection "Backend-API.Export"

REM Summary
echo.
echo ========================================
echo Test Summary
echo ========================================
echo Total Collections: %TOTAL%
echo Passed: %PASSED%
echo Failed: %FAILED%
echo.

REM Reports location
echo Reports saved to: %REPORT_DIR%
echo.

REM Exit with appropriate code
if %FAILED% EQU 0 (
    echo [SUCCESS] All tests passed!
    exit /b 0
) else (
    echo [FAILED] Some tests failed
    exit /b 1
)

:run_collection
set "collection_name=%~1"
set "collection_file=%POSTMAN_DIR%%collection_name%.postman_collection.json"

set /a TOTAL+=1

echo Running: %collection_name%
echo ----------------------------------------

newman run "%collection_file%" ^
    -e "%ENVIRONMENT%" ^
    --reporters cli,json ^
    --reporter-json-export "%REPORT_DIR%\%collection_name%-report.json" ^
    --color on ^
    --timeout-request 10000

if %ERRORLEVEL% EQU 0 (
    echo [PASSED] %collection_name%
    set /a PASSED+=1
) else (
    echo [FAILED] %collection_name%
    set /a FAILED+=1
)

echo.
goto :eof
