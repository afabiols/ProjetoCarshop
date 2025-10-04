@echo off
REM === Git Smart Setup & Push para ProjetoCarshop ===
chcp 65001 >nul
setlocal ENABLEDELAYEDEXPANSION

REM >>> AJUSTE estes dois se for usar outro repositório <<<
set "REPO_DIR=C:\Users\Fabio Lima\Documents\GitHub\ProjetoCarshop"
set "REMOTE_URL=https://github.com/afabiols/ProjetoCarshop.git"
REM <<<

set "DEFAULT_BRANCH=main"
REM (opcional) defina se quiser configurar no repo local, caso ainda não tenha:
set "GIT_USER_NAME=Fabio Lima"
set "GIT_USER_EMAIL=seu-email@exemplo.com"

echo.
echo [1/8] Indo para a pasta do projeto...
cd /d "%REPO_DIR%" || (echo ERRO: Pasta nao encontrada: %REPO_DIR% & pause & exit /b 1)

echo [2/8] Verificando Git instalado...
where git >nul 2>nul || (echo ERRO: Git nao encontrado no PATH. Instale o Git. & pause & exit /b 1)

REM ---------------- Repo init / config ----------------
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo [3/8] Inicializando novo repositorio Git...
  git init || (echo ERRO: git init falhou. & pause & exit /b 1)
  git branch -M "%DEFAULT_BRANCH%"
) else (
  echo [3/8] Repositorio Git detectado.
)

REM Configura user.name e user.email se nao existirem no repo
for /f "tokens=*" %%i in ('git config user.name 2^>nul') do set HAVE_GITNAME=1
if not defined HAVE_GITNAME if not "%GIT_USER_NAME%"=="" git config user.name "%GIT_USER_NAME%"
for /f "tokens=*" %%i in ('git config user.email 2^>nul') do set HAVE_GITEMAIL=1
if not defined HAVE_GITEMAIL if not "%GIT_USER_EMAIL%"=="" git config user.email "%GIT_USER_EMAIL%"

REM ---------------- Remote origin ----------------
echo [4/8] Configurando 'origin'...
for /f "tokens=*" %%i in ('git remote 2^>nul') do set HAVE_REMOTE=1
if not defined HAVE_REMOTE (
  git remote add origin "%REMOTE_URL%" || (echo ERRO: nao foi possivel adicionar origin. & pause & exit /b 1)
) else (
  REM Garante que a URL esta correta; se quiser SEMPRE sobrescrever, descomente as 2 linhas abaixo:
  REM git remote remove origin
  REM git remote add origin "%REMOTE_URL%"
)

REM ---------------- Primeiro commit? ----------------
git rev-parse --verify HEAD >nul 2>nul
if errorlevel 1 ( set FIRST_COMMIT=1 ) else ( set FIRST_COMMIT= )

if defined FIRST_COMMIT (
  echo [5/8] Nenhum commit local ainda.
  REM Se a branch existir no remoto, faz pull --rebase para alinhar
  git ls-remote --exit-code --heads origin "%DEFAULT_BRANCH%" >nul 2>nul
  if not errorlevel 1 (
    echo   - Branch "%DEFAULT_BRANCH%" existe no remoto. Fazendo pull --rebase...
    git pull --rebase origin "%DEFAULT_BRANCH%" || echo   (Aviso: pull inicial falhou ou remoto vazio. Prosseguindo.)
  ) else (
    echo   - Remoto sem a branch "%DEFAULT_BRANCH%" (ou repo vazio). Prosseguindo sem pull.
  )
) else (
  echo [5/8] Repo local ja possui commits.
)

REM ---------------- Commit (se houver mudanca) ----------------
echo [6/8] Verificando alteracoes...
set CHANGES=
for /f "delims=" %%i in ('git status --porcelain') do set CHANGES=1

if not defined CHANGES (
  echo   - Nao ha alteracoes para commitar.
) else (
  git add -A
  set /p MSG=Mensagem do commit (vazio = "update: alteracoes recentes"): 
  if "%MSG%"=="" set "MSG=update: alteracoes recentes"
  git commit -m "%MSG%" || echo   - Aviso: commit nao realizado (hooks ou conflito).
)

REM Garante existencia da branch local
git rev-parse --verify "%DEFAULT_BRANCH%" >nul 2>nul
if errorlevel 1 (
  if not defined CHANGES if defined FIRST_COMMIT (
    echo   - Criando commit vazio para inicializar o historico...
    git commit --allow-empty -m "chore: initial commit (empty)"
  )
  git branch -M "%DEFAULT_BRANCH%"
)

REM ---------------- Push com upstream se necessario ----------------
echo [7/8] Enviando para o remoto (%DEFAULT_BRANCH%)...
git rev-parse --abbrev-ref --symbolic-full-name @{u} >nul 2>nul
if errorlevel 1 (
  git push -u origin "%DEFAULT_BRANCH%" || (echo ERRO: push falhou. & pause & exit /b 1)
) else (
  REM Tenta rebase (se o remoto tiver avancado) e reenviar
  git pull --rebase origin "%DEFAULT_BRANCH%" || echo (Aviso: pull --rebase falhou; tentando prosseguir.)
  git push origin "%DEFAULT_BRANCH%" || (echo ERRO: push falhou. & pause & exit /b 1)
)

echo [8/8] Sucesso!
echo.
echo ===== Remote: =====
git remote -v
echo.
echo ===== Ultimo commit: =====
git log -1 --oneline
echo.
echo ===== Status final: =====
git status -sb

echo.
echo ✅ Repositorio sincronizado com o GitHub.
pause
endlocal
