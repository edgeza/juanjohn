# AutonamaDash GitHub Migration Script
# Simple version - run this after installing Git

param(
    [switch]$DryRun = $false
)

Write-Host "🚀 AutonamaDash GitHub Migration Script" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Check if Git is available
try {
    $gitVersion = git --version
    Write-Host "✅ Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git not found. Please run install_git.ps1 first!" -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ docker-compose.yml not found. Please run this script from the AutonamaDash root directory." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All prerequisites met!" -ForegroundColor Green

# Step 1: Clean up sensitive data
Write-Host "`n🧹 Step 1: Cleaning up sensitive data..." -ForegroundColor Yellow

$sensitiveFiles = @(".env", "crypto_data.db", "export_results/", "results/")
foreach ($file in $sensitiveFiles) {
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would remove: $file" -ForegroundColor Cyan
        } else {
            try {
                if (Test-Path $file -PathType Container) {
                    Remove-Item $file -Recurse -Force
                } else {
                    Remove-Item $file -Force
                }
                Write-Host "  ✅ Removed: $file" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️  Could not remove: $file" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  ℹ️  Not found: $file" -ForegroundColor Gray
    }
}

# Step 2: Check .gitignore
Write-Host "`n🔒 Step 2: Checking .gitignore..." -ForegroundColor Yellow

if (Test-Path ".gitignore") {
    Write-Host "✅ .gitignore found" -ForegroundColor Green
} else {
    Write-Host "❌ .gitignore not found. Please ensure it exists!" -ForegroundColor Red
    exit 1
}

# Step 3: Initialize Git repository
Write-Host "`n📦 Step 3: Setting up Git repository..." -ForegroundColor Yellow

if (Test-Path ".git") {
    Write-Host "ℹ️  Git repository already exists" -ForegroundColor Gray
} else {
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would initialize Git repository" -ForegroundColor Cyan
    } else {
        try {
            git init
            Write-Host "✅ Git repository initialized" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to initialize Git repository" -ForegroundColor Red
            exit 1
        }
    }
}

# Step 4: Add GitHub remote
Write-Host "`n🔗 Step 4: Adding GitHub remote..." -ForegroundColor Yellow

$githubUrl = "https://github.com/edgeza/juanjohn.git"

if ($DryRun) {
    Write-Host "  [DRY RUN] Would add GitHub remote: $githubUrl" -ForegroundColor Cyan
} else {
    try {
        # Check if remote already exists
        $existingRemote = git remote get-url origin 2>$null
        if ($existingRemote) {
            if ($existingRemote -eq $githubUrl) {
                Write-Host "✅ GitHub remote already configured" -ForegroundColor Green
            } else {
                Write-Host "🔄 Updating remote URL..." -ForegroundColor Yellow
                git remote set-url origin $githubUrl
                Write-Host "✅ Remote URL updated" -ForegroundColor Green
            }
        } else {
            Write-Host "➕ Adding GitHub remote..." -ForegroundColor Yellow
            git remote add origin $githubUrl
            Write-Host "✅ GitHub remote added" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Failed to configure GitHub remote" -ForegroundColor Red
        exit 1
    }
}

# Step 5: Add files and commit
Write-Host "`n📝 Step 5: Adding files and committing..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "  [DRY RUN] Would add files and commit" -ForegroundColor Cyan
} else {
    try {
        git add .
        Write-Host "✅ Files added to staging" -ForegroundColor Green
        
        $status = git status --porcelain
        if ($status) {
            Write-Host "📋 Files to be committed:" -ForegroundColor Cyan
            $status | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            
            git commit -m "Initial commit: AutonamaDash trading system migration to GitHub"
            Write-Host "✅ Initial commit created" -ForegroundColor Green
        } else {
            Write-Host "ℹ️  No changes to commit" -ForegroundColor Gray
        }
    } catch {
        Write-Host "❌ Failed to add/commit files" -ForegroundColor Red
        exit 1
    }
}

# Step 6: Set main branch
Write-Host "`n🚀 Step 6: Setting up main branch..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "  [DRY RUN] Would set main branch" -ForegroundColor Cyan
} else {
    try {
        git branch -M main
        Write-Host "✅ Main branch set" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to set main branch" -ForegroundColor Red
        exit 1
    }
}

# Final instructions
Write-Host "`n🎉 Migration preparation complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

if ($DryRun) {
    Write-Host "This was a dry run. No changes were made." -ForegroundColor Cyan
    Write-Host "Run without -DryRun to perform the actual migration." -ForegroundColor Cyan
} else {
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Push to GitHub: git push -u origin main" -ForegroundColor White
    Write-Host "2. Set up environment: cp env.example .env" -ForegroundColor White
    Write-Host "3. Edit .env with your API keys" -ForegroundColor White
    Write-Host "4. Start services: docker-compose up -d --build" -ForegroundColor White
}

Write-Host "`nHappy Trading! 🚀📈" -ForegroundColor Green
