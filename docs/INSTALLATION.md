# 🚀 Установка AntiSpam Bot

Полное руководство по установке AntiSpam Bot на сервер.

## 📋 Требования

### Системные требования
- **ОС**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: Минимум 512MB, рекомендуется 1GB+
- **Диск**: Минимум 2GB свободного места
- **Сеть**: Доступ к интернету, открытые порты 80 и 443

### Доменные требования
- **Домен**: Действующий домен, указывающий на сервер
- **DNS**: A запись для домена и www поддомена
- **Email**: Валидный email для Let's Encrypt

## 🎯 Варианты установки

### 1. 🐳 Docker (рекомендуется)
- **Плюсы**: Простота, изоляция, легкое обновление
- **Минусы**: Больше потребление ресурсов
- **Подходит для**: Продакшена, тестирования

### 2. ⚙️ systemd (прямая установка)
- **Плюсы**: Меньше ресурсов, больше контроля
- **Минусы**: Сложнее настройка
- **Подходит для**: VPS, выделенных серверов

## 🚀 Быстрая установка

### Автоматическая установка (рекомендуется)
```bash
# Скачивание и запуск
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
cd Flame_Of_Styx_bot
sudo bash install.sh
```

### Неинтерактивная установка
```bash
# С параметрами
sudo bash install.sh --profile=prod --type=systemd --domain=your-domain.com --email=your@email.com --bot-token=your_token --admin-ids=123456789,987654321 --non-interactive
```

### Установка через Makefile
```bash
# Docker установка
make install-docker

# systemd установка
make install-systemd
```

## 📖 Подробная установка

### 1. Подготовка сервера

#### Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

#### Установка зависимостей
```bash
sudo apt install -y git curl wget python3 python3-pip python3-venv nginx certbot python3-certbot-nginx fail2ban ufw
```

### 2. Настройка бота

#### Клонирование репозитория
```bash
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
cd Flame_Of_Styx_bot
```

#### Настройка переменных окружения
```bash
cp env.template .env
nano .env
```

#### Основные переменные
```env
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321

# Native Channels (каналы, где бот является администратором)
NATIVE_CHANNEL_IDS=-10000000000

# Database Configuration
DB_PATH=db.sqlite3

# Logging Configuration
LOG_LEVEL=INFO

# Rate Limiting Configuration
RATE_LIMIT=5
RATE_INTERVAL=60

# Additional Configuration
DOMAIN=your-domain.com
EMAIL=your-email@example.com
REDIS_PASSWORD=your_redis_password
NOTIFICATION_WEBHOOK=https://api.telegram.org/bot<token>/sendMessage?chat_id=<admin_id>&text=
```

### 3. Установка зависимостей

#### Python зависимости
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Проверка установки
```bash
python bot.py --help
```

### 4. Настройка каналов

#### В канале
1. **Добавьте бота в канал как администратора**
2. **Настройте права бота:**
   - ✅ Удалять сообщения
   - ✅ Блокировать пользователей
   - ✅ Просматривать сообщения

#### В группе комментариев (если есть)
1. **Добавьте бота в группу комментариев как администратора**
2. **Настройте те же права:**
   - ✅ Удалять сообщения
   - ✅ Блокировать пользователей
   - ✅ Просматривать сообщения

#### Проверка настройки
```bash
# Запустите бота и выполните команду
/channels
```

### 5. Настройка лимитов

#### Создание файла лимитов
```bash
cat > limits.json << EOF
{
  "max_messages_per_minute": 10,
  "max_links_per_message": 3,
  "ban_duration_hours": 24,
  "suspicion_threshold": 0.4,
  "check_media_without_caption": true,
  "allow_videos_without_caption": true,
  "allow_photos_without_caption": true,
  "max_document_size_suspicious": 50000
}
EOF
```

## 🐳 Docker установка

### 1. Подготовка Docker
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Настройка конфигурации
```bash
# Копирование конфигурации
cp env.template .env
nano .env
```

### 3. Запуск контейнера
```bash
# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f
```

