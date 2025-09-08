# Руководство администратора AntiSpam Bot!

## 🎯 Обзор

Это руководство для администраторов проекта AntiSpam Bot. Содержит пошаговые инструкции по развертыванию, настройке, мониторингу и устранению неполадок.

## 📋 Содержание

1. [Первоначальная настройка](#первоначальная-настройка)
2. [Развертывание обновлений](#развертывание-обновлений)
3. [Мониторинг и проверки](#мониторинг-и-проверки)
4. [Устранение неполадок](#устранение-неполадок)
5. [Вопросы команде разработки](#вопросы-команде-разработки)
6. [Чек-листы](#чек-листы)

---

## 🚀 Первоначальная настройка

### 1. Подготовка сервера

#### Системные требования
- **ОС**: Ubuntu 20.04 LTS или новее
- **RAM**: минимум 1GB, рекомендуется 2GB
- **Диск**: минимум 10GB свободного места
- **Python**: 3.11 или новее

#### Установка зависимостей
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Установка системных зависимостей
sudo apt install -y git curl wget htop

# Создание пользователя для бота
sudo useradd -m -s /bin/bash antispam
sudo usermod -aG sudo antispam
```

### 2. Клонирование и настройка

```bash
# Переключение на пользователя antispam
sudo su - antispam

# Клонирование репозитория
git clone https://github.com/your-org/antispam-bot.git
cd antispam-bot

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Конфигурация

```bash
# Копирование примера конфигурации
cp env.example .env

# Редактирование конфигурации
nano .env
```

#### Обязательные настройки в .env:
```bash
# Токен бота (получить у @BotFather)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321

# Путь к базе данных
DB_PATH=/opt/antispam-bot/data/bot.db

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=text
```

### 4. Настройка systemd сервиса

```bash
# Создание директории для данных
sudo mkdir -p /opt/antispam-bot/data
sudo mkdir -p /opt/antispam-bot/logs
sudo chown -R antispam:antispam /opt/antispam-bot

# Копирование файлов
sudo cp -r . /opt/antispam-bot/
sudo chown -R antispam:antispam /opt/antispam-bot

# Создание systemd сервиса
sudo nano /etc/systemd/system/antispam-bot.service
```

#### Содержимое antispam-bot.service:
```ini
[Unit]
Description=AntiSpam Bot
After=network.target

[Service]
Type=simple
User=antispam
Group=antispam
WorkingDirectory=/opt/antispam-bot
Environment=PATH=/opt/antispam-bot/venv/bin
ExecStart=/opt/antispam-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Запуск сервиса

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable antispam-bot

# Запуск сервиса
sudo systemctl start antispam-bot

# Проверка статуса
sudo systemctl status antispam-bot
```

---

## 🔄 Развертывание обновлений

### 1. Подготовка к обновлению

#### Проверка текущего состояния
```bash
# Проверка статуса сервиса
sudo systemctl status antispam-bot

# Проверка логов на ошибки
sudo journalctl -u antispam-bot --since "1 hour ago" | grep -i error

# Проверка использования ресурсов
htop
df -h
free -h
```

#### Создание резервной копии
```bash
# Создание бэкапа базы данных
sudo -u antispam cp /opt/antispam-bot/data/bot.db /opt/antispam-bot/data/bot.db.backup.$(date +%Y%m%d_%H%M%S)

# Создание бэкапа конфигурации
sudo -u antispam cp /opt/antispam-bot/.env /opt/antispam-bot/.env.backup.$(date +%Y%m%d_%H%M%S)

# Создание бэкапа логов
sudo -u antispam tar -czf /opt/antispam-bot/logs/backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/antispam-bot/logs/*.log
```

### 2. Процесс обновления

#### Остановка сервиса
```bash
sudo systemctl stop antispam-bot
```

#### Обновление кода
```bash
# Переключение на пользователя antispam
sudo su - antispam
cd /opt/antispam-bot

# Получение обновлений
git fetch origin
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt
```

#### Применение миграций базы данных
```bash
# Если есть миграции
alembic upgrade head
```

#### Запуск сервиса
```bash
# Выход из пользователя antispam
exit

# Запуск сервиса
sudo systemctl start antispam-bot

# Проверка статуса
sudo systemctl status antispam-bot
```

### 3. Проверка после обновления

#### Базовые проверки
```bash
# Статус сервиса
sudo systemctl status antispam-bot

# Логи за последние 5 минут
sudo journalctl -u antispam-bot --since "5 minutes ago"

# Проверка ошибок
sudo journalctl -u antispam-bot --since "5 minutes ago" | grep -i error
```

#### Функциональные проверки
```bash
# Проверка подключения к Telegram
# (отправить /start боту в личные сообщения)

# Проверка админских команд
# (отправить /help, /status, /channels, /bots)

# Проверка логирования
tail -f /opt/antispam-bot/logs/bot.log
```

---

## 📊 Мониторинг и проверки

### 1. Ежедневные проверки

#### Утренняя проверка (9:00)
```bash
# Статус сервиса
sudo systemctl status antispam-bot

# Логи за ночь
sudo journalctl -u antispam-bot --since "yesterday 18:00"

# Использование ресурсов
htop
df -h
free -h

# Размер логов
du -sh /opt/antispam-bot/logs/
```

#### Вечерняя проверка (18:00)
```bash
# Статус сервиса
sudo systemctl status antispam-bot

# Логи за день
sudo journalctl -u antispam-bot --since "today 09:00"

# Проверка ошибок
sudo journalctl -u antispam-bot --since "today 09:00" | grep -i error | wc -l
```

### 2. Еженедельные проверки

#### Проверка базы данных
```bash
# Размер базы данных
ls -lh /opt/antispam-bot/data/bot.db

# Проверка целостности (если SQLite)
sqlite3 /opt/antispam-bot/data/bot.db "PRAGMA integrity_check;"

# Количество записей в таблицах
sqlite3 /opt/antispam-bot/data/bot.db "SELECT COUNT(*) FROM users;"
sqlite3 /opt/antispam-bot/data/bot.db "SELECT COUNT(*) FROM channels;"
sqlite3 /opt/antispam-bot/data/bot.db "SELECT COUNT(*) FROM moderation_log;"
```

#### Очистка логов
```bash
# Сжатие старых логов
find /opt/antispam-bot/logs/ -name "*.log" -mtime +7 -exec gzip {} \;

# Удаление старых логов (старше 30 дней)
find /opt/antispam-bot/logs/ -name "*.log.gz" -mtime +30 -delete
```

### 3. Мониторинг производительности

#### Ключевые метрики
- **Время отклика бота**: < 2 секунд
- **Использование памяти**: < 500MB
- **Использование CPU**: < 50%
- **Размер базы данных**: < 100MB
- **Количество ошибок**: < 10 в день

#### Команды для проверки
```bash
# Использование памяти
ps aux | grep python | grep bot

# Использование CPU
top -p $(pgrep -f "python.*bot.py")

# Размер базы данных
du -h /opt/antispam-bot/data/bot.db

# Количество ошибок за день
sudo journalctl -u antispam-bot --since "today" | grep -i error | wc -l
```

---

## 🚨 Устранение неполадок

### 1. Бот не отвечает

#### Диагностика
```bash
# Проверка статуса сервиса
sudo systemctl status antispam-bot

# Проверка логов
sudo journalctl -u antispam-bot -f

# Проверка конфигурации
cat /opt/antispam-bot/.env | grep BOT_TOKEN
```

#### Возможные причины и решения
1. **Неправильный токен бота**
   ```bash
   # Проверить токен в .env
   nano /opt/antispam-bot/.env
   # Перезапустить сервис
   sudo systemctl restart antispam-bot
   ```

2. **Проблемы с сетью**
   ```bash
   # Проверить подключение к интернету
   ping google.com
   # Проверить подключение к Telegram API
   curl -s https://api.telegram.org/bot$BOT_TOKEN/getMe
   ```

3. **Ошибки в коде**
   ```bash
   # Проверить логи на ошибки
   sudo journalctl -u antispam-bot | grep -i error
   # Откатиться к предыдущей версии
   git log --oneline -5
   git checkout <previous-commit>
   ```

### 2. Высокое использование ресурсов

#### Диагностика
```bash
# Проверка использования памяти
ps aux | grep python | grep bot
htop

# Проверка использования диска
df -h
du -sh /opt/antispam-bot/logs/

# Проверка логов на утечки памяти
sudo journalctl -u antispam-bot | grep -i "memory\|leak"
```

#### Решения
1. **Перезапуск сервиса**
   ```bash
   sudo systemctl restart antispam-bot
   ```

2. **Очистка логов**
   ```bash
   # Сжатие логов
   find /opt/antispam-bot/logs/ -name "*.log" -exec gzip {} \;
   ```

3. **Проверка базы данных**
   ```bash
   # Проверка размера БД
   ls -lh /opt/antispam-bot/data/bot.db
   # Очистка старых записей (если нужно)
   ```

### 3. Проблемы с базой данных

#### Диагностика
```bash
# Проверка целостности БД
sqlite3 /opt/antispam-bot/data/bot.db "PRAGMA integrity_check;"

# Проверка блокировок
lsof /opt/antispam-bot/data/bot.db
```

#### Решения
1. **Восстановление из бэкапа**
   ```bash
   sudo systemctl stop antispam-bot
   sudo -u antispam cp /opt/antispam-bot/data/bot.db.backup.* /opt/antispam-bot/data/bot.db
   sudo systemctl start antispam-bot
   ```

2. **Пересоздание БД**
   ```bash
   sudo systemctl stop antispam-bot
   sudo -u antispam rm /opt/antispam-bot/data/bot.db
   sudo systemctl start antispam-bot
   ```

---

## ❓ Вопросы команде разработки

### 1. Перед развертыванием

#### Технические вопросы
- [ ] **Есть ли breaking changes** в новой версии?
- [ ] **Нужны ли миграции базы данных**?
- [ ] **Изменились ли переменные окружения**?
- [ ] **Есть ли новые зависимости**?
- [ ] **Какие новые функции** добавлены?

#### Вопросы по конфигурации
- [ ] **Нужно ли обновить .env файл**?
- [ ] **Изменились ли настройки rate limiting**?
- [ ] **Нужно ли обновить systemd сервис**?
- [ ] **Есть ли новые логи** для мониторинга?

### 2. После развертывания

#### Вопросы по мониторингу
- [ ] **Какие метрики** нужно отслеживать?
- [ ] **Какие ошибки** являются критическими?
- [ ] **Как часто** проверять логи?
- [ ] **Есть ли алерты** для критических ошибок?

#### Вопросы по производительности
- [ ] **Какие ресурсы** критичны для работы?
- [ ] **Есть ли рекомендации** по оптимизации?
- [ ] **Как часто** нужно перезапускать сервис?
- [ ] **Есть ли планы** по масштабированию?

### 3. При возникновении проблем

#### Вопросы для диагностики
- [ ] **Какие логи** нужно собрать?
- [ ] **Есть ли известные проблемы** с этой версией?
- [ ] **Как воспроизвести** проблему?
- [ ] **Есть ли временные решения**?

#### Вопросы по откату
- [ ] **Можно ли откатиться** к предыдущей версии?
- [ ] **Какие данные** могут быть потеряны?
- [ ] **Как восстановить** работоспособность?
- [ ] **Есть ли hotfix** для проблемы?

---

## ✅ Чек-листы

### Чек-лист развертывания

#### Перед развертыванием
- [ ] Создать резервную копию базы данных
- [ ] Создать резервную копию конфигурации
- [ ] Проверить статус текущего сервиса
- [ ] Убедиться в наличии свободного места
- [ ] Получить подтверждение от команды разработки

#### Во время развертывания
- [ ] Остановить сервис
- [ ] Обновить код
- [ ] Обновить зависимости
- [ ] Применить миграции (если есть)
- [ ] Запустить сервис
- [ ] Проверить статус

#### После развертывания
- [ ] Проверить статус сервиса
- [ ] Проверить логи на ошибки
- [ ] Протестировать основные функции
- [ ] Проверить производительность
- [ ] Уведомить команду о результатах

### Чек-лист мониторинга

#### Ежедневно
- [ ] Статус сервиса
- [ ] Логи на ошибки
- [ ] Использование ресурсов
- [ ] Размер логов

#### Еженедельно
- [ ] Целостность базы данных
- [ ] Количество записей в таблицах
- [ ] Очистка старых логов
- [ ] Проверка производительности

#### Ежемесячно
- [ ] Обновление системы
- [ ] Проверка безопасности
- [ ] Анализ производительности
- [ ] Планирование обновлений

### Чек-лист устранения неполадок

#### При проблемах с ботом
- [ ] Проверить статус сервиса
- [ ] Проверить логи
- [ ] Проверить конфигурацию
- [ ] Проверить сеть
- [ ] Связаться с командой разработки

#### При проблемах с производительностью
- [ ] Проверить использование ресурсов
- [ ] Проверить размер логов
- [ ] Проверить базу данных
- [ ] Перезапустить сервис
- [ ] Связаться с командой разработки

---

## 📞 Контакты и ресурсы

### Команда разработки
- **Lead Developer**: [имя] - [email/telegram]
- **DevOps Engineer**: [имя] - [email/telegram]
- **QA Engineer**: [имя] - [email/telegram]

### Полезные ссылки
- **Репозиторий**: https://github.com/your-org/antispam-bot
- **Документация**: https://docs.your-org.com/antispam-bot
- **Мониторинг**: https://monitoring.your-org.com
- **Логи**: https://logs.your-org.com

### Экстренные контакты
- **24/7 Support**: [телефон]
- **Emergency Telegram**: [@username]
- **Incident Channel**: [ссылка]

---

## 📝 Примечания

### Важные моменты
1. **Всегда создавайте резервные копии** перед обновлениями
2. **Тестируйте изменения** на тестовом сервере
3. **Ведите журнал** всех изменений
4. **Не стесняйтесь обращаться** к команде разработки
5. **Документируйте проблемы** и их решения

### Лучшие практики
1. **Регулярно обновляйте** систему и зависимости
2. **Мониторьте производительность** постоянно
3. **Планируйте обновления** заранее
4. **Тестируйте процедуры** восстановления
5. **Обучайте команду** новым процедурам

---

*Последнее обновление: [дата]*
*Версия документа: 1.0*
