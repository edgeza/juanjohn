# Test Environment Script for Autonama Dashboard
# This script helps you test both local development and server production environments

param(
    [switch]$Local,
    [switch]$Server,
    [switch]$Both
)

Write-Host "🔧 Autonama Environment Test Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

if ($Local -or $Both) {
    Write-Host "`n🌐 Testing Local Development Environment..." -ForegroundColor Green
    
    # Start local development server
    Write-Host "Starting local development server on http://localhost:3001" -ForegroundColor Yellow
    Write-Host "API will automatically use: http://localhost:8000" -ForegroundColor Yellow
    Write-Host "`nTo test:" -ForegroundColor White
    Write-Host "1. Open http://localhost:3001/debug" -ForegroundColor White
    Write-Host "2. Check that it shows 'Development' mode" -ForegroundColor White
    Write-Host "3. Verify API URL is http://localhost:8000" -ForegroundColor White
    
    if ($Both) {
        Write-Host "`nPress any key to continue to server test..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

if ($Server -or $Both) {
    Write-Host "`n🌐 Testing Server Production Environment..." -ForegroundColor Green
    
    Write-Host "To test server environment:" -ForegroundColor Yellow
    Write-Host "1. Deploy to server or access via server IP" -ForegroundColor White
    Write-Host "2. Open http://129.232.243.210:3001/debug" -ForegroundColor White
    Write-Host "3. Check that it shows 'Production' mode" -ForegroundColor White
    Write-Host "4. Verify API URL is http://129.232.243.210:8000" -ForegroundColor White
}

if (-not ($Local -or $Server -or $Both)) {
    Write-Host "`nUsage:" -ForegroundColor Yellow
    Write-Host "  .\test-environments.ps1 -Local    # Test local development" -ForegroundColor White
    Write-Host "  .\test-environments.ps1 -Server   # Test server production" -ForegroundColor White
    Write-Host "  .\test-environments.ps1 -Both     # Test both environments" -ForegroundColor White
}

Write-Host "`n✅ Environment detection is automatic based on hostname:" -ForegroundColor Green
Write-Host "   - localhost/127.0.0.1/192.168.x.x → Development mode" -ForegroundColor White
Write-Host "   - 129.232.243.210 → Production mode" -ForegroundColor White
