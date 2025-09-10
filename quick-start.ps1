# WhatsApp Revenue Copilot - Quick Start Script (Windows)
# This script sets up and launches the entire system with one command

Write-Host "🚀 WhatsApp Revenue Copilot - Quick Start" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker and Docker Compose are installed" -ForegroundColor Green

# Check if .env exists
if (!(Test-Path ".env")) {
    Write-Host "📝 Creating environment file from template..." -ForegroundColor Yellow
    Copy-Item "infra\env.sample" ".env"
    Write-Host "⚠️  Please edit .env file with your actual API keys and configuration" -ForegroundColor Yellow
    Write-Host "   Required: OPENAI_API_KEY, Google credentials, WhatsApp tokens"
    Write-Host ""
    Read-Host "Press Enter when you've configured .env file"
}

# Create data directories
Write-Host "📁 Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\chroma" | Out-Null
New-Item -ItemType Directory -Force -Path "data\n8n" | Out-Null
New-Item -ItemType Directory -Force -Path "data\backups" | Out-Null

# Build and start services
Write-Host "🏗️  Building and starting services..." -ForegroundColor Yellow
Set-Location infra
docker-compose down 2>$null
docker-compose up --build -d

Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep 30

# Check service health
Write-Host "🏥 Checking service health..." -ForegroundColor Yellow

$services = @{
    "http://localhost:8001/health" = "Agent A"
    "http://localhost:8002/health" = "Agent B"
    "http://localhost:8000/health" = "Intent Classifier"
    "http://localhost:8000/api/v1/heartbeat" = "Chroma"
}

$allHealthy = $true

foreach ($service in $services.GetEnumerator()) {
    try {
        $response = Invoke-WebRequest -Uri $service.Key -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Value) is healthy" -ForegroundColor Green
        } else {
            Write-Host "❌ $($service.Value) is not responding" -ForegroundColor Red
            $allHealthy = $false
        }
    } catch {
        Write-Host "❌ $($service.Value) is not responding" -ForegroundColor Red
        $allHealthy = $false
    }
}

if ($allHealthy) {
    Write-Host ""
    Write-Host "🎉 All services are running successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 Service URLs:" -ForegroundColor Cyan
    Write-Host "   • n8n Dashboard: http://localhost:5678 (admin/admin123)"
    Write-Host "   • Agent A API: http://localhost:8001"
    Write-Host "   • Agent B API: http://localhost:8002"
    Write-Host "   • Chroma Database: http://localhost:8000"
    Write-Host "   • Intent Classifier: http://localhost:8000"
    Write-Host ""
    Write-Host "📚 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Open n8n at http://localhost:5678"
    Write-Host "   2. Import workflows from n8n/workflows/"
    Write-Host "   3. Configure WhatsApp webhook URL"
    Write-Host "   4. Test with the demo script in docs/demo-script.md"
    Write-Host ""
    Write-Host "🧪 Run tests: python test_runner.py" -ForegroundColor Cyan
    Write-Host "📖 Full documentation: README.md" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✨ Your WhatsApp Revenue Copilot is ready!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠️  Some services are not healthy. Check the logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs -f"
    Write-Host ""
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   • Verify .env configuration"
    Write-Host "   • Check Docker resource limits"
    Write-Host "   • Ensure ports 5678, 8000, 8001, 8002 are available"
}

Set-Location ..
