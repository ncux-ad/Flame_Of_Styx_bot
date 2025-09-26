# 🚀 Руководство по развертыванию

## 📋 Предварительные требования

### Системные требования
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **RAM**: Минимум 512MB, рекомендуется 1GB+
- **Диск**: 2GB свободного места
- **CPU**: 1 ядро (рекомендуется 2+)

### Программное обеспечение
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: для клонирования репозитория

## 🔧 Установка

### 1. Подготовка сервера

```bash
# Обновление системы (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
```

### 2. Получение бота

```bash
# Клонирование репозитория
git clone <repository-url>
cd ad_anti_spam_bot_full

# Создание директорий для данных
mkdir -p data logs
```

### 3. Создание Telegram бота

1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 4. Настройка конфигурации

#### Вариант A: Через .env файл

```bash
# Создание .env файла
cp env.example .env

# Редактирование конфигурации
nano .env
```

Содержимое `.env`:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321
DB_PATH=db.sqlite3
```

#### Вариант B: Через docker-compose.yml

Отредактируйте секцию `environment` в `docker-compose.yml`:

```yaml
environment:
  - BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
  - ADMIN_IDS=123456789,987654321
  - DB_PATH=db.sqlite3
```

## 🚀 Запуск

### Простой запуск

```bash
# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f antispam-bot
```

### Запуск с пересборкой

```bash
# Принудительная пересборка
docker-compose up --build -d

# Очистка кэша Docker
docker-compose build --no-cache
```

## 🔍 Проверка работы

### 1. Проверка логов

```bash
# Просмотр логов
docker logs antispam-bot

# Следить за логами в реальном времени
docker logs antispam-bot -f
```

Ожидаемый вывод:
```
2025-09-08 14:06:01,655 - __main__ - INFO - Configuration loaded successfully
2025-09-08 14:06:01,655 - __main__ - INFO - Bot token: 7977609078...
2025-09-08 14:06:01,655 - __main__ - INFO - Admin IDs: [366490333, 439304619]
2025-09-08 14:06:01,655 - __main__ - INFO - Database path: db.sqlite3
2025-09-08 14:06:01,719 - __main__ - INFO - Database tables created successfully
2025-09-08 14:06:01,719 - __main__ - INFO - Middlewares registered successfully
2025-09-08 14:06:02,018 - __main__ - INFO - Starting bot...
2025-09-08 14:06:02,019 - aiogram.dispatcher - INFO - Start polling
2025-09-08 14:06:02,331 - aiogram.dispatcher - INFO - Run polling for bot @FlameOfStyx_bot id=7977609078 - 'Пламя Стикса'
```

### 2. Тестирование бота

1. Найдите бота в Telegram по username
2. Отправьте команду `/start`
3. Проверьте ответ бота

## 🔧 Управление

### Остановка

```bash
# Остановка контейнеров
docker-compose down

# Остановка с удалением данных
docker-compose down -v
```

### Перезапуск

```bash
# Перезапуск
docker-compose restart

# Перезапуск с пересборкой
docker-compose up --build -d
```

### Обновление

```bash
# Получение обновлений
git pull

# Пересборка и перезапуск
docker-compose down
docker-compose up --build -d
```

## 📊 Мониторинг

### Логи

```bash
# Просмотр логов за последний час
docker logs --since 1h antispam-bot

# Поиск ошибок
docker logs antispam-bot 2>&1 | grep ERROR

# Сохранение логов в файл
docker logs antispam-bot > bot.log
```

### Ресурсы

```bash
# Использование ресурсов
docker stats antispam-bot

# Информация о контейнере
docker inspect antispam-bot
```

### База данных

```bash
# Подключение к базе данных
docker exec -it antispam-bot sqlite3 /app/db.sqlite3

# Резервное копирование
docker cp antispam-bot:/app/db.sqlite3 ./backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

## 🛠️ Настройка для продакшена

### 1. Настройка Docker Compose

```yaml
version: '3.8'
services:
  antispam-bot:
    build: .
    container_name: antispam-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_IDS=${ADMIN_IDS}
      - DB_PATH=${DB_PATH}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - antispam-network
    # Ограничения ресурсов
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### 2. Настройка systemd (опционально)

Создайте файл `/etc/systemd/system/antispam-bot.service`:

```ini
[Unit]
Description=AntiSpam Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/ad_anti_spam_bot_full
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl enable antispam-bot
sudo systemctl start antispam-bot
```

### 3. Настройка логирования

```bash
# Ротация логов
sudo nano /etc/logrotate.d/antispam-bot
```

Содержимое:
```
/path/to/ad_anti_spam_bot_full/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
```

## 🚨 Устранение неполадок

### Проблема: Бот не запускается

**Решение:**
1. Проверьте токен бота
2. Убедитесь, что ADMIN_IDS корректны
3. Проверьте логи: `docker logs antispam-bot`

### Проблема: Ошибка "Token is invalid"

**Решение:**
1. Проверьте правильность токена
2. Убедитесь, что токен не содержит лишних пробелов
3. Пересоздайте токен через @BotFather

### Проблема: Бот не отвечает на команды

**Решение:**
1. Проверьте, что пользователь в списке админов
2. Убедитесь, что бот запущен: `docker ps`
3. Проверьте логи на ошибки

### Проблема: Ошибки базы данных

**Решение:**
1. Проверьте права доступа к директории `data/`
2. Убедитесь, что SQLite установлен
3. Проверьте свободное место на диске

## 📞 Поддержка

Если у вас возникли проблемы:

1. Проверьте [руководство по DI](DI_BEST_PRACTICES.md)
2. Изучите [документацию для разработчиков](DEVELOPMENT.md)
3. Создайте Issue в репозитории
4. Обратитесь к логам для диагностики
