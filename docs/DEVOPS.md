# DevOps документация для AntiSpam Bot

## 🏗️ Архитектура

### Локальная разработка (Windows)
```
┌─────────────────┐    ┌─────────────────┐
│   Docker        │    │   AntiSpam Bot  │
│   (Изоляция)    │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘
```

### Продакшен (Ubuntu 20.04)
```
┌─────────────────┐    ┌─────────────────┐
│   Systemd       │    │   AntiSpam Bot  │
│   (Сервис)      │◄──►│   (Python 3.11) │
└─────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### Локальная разработка (Windows)

```bash
# Клонирование репозитория
git clone <repository-url>
cd antispam-bot

# Настройка окружения
cp env.example .env
# Отредактируйте .env файл

# Запуск через Docker (простой)
docker-compose up -d

# Просмотр логов
docker-compose logs -f antispam-bot

# Остановка
docker-compose down
```

### Продакшен развертывание (Ubuntu 20.04)

```bash
# Автоматическое развертывание
sudo ./scripts/deploy.sh

# Настройка конфигурации
sudo nano /opt/antispam-bot/.env

# Перезапуск после настройки
sudo systemctl restart antispam-bot
```

## 🐳 Docker (только для локальной разработки)

### Простая сборка

```bash
# Сборка образа
docker build -t antispam-bot:latest .

# Запуск контейнера
docker run -d --name antispam-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  antispam-bot:latest
```

### Docker Compose (упрощенный)

```bash
# Основной сервис
docker-compose up -d

# С Redis (опционально)
docker-compose --profile redis up -d

# Просмотр логов
docker-compose logs -f antispam-bot
```

## 📊 Мониторинг (опционально)

### Простой мониторинг

```bash
# Проверка статуса сервиса
sudo systemctl status antispam-bot

# Просмотр логов
sudo journalctl -u antispam-bot -f

# Проверка использования ресурсов
htop
df -h
free -h
```

### Логирование

```bash
# Все логи
sudo journalctl -u antispam-bot

# Логи за последний час
sudo journalctl -u antispam-bot --since "1 hour ago"

# Логи с фильтром
sudo journalctl -u antispam-bot | grep ERROR
```

## 🔧 Управление сервисом

### Systemd команды (продакшен)

```bash
# Статус сервиса
sudo systemctl status antispam-bot

# Запуск/остановка
sudo systemctl start antispam-bot
sudo systemctl stop antispam-bot
sudo systemctl restart antispam-bot

# Просмотр логов
sudo journalctl -u antispam-bot -f

# Включение автозапуска
sudo systemctl enable antispam-bot
```

### Docker команды (локальная разработка)

```bash
# Статус контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f antispam-bot

# Перезапуск сервиса
docker-compose restart antispam-bot

# Остановка
docker-compose down
```

## 💾 Резервное копирование

### Простое резервное копирование

```bash
# Создание бэкапа
sudo ./scripts/backup.sh

# Восстановление из бэкапа
sudo ./scripts/restore.sh /backups/antispam-bot/antispam-backup-20240101_120000.tar.gz
```

### Автоматическое резервное копирование

```bash
# Добавление в crontab
sudo crontab -e

# Резервное копирование каждый день в 2:00
0 2 * * * /opt/antispam-bot/scripts/backup.sh

# Очистка старых бэкапов каждую неделю
0 3 * * 0 find /backups/antispam-bot -name "*.tar.gz" -mtime +30 -delete
```

## 🔒 Безопасность

### Базовые настройки

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Настройка firewall (если нужен)
sudo ufw allow 22/tcp    # SSH
sudo ufw enable

# Проверка прав доступа
sudo chown -R antispam:antispam /opt/antispam-bot
sudo chmod 600 /opt/antispam-bot/.env
```

### Обновления

```bash
# Обновление бота
sudo ./scripts/update.sh

# Обновление системы
sudo apt update && sudo apt upgrade -y
```

## 🚨 Устранение неполадок

### Проверка здоровья

```bash
# Проверка статуса сервиса
sudo systemctl status antispam-bot

# Проверка логов на ошибки
sudo journalctl -u antispam-bot | grep -i error

# Проверка использования ресурсов
htop
df -h
free -h
```

### Частые проблемы

1. **Бот не отвечает**
   - Проверить токен в .env
   - Проверить логи: `sudo journalctl -u antispam-bot -f`

2. **Высокое использование памяти**
   - Перезапустить сервис: `sudo systemctl restart antispam-bot`
   - Проверить утечки памяти в логах

3. **База данных заблокирована**
   - Остановить сервис: `sudo systemctl stop antispam-bot`
   - Проверить файл БД на целостность
   - Восстановить из бэкапа

## 📈 Масштабирование

### Простое масштабирование

```bash
# Увеличение лимитов systemd
sudo systemctl edit antispam-bot

# Добавить в файл:
[Service]
MemoryLimit=1G
CPUQuota=200%
```

## 🔄 Обновления

### Автоматическое обновление

```bash
# Обновление кода
sudo ./scripts/update.sh

# Проверка статуса
sudo systemctl status antispam-bot
```

## 📞 Поддержка

- **Логи**: `sudo journalctl -u antispam-bot -f`
- **Статус**: `sudo systemctl status antispam-bot`
- **Документация**: [docs/](docs/)
