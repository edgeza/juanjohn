# Git Installation Script for Windows
# This script helps install Git if it's not already available

Write-Host "🔧 Git Installation Helper for Windows" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check if Git is already installed
try {
    $gitVersion = git --version 2>$null
    if ($gitVersion) {
        Write-Host "✅ Git is already installed: $gitVersion" -ForegroundColor Green
        Write-Host "You can proceed with the migration!" -ForegroundColor Green
        exit 0
    }
} catch {
    Write-Host "Git not found in PATH" -ForegroundColor Yellow
}

Write-Host "`n📋 Git Installation Options:" -ForegroundColor Yellow
Write-Host "1. Download and install Git for Windows" -ForegroundColor White
Write-Host "2. Install via Chocolatey (if available)" -ForegroundColor White
Write-Host "3. Install via Winget (Windows 10/11)" -ForegroundColor White
Write-Host "4. Manual installation instructions" -ForegroundColor White

Write-Host "`n🚀 Recommended: Option 1 (Direct download)" -ForegroundColor Green

# Option 1: Direct download
Write-Host "`n📥 Option 1: Downloading Git for Windows..." -ForegroundColor Yellow

try {
    # Download Git installer
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $installerPath = "$env:TEMP\GitInstaller.exe"
    
    Write-Host "Downloading Git installer..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $gitUrl -OutFile $installerPath
    
    Write-Host "✅ Download complete!" -ForegroundColor Green
    Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
    Write-Host "1. Run the installer: $installerPath" -ForegroundColor White
    Write-Host "2. Follow the installation wizard" -ForegroundColor White
    Write-Host "3. Restart PowerShell after installation" -ForegroundColor White
    Write-Host "4. Run: git --version to verify" -ForegroundColor White
    
    # Ask if user wants to run installer now
    $runNow = Read-Host "`nWould you like to run the installer now? (y/n)"
    if ($runNow -eq 'y' -or $runNow -eq 'Y') {
        Write-Host "🚀 Starting Git installer..." -ForegroundColor Green
        Start-Process -FilePath $installerPath -Wait
        Write-Host "`n✅ Installation complete! Please restart PowerShell and try again." -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Failed to download Git installer" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    Write-Host "`n📋 Alternative installation methods:" -ForegroundColor Yellow
    
    # Option 2: Chocolatey
    Write-Host "`n🍫 Option 2: Install via Chocolatey" -ForegroundColor Cyan
    Write-Host "If you have Chocolatey installed, run:" -ForegroundColor White
    Write-Host "  choco install git" -ForegroundColor Gray
    
    # Option 3: Winget
    Write-Host "`n📦 Option 3: Install via Winget" -ForegroundColor Cyan
    Write-Host "If you have Winget available, run:" -ForegroundColor White
    Write-Host "  winget install --id Git.Git -e --source winget" -ForegroundColor Gray
    
    # Option 4: Manual
    Write-Host "`n📖 Option 4: Manual Installation" -ForegroundColor Cyan
    Write-Host "1. Visit: https://git-scm.com/download/win" -ForegroundColor White
    Write-Host "2. Download the latest version" -ForegroundColor White
    Write-Host "3. Run the installer" -ForegroundColor White
    Write-Host "4. Restart PowerShell" -ForegroundColor White
}

Write-Host "`n📚 After installing Git:" -ForegroundColor Yellow
Write-Host "1. Restart PowerShell" -ForegroundColor White
Write-Host "2. Verify installation: git --version" -ForegroundColor White
Write-Host "3. Configure Git: git config --global user.name 'Your Name'" -ForegroundColor White
Write-Host "4. Configure Git: git config --global user.email 'your.email@example.com'" -ForegroundColor White
Write-Host "5. Run the migration script again" -ForegroundColor White

Write-Host "`n🤝 Need help? Check the MIGRATION_GUIDE.md file for detailed instructions." -ForegroundColor Cyan
