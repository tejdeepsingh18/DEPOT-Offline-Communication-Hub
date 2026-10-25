@echo off
rem Restores the version that was on the Pi before the last deploy.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File pi_find.ps1
set /p PIIP=<pi_ip.txt
ssh -t netpie@%PIIP% "bash /home/netpie/depot/rollback.sh"
pause
