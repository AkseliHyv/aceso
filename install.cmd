@echo off
powershell.exe -ExecutionPolicy Bypass -NoProfile -File ".\mpremote-sync.ps1" push -Clean
pause