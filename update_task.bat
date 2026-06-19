@echo off
title 创建定时清理任务

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请右键本文件 --> 以管理员身份运行
    pause
    exit /b
)

set "PROJECT=%~dp0"
set "PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
set "TASKNAME=SystemCleaner"

echo ============================================================
echo   创建系统垃圾清理定时任务
echo ============================================================
echo.
echo   任务名称: %TASKNAME%
echo   Python:   %PYTHON%
echo   脚本路径: %PROJECT%cleaner.py
echo   执行时间: 每天 15:27
echo   运行身份: SYSTEM
echo.

:: 如果 Python 路径不存在，检查常见位置
if not exist "%PYTHON%" (
    echo [WARN] Python 未在默认位置, 尝试查找...
    for /f "delims=" %%i in ('where python 2^>nul') do (
        if exist "%%i" (
            set "PYTHON=%%i"
            echo [OK]  找到: %%i
            goto :found
        )
    )
    echo [FAIL] 未找到 Python，请手动编辑本文件第 8 行
    pause
    exit /b
)
:found

:: 删除旧任务
schtasks /delete /tn %TASKNAME% /f >nul 2>&1

:: 创建新任务
schtasks /create /tn %TASKNAME% /tr "cmd /c %PYTHON% %PROJECT%cleaner.py --quiet --no-confirm >> %PROJECT%cleaner_report.log 2>&1" /sc daily /st 15:27 /ru SYSTEM /rl HIGHEST /f

if %errorLevel% equ 0 (
    echo.
    echo ============================================================
    echo   [OK] 创建成功！下次运行: 明天 15:27
    echo ============================================================
) else (
    echo.
    echo   [FAIL] 创建失败，错误码: %errorLevel%
)

echo.
pause
