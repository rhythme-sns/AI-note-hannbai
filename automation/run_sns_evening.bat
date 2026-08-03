@echo off
cd /d "%~dp0"
python sns_single_post.py evening >> run_log.txt 2>&1
