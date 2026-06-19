@echo off
title Windows Cleaner

net session >nul 2>&1
if %errorLevel% neq 0 (
    PowerShell -Command "Start-Process '%~f0' -Verb RunAs" >nul 2>&1
    exit /b
)

cd /d "%~dp0"

for /f %%a in ('PowerShell -NoProfile -Command "(Get-PSDrive C).Free"') do set before=%%a
PowerShell -NoProfile -Command "$b=[double]%before%; Write-Host ('Before: {0:N2} GB' -f ($b/1GB))"

echo.
echo Cleaning...
echo.

python cleaner.py --no-confirm

echo.

for /f %%a in ('PowerShell -NoProfile -Command "(Get-PSDrive C).Free"') do set after=%%a
PowerShell -NoProfile -Command "$b=[double]%before%; $a=[double]%after%; Write-Host ('Before: {0:N2} GB  After: {1:N2} GB  Freed: +{2:N2} GB' -f ($b/1GB), ($a/1GB), (($a-$b)/1GB))"

echo.
echo Done. Log: cleaner.log
echo.
pause
