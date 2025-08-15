# AutonamaDash Quick Start Script
# Run this after cloning the repository to get started quickly

param(
    [switch]$SkipEnvSetup = $false,
    [switch]$SkipDocker = $false,
    [switch]$DryRun = $false
)

# Be strict and use UTF-8 console
$ErrorActionPreference = 'Stop'
try { chcp 65001 > $null } catch {}

Write-Host "🚀 AutonamaDash Quick Start Script" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop from https://www.docker.com/" -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ docker-compose.yml not found. Please run this script from the repository root directory." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All prerequisites met!" -ForegroundColor Green

# Step 1: Environment Setup
if (-not $SkipEnvSetup) {
    Write-Host "`n🔧 Step 1: Setting up environment..." -ForegroundColor Yellow
    
    if (Test-Path ".env") {
        Write-Host "ℹ️  .env file already exists" -ForegroundColor Gray
    } else {
        if (Test-Path "env.example") {
            if ($DryRun) {
                Write-Host "  [DRY RUN] Would copy env.example to .env" -ForegroundColor Cyan
            } else {
                try {
                    Copy-Item "env.example" ".env"
                    Write-Host "✅ Created .env from env.example" -ForegroundColor Green
                    Write-Host "⚠️  IMPORTANT: Edit .env with your actual API keys before starting services!" -ForegroundColor Yellow
                } catch {
                    Write-Host "❌ Failed to create .env file" -ForegroundColor Red
                    exit 1
                }
            }
        } else {
            Write-Host "❌ env.example not found. Cannot create .env file." -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "`n⏭️  Step 1: Skipping environment setup (SkipEnvSetup=true)" -ForegroundColor Yellow
}

# Step 2: Check environment configuration
Write-Host "`n🔍 Step 2: Checking environment configuration..." -ForegroundColor Yellow

if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    # Check for required API keys
    $requiredKeys = @("TWELVEDATA_API_KEY", "BINANCE_API_KEY", "BINANCE_SECRET_KEY")
    $missingKeys = @()
    
    foreach ($key in $requiredKeys) {
        if ($envContent -notmatch "^$key=" -or $envContent -match "^$key=your_.*_here$") {
            $missingKeys += $key
        }
    }
    
    if ($missingKeys.Count -eq 0) {
        Write-Host "✅ All required API keys are configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Missing or default API keys: $($missingKeys -join ', ')" -ForegroundColor Yellow
        Write-Host "   Please edit .env file with your actual API keys:" -ForegroundColor Cyan
        Write-Host "   - TwelveData: https://twelvedata.com/" -ForegroundColor White
        Write-Host "   - Binance: https://www.binance.com/en/my/settings/api-management" -ForegroundColor White
    }
} else {
    Write-Host "❌ .env file not found. Please run without -SkipEnvSetup first." -ForegroundColor Red
    exit 1
}

# Step 3: Start Docker services
if (-not $SkipDocker) {
    Write-Host "`n🐳 Step 3: Starting Docker services..." -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would start Docker services with: docker-compose up -d --build" -ForegroundColor Cyan
    } else {
        try {
            Write-Host "  🚀 Starting services (this may take a few minutes on first run)..." -ForegroundColor Yellow
            
            # Start services in background
            $process = Start-Process -FilePath "docker-compose" -ArgumentList "up", "-d", "--build" -NoNewWindow -PassThru
            $process.WaitForExit()
            
            if ($process.ExitCode -eq 0) {
                Write-Host "✅ Docker services started successfully!" -ForegroundColor Green
            } else {
                Write-Host "❌ Failed to start Docker services" -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "❌ Failed to start Docker services: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "`n⏭️  Step 3: Skipping Docker startup (SkipDocker=true)" -ForegroundColor Yellow
}

# Step 4: Check service status
if (-not $SkipDocker -and -not $DryRun) {
    Write-Host "`n📊 Step 4: Checking service status..." -ForegroundColor Yellow
    
    try {
        Start-Sleep -Seconds 10  # Give services time to start
        
        $status = docker-compose ps
        Write-Host "`nService Status:" -ForegroundColor Cyan
        Write-Host $status -ForegroundColor White
        
        # Check if all services are running
        $runningServices = ($status | Select-String "Up").Count
        $totalServices = ($status | Select-String -NotMatch "NAME|--").Count
        
        if ($runningServices -eq $totalServices) {
            Write-Host "`n✅ All services are running!" -ForegroundColor Green
        } else {
            Write-Host "`n⚠️  Some services may not be fully started yet" -ForegroundColor Yellow
            Write-Host "   Check logs with: docker-compose logs [service_name]" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "⚠️  Could not check service status" -ForegroundColor Yellow
    }
}

# Final instructions
Write-Host "`n🎉 Setup complete!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green

if ($DryRun) {
    Write-Host "This was a dry run. No changes were made." -ForegroundColor Cyan
    Write-Host "Run without -DryRun to perform the actual setup." -ForegroundColor Cyan
} else {
    Write-Host "Your AutonamaDash system is ready!" -ForegroundColor Green
    Write-Host "`n🌐 Access your application:" -ForegroundColor Yellow
    Write-Host "   Dashboard: http://localhost:3001" -ForegroundColor White
    Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   Monitoring: http://localhost:5555" -ForegroundColor White
    
    Write-Host "`n🔧 Useful commands:" -ForegroundColor Yellow
    Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
    Write-Host "   Stop services: docker-compose down" -ForegroundColor White
    Write-Host "   Restart: docker-compose restart" -ForegroundColor White
    
    Write-Host "`n📖 For more information:" -ForegroundColor Yellow
    Write-Host "   - README.md - Complete documentation" -ForegroundColor White
    Write-Host "   - MIGRATION_GUIDE.md - Migration instructions" -ForegroundColor White
    Write-Host "   - DOCKER_SETUP.md - Docker configuration details" -ForegroundColor White
}

Write-Host "`nHappy Trading! 🚀📈" -ForegroundColor Green