### 4. Управление контейнером
```bash
# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Обновление
docker-compose pull
docker-compose up -d
```

## ⚙️ systemd установка

### 1. Создание пользователя
```bash
sudo useradd -r -s /bin/false antispam
sudo mkdir -p /opt/antispam-bot
sudo chown -R antispam:antispam /opt/antispam-bot
```

### 2. Копирование файлов
```bash
sudo cp -r . /opt/antispam-bot/
sudo chown -R antispam:antispam /opt/antispam-bot
```

### 3. Создание systemd unit
```bash
sudo tee /etc/systemd/system/antispam-bot.service > /dev/null << EOF
[Unit]
Description=AntiSpam Telegram Bot
After=network.target

[Service]
Type=simple
User=antispam
Group=antispam
WorkingDirectory=/opt/antispam-bot
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/antispam-bot/venv/bin
Environment=PYTHONPATH=/opt/antispam-bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/antispam-bot/venv/bin/python /opt/antispam-bot/bot.py
Restart=always
RestartSec=10
TimeoutStartSec=30

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=antispam-bot

[Install]
WantedBy=multi-user.target
EOF
```

### 4. Запуск сервиса
```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable antispam-bot.service

# Запуск сервиса
sudo systemctl start antispam-bot.service

# Проверка статуса
sudo systemctl status antispam-bot.service
```

## 🔧 Настройка Nginx

### 1. Установка Nginx
```bash
sudo apt install -y nginx
```

### 2. Создание конфигурации
```bash
sudo tee /etc/nginx/sites-available/antispam-bot > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
```

### 3. Активация сайта
```bash
sudo ln -s /etc/nginx/sites-available/antispam-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Настройка SSL (Let's Encrypt)

### 1. Получение сертификата
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 2. Автоматическое обновление
```bash
sudo crontab -e
# Добавьте строку:
0 2 * * * certbot renew --quiet && systemctl reload nginx
```

## 🛡️ Настройка безопасности

### 1. Настройка UFW
```bash
# Включение UFW
sudo ufw enable

# Разрешение SSH
sudo ufw allow ssh

# Разрешение HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Проверка статуса
sudo ufw status
```

### 2. Настройка fail2ban
```bash
# Создание конфигурации
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
EOF

# Запуск fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📊 Мониторинг и логи

### 1. Просмотр логов
```bash
# systemd логи
sudo journalctl -u antispam-bot.service -f

# Docker логи
docker-compose logs -f

# Nginx логи
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Мониторинг через бота
```bash
# Статистика
/status

# Настройки
/settings

# Логи
/logs error
```

## 🔧 Устранение неполадок

### 1. Проблемы с запуском
```bash
# Проверка статуса
sudo systemctl status antispam-bot.service

# Перезапуск
sudo systemctl restart antispam-bot.service

# Просмотр логов
sudo journalctl -u antispam-bot.service --since "1 hour ago"
```

### 2. Проблемы с правами
```bash
# Исправление прав
sudo chown -R antispam:antispam /opt/antispam-bot
sudo chmod -R 755 /opt/antispam-bot
```

### 3. Проблемы с каналами
```bash
# Проверка через бота
/channels

# Проверка прав бота в канале
# Убедитесь, что бот админ с правами на удаление и бан
```

## 🚀 Проверка установки

### 1. Тест бота
```bash
# Отправьте команду /start боту в личку
# Должен ответить приветствием
```

### 2. Тест антиспама
```bash
# Отправьте сообщение с бот-ссылкой в канал
# Бот должен удалить сообщение и заблокировать пользователя
```

### 3. Тест команд
```bash
# /status - статистика
# /channels - каналы
# /logs - логи
# /help - справка
```

## 📞 Поддержка

Если у вас возникли проблемы:

1. Проверьте [руководство по устранению неполадок](TROUBLESHOOTING.md)
2. Создайте [Issue](../../issues)
3. Обратитесь к разработчику: [@ncux-ad](https://github.com/ncux-ad)

---

**Установка завершена! Бот готов к работе!** 🚀