@echo off
rem Roda o apontamento do Systextil com o Python do ambiente conda "systextil-rpa".
rem Usa o caminho completo, porque o conda nao esta no PATH do PowerShell.
rem Uso: duplo clique, ou no terminal:
rem   rodar_apontamento.bat 2400 --ordem 123456 --linha 6   (completo, a partir da busca)
rem   rodar_apontamento.bat 2400 --so-rolo                  (tela de rolos ja aberta)

set PY=%LOCALAPPDATA%\miniconda3\envs\systextil-rpa\python.exe
if not exist "%PY%" (
    echo Ambiente systextil-rpa nao encontrado em %PY%
    pause
    exit /b 2
)

if "%~1"=="" (
    "%PY%" "%~dp0apontamento_rolo.py"
) else (
    "%PY%" "%~dp0apontamento_rolo.py" --metros %*
)
pause
