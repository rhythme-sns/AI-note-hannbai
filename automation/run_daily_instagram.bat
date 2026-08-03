@echo off
cd /d "%~dp0"
python daily_instagram.py >> run_log.txt 2>&1
