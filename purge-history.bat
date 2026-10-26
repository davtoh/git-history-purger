@echo off
setlocal
python "%~dp0purge_git_history.py" %*
endlocal
