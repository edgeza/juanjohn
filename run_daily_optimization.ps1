param(
    [switch]$QuickUpdateFirst = $true,
    [switch]$SkipDocker = $false,
    [switch]$DirectConsole = $true
)

# Be strict and use UTF-8 console for clean tqdm rendering
$ErrorActionPreference = 'Stop'
try { chcp 65001 > $null } catch {}

# Daily Optimization Script for Autonama (Custom Engine)
Write-Host "Starting daily optimization (custom engine pipeline)..." -ForegroundColor Green

# Ensure we can run with the correct Conda environment (best-effort)
Write-Host "Activating conda environment..." -ForegroundColor Yellow
try {
    conda activate enigma311
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Conda environment activated successfully!" -ForegroundColor Green
    } else {
        Write-Host "Could not activate conda env; proceeding with 'conda run' wrappers" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Conda activation not available; proceeding with 'conda run' wrappers" -ForegroundColor Yellow
}

# Prevent Python from loading user site-packages that can shadow Conda packages
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONFAULTHANDLER = '1'

# Preflight: verify core dependencies (non-fatal)
Write-Host "Preflight: Checking core Python dependencies..." -ForegroundColor Yellow
try {
    conda run -n enigma311 python -c "import numpy, pandas, optuna; print('numpy', numpy.__version__, 'pandas', pandas.__version__, 'optuna', optuna.__version__)"
} catch {
    Write-Host "Preflight check encountered an issue; continuing." -ForegroundColor Yellow
}

# Optional Step 0: Ensure data is downloaded & a quick sanity export exists (top 100, no optimization)
if ($QuickUpdateFirst) {
    Write-Host "Step 0: Quick data update + 100-asset analysis (no optimization)" -ForegroundColor Yellow
    Push-Location
    try {
        Set-Location $PSScriptRoot
        if (Test-Path "autonama.engine/run_quick_100.py") { Set-Location autonama.engine }
        $env:PYTHONUNBUFFERED = '1'
        if ($DirectConsole) {
            conda run -n enigma311 python -u run_quick_100.py
        } else {
            $quickLog = Join-Path $PSScriptRoot ("autonama.engine\\quick_100_" + (Get-Date -Format yyyyMMdd_HHmmss) + ".log")
            conda run -n enigma311 python -u run_quick_100.py 2>&1 | Tee-Object -FilePath $quickLog
        }
        $quickExit = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($quickExit -ne 0) {
        Write-Host "Step 0 completed with exit code $quickExit (continuing)" -ForegroundColor Yellow
        $LASTEXITCODE = 0
    }
}

# Step 1: Run full optimization (downloads/updates data, analyzes top 100, exports)
Write-Host "Step 1: Running complete optimization (with exports)..." -ForegroundColor Yellow
Push-Location
try {
    # Ensure we operate relative to the script directory (repo root)
    Set-Location $PSScriptRoot
    if (Test-Path "autonama.engine/run_complete_optimization.py") {
        Set-Location autonama.engine
    } elseif (Test-Path "run_complete_optimization.py") {
        # already in engine dir
    } else {
        throw "Cannot find run_complete_optimization.py"
    }
    # Ensure unbuffered output so progress streams live (use conda run to guarantee env)
    $env:PYTHONUNBUFFERED = '1'
    if ($DirectConsole) {
        conda run -n enigma311 python -u run_complete_optimization.py
    } else {
        $optLog = Join-Path $PSScriptRoot ("autonama.engine\\complete_optimization_" + (Get-Date -Format yyyyMMdd_HHmmss) + ".log")
        conda run -n enigma311 python -u run_complete_optimization.py 2>&1 | Tee-Object -FilePath $optLog
    }
} finally {
    Pop-Location
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Optimization failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Optimization completed successfully!" -ForegroundColor Green

# Step 2: Ensure Docker is running and bring up containers (if not skipped)
if ($SkipDocker) {
    Write-Host "Step 2: Skipped Docker startup (SkipDocker=true)" -ForegroundColor Yellow
} else {
    Write-Host "Step 2: Ensuring Docker Desktop and containers are running..." -ForegroundColor Yellow

    # Wait for Docker daemon to be available (up to ~60s)
    $dockerAvailable = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            & docker version 1>$null 2>$null
            if ($LASTEXITCODE -eq 0) { $dockerAvailable = $true; break }
        } catch {
            $dockerAvailable = $false
        }
        Start-Sleep -Seconds 2
    }

    if (-not $dockerAvailable) {
        Write-Host "Docker Desktop is not running. Please start Docker Desktop and rerun." -ForegroundColor Red
        exit 1
    }

    Push-Location
    try {
        Set-Location $PSScriptRoot

        # Prefer Docker Compose V2; fallback to legacy docker-compose
        $composeCmd = "docker compose"
        $composeCheck = (& docker compose version 2>$null)
        if (-not $composeCheck) { $composeCmd = "docker-compose" }

        # Resolve compose file path robustly
        $composeCandidates = @(
            (Join-Path $PSScriptRoot 'docker-compose.yml'),
            (Join-Path $PSScriptRoot 'docker-compose.yaml'),
            (Join-Path $PSScriptRoot 'compose.yml'),
            (Join-Path $PSScriptRoot 'compose.yaml')
        )
        $composeFile = $composeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

        if ($composeFile) {
            Write-Host "Bringing up Docker services (build if needed)..." -ForegroundColor Yellow
            iex "$composeCmd -f `"$composeFile`" up -d --build | Out-String | Write-Host"
        } else {
            Write-Host "No Docker compose file found; skipping container orchestration." -ForegroundColor Yellow
        }
    } finally {
        Pop-Location
    }
}

# Step 3: Ingest results for the live Docker dashboard
Write-Host "Step 3: Ingesting latest export files for Docker web..." -ForegroundColor Yellow
Push-Location
try {
    # Ensure we operate relative to the script directory (repo root)
    Set-Location $PSScriptRoot
    if (Test-Path "autonama.engine/ingest_to_docker.py") {
        Set-Location autonama.engine
    } elseif (Test-Path "ingest_to_docker.py") {
        # already in engine dir
    } else {
        throw "Cannot find ingest_to_docker.py"
    }
    $env:PYTHONUNBUFFERED = '1'
    if ($DirectConsole) {
        conda run -n enigma311 python -u ingest_to_docker.py
    } else {
        $ingLog = Join-Path $PSScriptRoot ("autonama.engine\\ingest_to_docker_" + (Get-Date -Format yyyyMMdd_HHmmss) + ".log")
        conda run -n enigma311 python -u ingest_to_docker.py 2>&1 | Tee-Object -FilePath $ingLog
    }
} finally {
    Pop-Location
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker ingestion failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Docker ingestion completed successfully!" -ForegroundColor Green

Write-Host "Daily optimization complete!" -ForegroundColor Green
Write-Host "Open http://localhost:3001 to view the updated dashboard" -ForegroundColor Cyan 