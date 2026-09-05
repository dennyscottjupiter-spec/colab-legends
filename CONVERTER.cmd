@echo off
REM Duplo clique: converte todos os videos desta pasta em .mp3
REM Ou arraste um video (ou varios) para cima deste arquivo.
cd /d "%~dp0"
python3 mp4_para_mp3.py %*
echo.
pause
