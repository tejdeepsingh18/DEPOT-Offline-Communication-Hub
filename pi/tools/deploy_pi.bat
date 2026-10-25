@echo off
rem ================================================================
rem  DEPOT - deploy the new server.py + index.html to the Pi.
rem  Double-click. It finds the Pi, copies the files, backs up the
rem  old version on the Pi, and restarts. You'll be asked for the
rem  Pi's password ONCE (for sudo restart).
rem ================================================================
cd /d "%~dp0"
echo Finding the Pi on 192.168.137.x ...
powershell -NoProfile -ExecutionPolicy Bypass -File pi_find.ps1
if not exist pi_ip.txt ( echo NO PI FOUND - check cable / ICS & pause & exit /b 1 )
set /p PIIP=<pi_ip.txt
echo Pi is at %PIIP%
ssh -o ConnectTimeout=8 netpie@%PIIP% "mkdir -p /tmp/depot_new"
scp ..\server.py ..\index.html install_on_pi.sh netpie@%PIIP%:/tmp/depot_new/
ssh -t netpie@%PIIP% "bash /tmp/depot_new/install_on_pi.sh 2>&1 | tee /tmp/depot_new/install.log"
scp netpie@%PIIP%:/tmp/depot_new/install.log deploy_log.txt
echo.
echo Log saved to tools\deploy_log.txt
pause
