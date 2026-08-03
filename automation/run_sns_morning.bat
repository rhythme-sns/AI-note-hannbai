@echo off
cd /d "%~dp0"
python sns_single_post.py morning >> run_log.txt 2>&1
