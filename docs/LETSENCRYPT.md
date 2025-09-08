# 🔐 Let's Encrypt SSL Сертификаты

Автоматическое получение и обновление SSL сертификатов Let's Encrypt для AntiSpam Bot.

## 📋 Обзор

Система автоматически:
- ✅ Получает SSL сертификаты от Let's Encrypt
- ✅ Обновляет сертификаты за 30 дней до истечения
- ✅ Перезапускает nginx после обновления
- ✅ Отправляет уведомления о статусе
- ✅ Проверяет валидность сертификатов

## 🚀 Быстрый старт

### 1. Настройка домена

```bash
# Автоматическая настройка домена
make setup-domain

# Или ручная настройка
export DOMAIN="your-domain.com"
export EMAIL="your-email@example.com"
```

### 2. Инициализация Let's Encrypt

```bash
# Инициализация Let's Encrypt
make letsencrypt-init
```

### 2. Запуск продакшена

```bash
# Запуск всех сервисов
make prod-up

# Проверка статуса
make letsencrypt-status
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# Основные настройки
DOMAIN=antispam-bot.com              # Ваш домен
EMAIL=admin@antispam-bot.com         # Email для уведомлений
NOTIFICATION_WEBHOOK=                # Webhook для уведомлений (опционально)

# Дополнительные настройки
RENEWAL_THRESHOLD=30                 # Дней до истечения для обновления
```

### DNS настройки

Убедитесь, что ваш домен указывает на сервер:

```bash
# Проверка DNS
nslookup your-domain.com
dig your-domain.com
```

## 📁 Структура файлов

```
nginx/
├── nginx.conf                 # Конфигурация nginx с Let's Encrypt
├── certbot.conf              # Конфигурация Certbot
├── Dockerfile.certbot        # Dockerfile для Certbot
└── certbot-scripts/
    ├── certbot-init.sh       # Инициализация сертификатов
    ├── certbot-renew.sh      # Обновление сертификатов
    └── certbot-status.sh     # Проверка статуса

scripts/
└── init-letsencrypt.sh       # Скрипт инициализации

docker-compose.prod.yml       # Продакшен конфигурация
```

## 🛠️ Команды управления

### Основные команды

```bash
# Инициализация Let's Encrypt
make letsencrypt-init

# Проверка статуса сертификатов
make letsencrypt-status

# Ручное обновление сертификатов
make letsencrypt-renew

# Просмотр логов
make letsencrypt-logs
```

### Docker команды

```bash
# Запуск продакшена
docker-compose -f docker-compose.prod.yml up -d

# Остановка продакшена
docker-compose -f docker-compose.prod.yml down

# Логи всех сервисов
docker-compose -f docker-compose.prod.yml logs -f

# Логи только Certbot
docker-compose -f docker-compose.prod.yml logs certbot
```

### Прямые команды Certbot

```bash
# Проверка статуса
docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-status.sh

# Обновление сертификатов
docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-renew.sh

# Инициализация
docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-init.sh
```

## 🔄 Автоматическое обновление

### Cron настройка

Скрипт автоматически настраивает cron для ежедневной проверки:

```bash
# Автоматическая настройка cron
0 2 * * * cd /path/to/project && docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-renew.sh >> /var/log/letsencrypt-renewal.log 2>&1
```

### Ручная настройка cron

```bash
# Редактирование crontab
sudo crontab -e

# Добавление задачи
0 2 * * * cd /path/to/antispam-bot && make letsencrypt-renew
```

## 📊 Мониторинг

### Проверка статуса

```bash
# Детальная проверка
make letsencrypt-status

# Проверка через curl
curl -I https://your-domain.com

# Проверка SSL сертификата
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### Логи

```bash
# Логи Certbot
make letsencrypt-logs

# Логи nginx
docker-compose -f docker-compose.prod.yml logs nginx

# Логи обновления
tail -f /var/log/letsencrypt-renewal.log
```

## 🚨 Устранение неполадок

### Проблемы с DNS

```bash
# Проверка DNS
nslookup your-domain.com
dig your-domain.com

# Проверка доступности
curl -I http://your-domain.com
```

### Проблемы с сертификатами

```bash
# Проверка существования сертификатов
ls -la /etc/letsencrypt/live/your-domain.com/

# Проверка валидности
openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout
```

### Проблемы с nginx

```bash
# Проверка конфигурации
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Перезапуск nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Проблемы с Certbot

```bash
# Проверка логов
docker-compose -f docker-compose.prod.yml logs certbot

# Ручной запуск
docker-compose -f docker-compose.prod.yml run --rm certbot certbot certificates
```

## 🔒 Безопасность

### Ограничения Let's Encrypt

- **Rate limits**: 50 сертификатов на домен в неделю
- **Duplicate certificates**: 5 дубликатов в неделю
- **Failed validations**: 5 неудачных попыток в час

### Рекомендации

1. **Используйте staging** для тестирования:
   ```bash
   # Тестовый режим
   certbot certonly --staging --webroot -w /var/www/certbot -d your-domain.com
   ```

2. **Мониторьте обновления**:
   ```bash
   # Настройка уведомлений
   export NOTIFICATION_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

3. **Резервное копирование**:
   ```bash
   # Копирование сертификатов
   cp -r /etc/letsencrypt/live/your-domain.com/ /backup/letsencrypt/
   ```

## 📈 Производительность

### Оптимизация nginx

```nginx
# Кеширование SSL сессий
ssl_session_cache shared:SSL:50m;
ssl_session_timeout 1d;

# HTTP/2
listen 443 ssl http2;

# Современные протоколы
ssl_protocols TLSv1.2 TLSv1.3;
```

### Мониторинг ресурсов

```bash
# Использование ресурсов
docker stats

# Логи производительности
docker-compose -f docker-compose.prod.yml logs nginx | grep "request_time"
```

## 🆘 Поддержка

### Полезные ссылки

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)

### Контакты

- **GitHub Issues**: [Создать issue](https://github.com/your-repo/issues)
- **Email**: admin@antispam-bot.com
- **Telegram**: @your_support

## 📝 Changelog

### v1.0.0
- ✅ Автоматическое получение сертификатов
- ✅ Автоматическое обновление
- ✅ Интеграция с nginx
- ✅ Мониторинг и логирование
- ✅ Docker контейнеризация
