@echo off
set PYTHONUTF8=1
cd /d "C:\Automatic-Code\calendario_uni"
echo ===== %date% %time% ===== >> registro.txt
py sincronizar.py >> registro.txt 2>&1