@echo off
cd /d "%~dp0"
echo Pulling latest updates...
git pull
echo.
echo Starting services (this may take a few minutes)...
docker-compose up --build
pause
