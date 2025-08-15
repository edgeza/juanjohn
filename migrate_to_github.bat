@echo off
chcp 65001 >nul
echo 🚀 AutonamaDash GitHub Migration Script
echo ===============================================
echo.

echo 📋 Checking prerequisites...
echo.

REM Check if Git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git not found. Please install Git first:
    echo    1. Visit: https://git-scm.com/download/win
    echo    2. Download and install Git for Windows
    echo    3. Restart this command prompt
    echo.
    pause
    exit /b 1
)

echo ✅ Git found
git --version
echo.

REM Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo ❌ docker-compose.yml not found. Please run this script from the AutonamaDash root directory.
    pause
    exit /b 1
)

echo ✅ All prerequisites met!
echo.

echo 🧹 Step 1: Cleaning up sensitive data...
echo.

REM Remove sensitive files
if exist ".env" (
    echo Removing .env file...
    del /f ".env" >nul 2>&1
    echo ✅ Removed .env
)

if exist "crypto_data.db" (
    echo Removing crypto_data.db...
    del /f "crypto_data.db" >nul 2>&1
    echo ✅ Removed crypto_data.db
)

if exist "export_results" (
    echo Removing export_results directory...
    rmdir /s /q "export_results" >nul 2>&1
    echo ✅ Removed export_results
)

if exist "results" (
    echo Removing results directory...
    rmdir /s /q "results" >nul 2>&1
    echo ✅ Removed results
)

echo.

echo 🔒 Step 2: Checking .gitignore...
if not exist ".gitignore" (
    echo ❌ .gitignore not found. Please ensure it exists!
    pause
    exit /b 1
)
echo ✅ .gitignore found
echo.

echo 📦 Step 3: Setting up Git repository...
if exist ".git" (
    echo ℹ️  Git repository already exists
) else (
    echo Initializing Git repository...
    git init
    if %errorlevel% neq 0 (
        echo ❌ Failed to initialize Git repository
        pause
        exit /b 1
    )
    echo ✅ Git repository initialized
)
echo.

echo 🔗 Step 4: Adding GitHub remote...
git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    echo Updating remote URL...
    git remote set-url origin https://github.com/edgeza/juanjohn.git
) else (
    echo Adding GitHub remote...
    git remote add origin https://github.com/edgeza/juanjohn.git
)
echo ✅ GitHub remote configured
echo.

echo 📝 Step 5: Adding files and committing...
git add .
echo ✅ Files added to staging

git status --porcelain | findstr . >nul
if %errorlevel% equ 0 (
    echo Files to be committed:
    git status --porcelain
    
    git commit -m "Initial commit: AutonamaDash trading system migration to GitHub"
    if %errorlevel% neq 0 (
        echo ❌ Failed to commit files
        pause
        exit /b 1
    )
    echo ✅ Initial commit created
) else (
    echo ℹ️  No changes to commit
)
echo.

echo 🚀 Step 6: Setting up main branch...
git branch -M main
echo ✅ Main branch set
echo.

echo 🎉 Migration preparation complete!
echo ===============================================
echo.
echo Next steps:
echo 1. Push to GitHub: git push -u origin main
echo 2. Set up environment: copy env.example .env
echo 3. Edit .env with your API keys
echo 4. Start services: docker-compose up -d --build
echo.

echo Happy Trading! 🚀📈
pause
