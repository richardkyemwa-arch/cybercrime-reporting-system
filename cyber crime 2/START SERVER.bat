@echo off
title CyberReport - Local Server
color 0B
echo =====================================================
echo   CyberReport - Starting Local Server with ngrok
echo =====================================================
echo.
set NGROK_PATH=C:\Users\KYEMWA RICHARD\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe
set PATH=%PATH%;%NGROK_PATH%
python start_local.py
pause
