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

### Интерактивная установка
```bash
# Скачивание и запуск
git clone https://github.com/your-repo/antispam-bot.git
cd antispam-bot
sudo bash install.sh
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

#### Установка базовых пакетов
```bash
sudo apt install -y curl wget git unzip htop nano vim
```

### 2. Настройка DNS

#### A записи
```
your-domain.com    A    YOUR_SERVER_IP
www.your-domain.com A    YOUR_SERVER_IP
```

#### Проверка DNS
```bash
nslookup your-domain.com
dig your-domain.com
```

### 3. Установка через Docker

#### Запуск установки
```bash
sudo bash scripts/install-docker.sh
```

#### Что происходит:
1. Установка Docker и Docker Compose
2. Настройка системы безопасности
3. Копирование файлов проекта
4. Создание systemd сервиса
5. Настройка Let's Encrypt
6. Запуск всех сервисов

### 4. Установка через systemd

#### Запуск установки
```bash
sudo bash scripts/install-systemd.sh
```

#### Что происходит:
1. Установка Python и зависимостей
2. Настройка Redis
3. Создание виртуального окружения
4. Установка nginx
5. Настройка Let's Encrypt
6. Создание systemd сервиса

## 🔧 Конфигурация

### Переменные окружения

#### Docker (.env.prod)
```bash
DOMAIN=your-domain.com
EMAIL=your-email@example.com
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
DB_PATH=db.sqlite3
REDIS_PASSWORD=your_redis_password
NOTIFICATION_WEBHOOK=
RENEWAL_THRESHOLD=30
```

#### systemd (/etc/antispam-bot/.env)
```bash
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
DB_PATH=/opt/antispam-bot/db.sqlite3
REDIS_PASSWORD=your_redis_password
NOTIFICATION_WEBHOOK=
```

### Настройка бота

#### Получение Bot Token
1. Напишите @BotFather в Telegram
2. Создайте нового бота: `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

#### Настройка Admin IDs
1. Напишите @userinfobot в Telegram
2. Скопируйте ваш ID
3. Добавьте в ADMIN_IDS

## 🛠️ Управление

### Команды управления

#### Через Makefile
```bash
# Установка
make install-docker
make install-systemd

# Управление
make bot-start
make bot-stop
make bot-restart
make bot-status
make bot-logs

# Обновление
make update

# Удаление
make uninstall
```

#### Через systemd
```bash
# Управление сервисом
sudo antispam-bot start
sudo antispam-bot stop
sudo antispam-bot restart
sudo antispam-bot status
sudo antispam-bot logs

# Обновление
sudo antispam-bot update
```

#### Через Docker
```bash
# Управление контейнерами
cd /opt/antispam-bot
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml logs -f
```

### Мониторинг

#### Проверка статуса
```bash
# Статус сервиса
sudo antispam-bot status

# Логи
sudo antispam-bot logs

# Docker контейнеры
docker ps
```

#### Проверка логов
```bash
# systemd логи
journalctl -u antispam-bot -f

# Docker логи
docker-compose -f docker-compose.prod.yml logs -f

# Файловые логи
tail -f /var/log/antispam-bot/*.log
```

## 🔄 Обновление

### Автоматическое обновление
```bash
# Проверка обновлений
sudo bash scripts/update.sh check

# Обновление
sudo bash scripts/update.sh update

# Или через Makefile
make update
```

### Ручное обновление
```bash
# Docker
cd /opt/antispam-bot
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build

# systemd
cd /opt/antispam-bot
git pull origin main
/opt/antispam-bot/venv/bin/pip install -r requirements.txt
sudo systemctl restart antispam-bot
```

## 🗑️ Удаление

### Полное удаление
```bash
sudo bash scripts/uninstall.sh
```

### Что удаляется:
- Все файлы бота
- База данных
- Логи
- Конфигурация
- systemd сервисы
- Docker контейнеры (если используется)

## 🚨 Устранение неполадок

### Проблемы с DNS
```bash
# Проверка DNS
nslookup your-domain.com
dig your-domain.com

# Проверка IP
curl ifconfig.me
```

### Проблемы с портами
```bash
# Проверка портов
netstat -tuln | grep -E ":80|:443"

# Открытие портов
sudo ufw allow 80
sudo ufw allow 443
```

### Проблемы с сертификатами
```bash
# Проверка сертификатов
sudo antispam-bot logs

# Ручное обновление
sudo certbot renew
```

### Проблемы с Docker
```bash
# Проверка контейнеров
docker ps -a

# Перезапуск
docker-compose -f docker-compose.prod.yml restart

# Очистка
docker system prune -f
```

## 📊 Мониторинг производительности

### Системные ресурсы
```bash
# CPU и память
htop

# Диск
df -h

# Сеть
netstat -i
```

### Логи производительности
```bash
# Nginx логи
tail -f /var/log/nginx/access.log

# Docker логи
docker-compose -f docker-compose.prod.yml logs nginx
```

## 🔒 Безопасность

### Настройка файрвола
```bash
# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Настройка fail2ban
```bash
# Проверка статуса
sudo systemctl status fail2ban

# Просмотр заблокированных IP
sudo fail2ban-client status sshd
```

### Обновление системы
```bash
# Обновление пакетов
sudo apt update && sudo apt upgrade -y

# Автоматические обновления
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## 📞 Поддержка

### Полезные команды
```bash
# Статус всех сервисов
sudo systemctl status antispam-bot*

# Логи всех сервисов
sudo journalctl -u antispam-bot* -f

# Проверка конфигурации
sudo nginx -t
sudo docker-compose -f docker-compose.prod.yml config
```

### Контакты
- **GitHub Issues**: [Создать issue](https://github.com/your-repo/issues)
- **Email**: admin@antispam-bot.com
- **Telegram**: @your_support

## 📝 Changelog

### v1.0.0
- ✅ Docker установка
- ✅ systemd установка
- ✅ Let's Encrypt интеграция
- ✅ Автоматическое обновление
- ✅ Скрипты управления
- ✅ Полная документация
