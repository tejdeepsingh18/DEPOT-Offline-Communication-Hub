@echo off
cd /d "%~dp0"
echo ==== discovery > pi_status.txt
powershell -NoProfile -ExecutionPolicy Bypass -File pi_find.ps1 >> pi_status.txt 2>&1
arp -a -N 192.168.137.1 >> pi_status.txt 2>&1
if not exist pi_ip.txt (
  echo NO PI FOUND on 192.168.137.x >> pi_status.txt
  goto laptop
)
set /p PIIP=<pi_ip.txt
echo ==== ssh netpie@%PIIP% >> pi_status.txt
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new netpie@%PIIP% "bash -s" < pi_check.sh >> pi_status.txt 2>&1
:laptop
echo. >> pi_status.txt
echo ==== laptop side >> pi_status.txt
ipconfig >> pi_status.txt
echo DONE >> pi_status.txt
