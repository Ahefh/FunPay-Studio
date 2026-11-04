@echo off
title FunPay Studio - Установка
cls
cd /d "%~dp0"
echo ====================================================
echo   Установка компонентов FunPay Studio (FPS)
echo ====================================================
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo ====================================================
echo [+] Установка успешно завершена!
echo Запустите Start.bat для первого запуска бота.
echo ====================================================
pause
