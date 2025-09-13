@echo off
REM === Setup inicial do Git para o projeto ===
chcp 65001 >nul

REM >>> AJUSTE estes dois se for usar outro repositório <<<
set "REPO_DIR=C:\Users\Fabio Lima\Documents\GitHub\ProjetoCarshop"
set "REMOTE_URL=https://github.com/afabiols/ProjetoCarshop.git"
REM <<<

echo.
echo [1/4] Indo para a pasta do projeto...
cd /d "%REPO_DIR%" || (echo ERRO: Pasta nao encontrada. & pause & exit /b 1)

echo [2/4] Verificando Git instalado...
where git >nul 2>nul || (echo ERRO: Git nao encontrado no PATH. Instale o Git. & pause & exit /b 1)

echo [3/4] Inicializando repositório (se necessario)...
if not exist ".git" (
  git init
) else (
  echo Ja existe um repo Git aqui.
)

echo [4/4] Configurando 'origin'...
git remote remove origin >nul 2>nul
git remote add origin "%REMOTE_URL%"

echo.
echo Fazendo commit inicial...
git add .
git commit -m "chore: commit inicial"

echo Definindo branch main e enviando...
git branch -M main
git push -u origin main

echo.
echo ✅ Setup concluido!
pause
