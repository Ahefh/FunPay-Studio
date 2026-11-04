@echo off
title FunPay Studio - Shutdown
cls
echo ====================================================
echo   Остановка FunPay Studio...
echo ====================================================
taskkill /F /FI "WINDOWTITLE eq FunPay Studio*" >nul 2>&1
taskkill /F /IM python.exe /FI "MODULES eq main.py" >nul 2>&1
echo.
echo [+] Процессы FunPay Studio успешно завершены.
timeout /t 3 >nul
