@echo off
title Fashion AI Chatbot Server
color 0A
echo ========================================================
echo        FASHION AI CHATBOT - SERVER LAUNCHER
echo ========================================================
echo.
cd /d "%~dp0"
echo Dang khoi dong Flask Server tai http://127.0.0.1:5000...
echo.
start "" http://127.0.0.1:5000
python app.py 5000
pause
