@echo off
chcp 65001 >nul
echo 🚨 Fixing Nested Git Repositories
echo =================================
echo.

echo 📋 Current situation:
echo - You have nested Git repositories in autonama.api, autonama.data, and autonama.web
echo - This prevents them from being part of your main application repository
echo - We need to remove the nested .git folders and re-add everything
echo.

echo 🔧 Step 1: Removing nested repositories from Git index...
git rm --cached -r autonama.api autonama.data autonama.web
if %errorlevel% neq 0 (
    echo ⚠️  Some folders may not have been cached yet
) else (
    echo ✅ Nested repositories removed from Git index
)
echo.

echo 🗑️  Step 2: Removing nested .git folders...
if exist "autonama.api\.git" (
    echo Removing autonama.api\.git...
    rmdir /s /q "autonama.api\.git"
    echo ✅ Removed autonama.api\.git
) else (
    echo ℹ️  autonama.api\.git not found
)

if exist "autonama.data\.git" (
    echo Removing autonama.data\.git...
    rmdir /s /q "autonama.data\.git"
    echo ✅ Removed autonama.data\.git
) else (
    echo ℹ️  autonama.data\.git not found
)

if exist "autonama.web\.git" (
    echo Removing autonama.web\.git...
    rmdir /s /q "autonama.web\.git"
    echo ✅ Removed autonama.web\.git
) else (
    echo ℹ️  autonama.web\.git not found
)
echo.

echo 📝 Step 3: Re-adding all files to Git...
git add .
echo ✅ All files added to Git
echo.

echo 📊 Step 4: Checking what will be committed...
git status --porcelain
echo.

echo 🚀 Step 5: Committing the unified application...
git commit -m "Add full AutonamaDash application (removed nested repositories)"
if %errorlevel% neq 0 (
    echo ❌ Failed to commit. You may need to configure Git user info first:
    echo    git config --global user.name "Your Name"
    echo    git config --global user.email "your.email@example.com"
    pause
    exit /b 1
)
echo ✅ Application committed successfully!
echo.

echo 📤 Step 6: Pushing to GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ Failed to push. You may need to authenticate or check your remote.
    pause
    exit /b 1
)
echo ✅ Successfully pushed to GitHub!
echo.

echo 🎉 Nested repository issue fixed!
echo =================================
echo.
echo Your AutonamaDash application is now:
echo ✅ One unified Git repository
echo ✅ All autonama folders included as normal content
echo ✅ Ready for collaboration and deployment
echo.
echo Next steps:
echo 1. Clone the repository: git clone https://github.com/edgeza/juanjohn.git
echo 2. Set up environment: copy env.example .env
echo 3. Edit .env with your API keys
echo 4. Start services: docker-compose up -d --build
echo.

echo Happy Trading! 🚀📈
pause
