@echo off
echo ===============================
echo    Habits Tracker Bot
echo ===============================
echo.

echo Installing pyTelegramBotAPI...
pip install pytelegrambotapi==4.14.1

echo.
echo Starting bot...
python bot.py

pause