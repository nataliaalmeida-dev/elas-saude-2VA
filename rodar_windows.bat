@echo off
TITLE Elas Saude - Inicializador Windows
echo ==========================================================
echo    🚀 INICIANDO PROJETO ELAS SAUDE...
echo ==========================================================
echo.

:: Suporte para caminhos de rede (UNC)
pushd "%~dp0"

powershell -ExecutionPolicy Bypass -File ".\rodarprojeto.ps1"

popd
pause
