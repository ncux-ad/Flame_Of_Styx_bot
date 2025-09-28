#!/bin/bash
# Быстрая установка мониторинга на сервере

set -e

echo "🚀 Quick Monitoring Setup for AntiSpam Bot"
echo "=========================================="

# Проверяем, что мы на сервере
if [[ "$USER" == "root" ]]; then
    echo "❌ Не запускайте скрипт от root! Используйте обычного пользователя."
    exit 1
fi

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker сначала:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    echo "   sudo usermod -aG docker $USER"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose сначала."
    exit 1
fi

# Проверяем, что мы в правильной директории
if [[ ! -f "bot.py" ]]; then
    echo "❌ Запустите скрипт из корневой директории проекта!"
    exit 1
fi

echo "✅ Проверки пройдены"

# Останавливаем бота
echo "🛑 Останавливаем бота..."
if systemctl is-active --quiet antispam-bot; then
    sudo systemctl stop antispam-bot
    echo "✅ Бот остановлен"
else
    echo "ℹ️ Бот не был запущен"
fi

# Обновляем код
echo "📥 Обновляем код..."
git pull origin master
echo "✅ Код обновлен"

# Устанавливаем мониторинг
echo "🔍 Устанавливаем мониторинг..."
chmod +x scripts/setup-monitoring.sh
./scripts/setup-monitoring.sh

# Создаем systemd сервис
echo "⚙️ Настраиваем автозапуск..."
sudo tee /etc/systemd/system/monitoring.service > /dev/null <<EOF
[Unit]
Description=Monitoring Services (Netdata + Uptime Kuma)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)/monitoring
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
sudo systemctl daemon-reload
sudo systemctl enable monitoring.service
sudo systemctl start monitoring.service

echo "✅ Мониторинг настроен и запущен"

# Запускаем бота
echo "🤖 Запускаем бота..."
sudo systemctl start antispam-bot

# Проверяем статус
echo "📊 Проверяем статус..."
echo ""
echo "=== СТАТУС СЕРВИСОВ ==="
sudo systemctl status antispam-bot --no-pager -l
echo ""
sudo systemctl status monitoring --no-pager -l
echo ""

# Проверяем порты
echo "=== ПРОВЕРКА ПОРТОВ ==="
if netstat -tlnp 2>/dev/null | grep -q ":19999"; then
    echo "✅ Netdata: http://$(hostname -I | awk '{print $1}'):19999"
else
    echo "❌ Netdata не запущен"
fi

if netstat -tlnp 2>/dev/null | grep -q ":3001"; then
    echo "✅ Uptime Kuma: http://$(hostname -I | awk '{print $1}'):3001"
else
    echo "❌ Uptime Kuma не запущен"
fi

echo ""
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo ""
echo "📊 Доступ к мониторингу:"
echo "  • Netdata: http://$(hostname -I | awk '{print $1}'):19999"
echo "  • Uptime Kuma: http://$(hostname -I | awk '{print $1}'):3001"
echo ""
echo "🔧 Управление:"
echo "  • Статус: sudo systemctl status monitoring"
echo "  • Логи: cd monitoring && docker-compose logs -f"
echo "  • Остановить: sudo systemctl stop monitoring"
echo "  • Запустить: sudo systemctl start monitoring"
echo ""
echo "📝 Следующие шаги:"
echo "  1. Откройте Netdata и настройте алерты"
echo "  2. Откройте Uptime Kuma и добавьте мониторинг бота"
echo "  3. Настройте уведомления"
echo ""
