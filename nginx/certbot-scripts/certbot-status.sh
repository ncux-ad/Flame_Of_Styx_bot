#!/bin/bash
# Скрипт проверки статуса Let's Encrypt сертификатов
# Status check script for Let's Encrypt certificates

set -e

echo "📊 Статус Let's Encrypt сертификатов"
echo "=================================="

# Переменные окружения
DOMAIN=${DOMAIN:-"antispam-bot.com"}

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка существования сертификатов
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    log "❌ Сертификаты не найдены для домена: $DOMAIN"
    exit 1
fi

# Информация о сертификате
log "🔐 Информация о сертификате:"
echo "Домен: $DOMAIN"
echo "Путь: /etc/letsencrypt/live/$DOMAIN/"

# Проверка срока действия
CERT_EXPIRY=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" | cut -d= -f2)
CERT_EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( (CERT_EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

echo "Дата истечения: $CERT_EXPIRY"
echo "Дней до истечения: $DAYS_UNTIL_EXPIRY"

# Проверка валидности сертификата
if openssl x509 -checkend 0 -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"; then
    echo "Статус: ✅ Действителен"
else
    echo "Статус: ❌ Истек"
fi

# Проверка цепочки сертификатов
echo ""
log "🔗 Проверка цепочки сертификатов:"
if openssl verify -CAfile "/etc/letsencrypt/live/$DOMAIN/chain.pem" "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"; then
    echo "Цепочка: ✅ Валидна"
else
    echo "Цепочка: ❌ Невалидна"
fi

# Проверка nginx конфигурации
echo ""
log "🌐 Проверка nginx конфигурации:"
if nginx -t; then
    echo "Nginx: ✅ Конфигурация корректна"
else
    echo "Nginx: ❌ Ошибка в конфигурации"
fi

# Проверка доступности HTTPS
echo ""
log "🌍 Проверка доступности HTTPS:"
if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" | grep -q "200\|301\|302"; then
    echo "HTTPS: ✅ Доступен"
else
    echo "HTTPS: ❌ Недоступен"
fi

# Рекомендации
echo ""
log "💡 Рекомендации:"
if [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
    echo "⚠️ Сертификат истекает через $DAYS_UNTIL_EXPIRY дней. Рекомендуется обновление."
elif [ $DAYS_UNTIL_EXPIRY -lt 7 ]; then
    echo "🚨 Сертификат истекает через $DAYS_UNTIL_EXPIRY дней. Требуется срочное обновление!"
else
    echo "✅ Сертификат действителен еще $DAYS_UNTIL_EXPIRY дней. Обновление не требуется."
fi

log "🏁 Проверка завершена"
