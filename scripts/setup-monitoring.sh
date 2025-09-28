#!/bin/bash
# Скрипт установки мониторинга для AntiSpam Bot

set -e

echo "🔍 Setting up monitoring for AntiSpam Bot..."

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Создаем директорию для мониторинга
echo "📁 Creating monitoring directory..."
mkdir -p monitoring

# Копируем конфигурацию
echo "📋 Copying monitoring configuration..."
cp monitoring/docker-compose.monitoring.yml monitoring/docker-compose.yml

# Создаем .env файл для мониторинга
echo "⚙️ Creating environment file..."
cat > monitoring/.env << EOF
# Netdata Cloud (optional)
# NETDATA_CLAIM_TOKEN=your_token_here
# NETDATA_CLAIM_URL=https://app.netdata.cloud
# NETDATA_CLAIM_ROOMS=your_room_id

# Uptime Kuma
UPTIME_KUMA_DISABLE_FRAME_SAMEORIGIN=1
EOF

# Запускаем мониторинг
echo "🚀 Starting monitoring services..."
cd monitoring
docker-compose up -d

# Ждем запуска
echo "⏳ Waiting for services to start..."
sleep 10

# Проверяем статус
echo "✅ Checking service status..."
docker-compose ps

echo ""
echo "🎉 Monitoring setup completed!"
echo ""
echo "📊 Services available:"
echo "  • Netdata: http://localhost:19999"
echo "  • Uptime Kuma: http://localhost:3001"
echo ""
echo "🔧 Management commands:"
echo "  • Start: cd monitoring && docker-compose up -d"
echo "  • Stop: cd monitoring && docker-compose down"
echo "  • Logs: cd monitoring && docker-compose logs -f"
echo "  • Status: cd monitoring && docker-compose ps"
echo ""
echo "📝 Next steps:"
echo "  1. Open Netdata and configure monitoring"
echo "  2. Open Uptime Kuma and add your bot endpoint"
echo "  3. Configure alerts in the bot settings"
echo ""
