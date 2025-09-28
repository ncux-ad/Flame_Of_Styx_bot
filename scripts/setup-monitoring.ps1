# Скрипт установки мониторинга для AntiSpam Bot (Windows)

Write-Host "🔍 Setting up monitoring for AntiSpam Bot..." -ForegroundColor Green

# Проверяем Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Создаем директорию для мониторинга
Write-Host "📁 Creating monitoring directory..." -ForegroundColor Yellow
if (!(Test-Path "monitoring")) {
    New-Item -ItemType Directory -Path "monitoring" | Out-Null
}

# Копируем конфигурацию
Write-Host "📋 Copying monitoring configuration..." -ForegroundColor Yellow
Copy-Item "monitoring/docker-compose.monitoring.yml" "monitoring/docker-compose.yml"

# Создаем .env файл для мониторинга
Write-Host "⚙️ Creating environment file..." -ForegroundColor Yellow
$envContent = @"
# Netdata Cloud (optional)
# NETDATA_CLAIM_TOKEN=your_token_here
# NETDATA_CLAIM_URL=https://app.netdata.cloud
# NETDATA_CLAIM_ROOMS=your_room_id

# Uptime Kuma
UPTIME_KUMA_DISABLE_FRAME_SAMEORIGIN=1
"@

$envContent | Out-File -FilePath "monitoring/.env" -Encoding UTF8

# Запускаем мониторинг
Write-Host "🚀 Starting monitoring services..." -ForegroundColor Yellow
Set-Location monitoring
docker-compose up -d

# Ждем запуска
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Проверяем статус
Write-Host "✅ Checking service status..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "🎉 Monitoring setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Services available:" -ForegroundColor Cyan
Write-Host "  • Netdata: http://localhost:19999" -ForegroundColor White
Write-Host "  • Uptime Kuma: http://localhost:3001" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Management commands:" -ForegroundColor Cyan
Write-Host "  • Start: cd monitoring && docker-compose up -d" -ForegroundColor White
Write-Host "  • Stop: cd monitoring && docker-compose down" -ForegroundColor White
Write-Host "  • Logs: cd monitoring && docker-compose logs -f" -ForegroundColor White
Write-Host "  • Status: cd monitoring && docker-compose ps" -ForegroundColor White
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open Netdata and configure monitoring" -ForegroundColor White
Write-Host "  2. Open Uptime Kuma and add your bot endpoint" -ForegroundColor White
Write-Host "  3. Configure alerts in the bot settings" -ForegroundColor White
Write-Host ""

Set-Location ..
