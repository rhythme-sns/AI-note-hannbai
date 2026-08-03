@echo off
cd /d "%~dp0"
python weekly_note.py >> run_log.txt 2>&1
