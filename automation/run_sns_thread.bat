@echo off
cd /d "%~dp0"
python sns_thread.py >> run_log.txt 2>&1
