#!/bin/bash
# Скрипт автоматического обновления Let's Encrypt сертификатов
# Automatic renewal script for Let's Encrypt certificates

set -e

echo "🔄 Проверка обновления Let's Encrypt сертификатов..."

# Переменные окружения
DOMAIN=${DOMAIN:-"antispam-bot.com"}
WEBROOT_PATH="/var/www/certbot"
RENEWAL_THRESHOLD=30

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка существования сертификатов
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    log "❌ Сертификаты не найдены. Запуск инициализации..."
    /scripts/certbot-init.sh
    exit 0
fi

# Проверка срока действия сертификата
CERT_EXPIRY=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" | cut -d= -f2)
CERT_EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( (CERT_EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

log "📅 Сертификат истекает через $DAYS_UNTIL_EXPIRY дней"

# Проверка необходимости обновления
if [ $DAYS_UNTIL_EXPIRY -lt $RENEWAL_THRESHOLD ]; then
    log "⚠️ Сертификат истекает через $DAYS_UNTIL_EXPIRY дней. Запуск обновления..."

    # Обновление сертификата
    certbot renew \
        --webroot \
        --webroot-path="$WEBROOT_PATH" \
        --non-interactive \
        --quiet

    if [ $? -eq 0 ]; then
        log "✅ Сертификат успешно обновлен!"

        # Копирование обновленных сертификатов
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "/etc/nginx/ssl/cert.pem"
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "/etc/nginx/ssl/key.pem"

        # Перезапуск nginx
        log "🔄 Перезапуск nginx..."
        nginx -s reload

        # Проверка статуса nginx
        if nginx -t; then
            log "✅ Nginx перезапущен успешно"
        else
            log "❌ Ошибка в конфигурации nginx"
            exit 1
        fi

        # Уведомление об успешном обновлении
        log "🎉 Сертификат обновлен и nginx перезапущен!"

        # Отправка уведомления (если настроено)
        if [ ! -z "$NOTIFICATION_WEBHOOK" ]; then
            curl -X POST "$NOTIFICATION_WEBHOOK" \
                -H "Content-Type: application/json" \
                -d "{\"text\":\"✅ Let's Encrypt сертификат для $DOMAIN успешно обновлен!\"}"
        fi

    else
        log "❌ Ошибка при обновлении сертификата"
        exit 1
    fi
else
    log "✅ Сертификат действителен еще $DAYS_UNTIL_EXPIRY дней. Обновление не требуется."
fi

log "🏁 Проверка завершена"
