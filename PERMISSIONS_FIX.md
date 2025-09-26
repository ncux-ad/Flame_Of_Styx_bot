# 🔧 Исправление ошибок прав доступа к .env файлу

## ❌ Проблема
Бот не может запуститься из-за ошибки:
```
PermissionError: [Errno 13] Permission denied: '.env'
```

## ✅ Решение

### Вариант 1: Исправление прав доступа (рекомендуется)
```bash
# Подключитесь к серверу
ssh your_username@your_server

# Перейдите в директорию бота
cd ~/bots/Flame_Of_Styx_bot

# Исправьте права доступа на всю директорию
sudo chown -R your_username:your_username .

# Установите правильные права на файлы
sudo chmod -R 755 .
sudo chmod 600 .env

# Перезапустите сервис
sudo systemctl restart antispam-bot.service

# Проверьте статус
sudo systemctl status antispam-bot.service
```

### Вариант 2: Изменение пользователя systemd сервиса
```bash
# Отредактируйте systemd unit файл
sudo systemctl edit antispam-bot.service --full

# Добавьте или измените строки:
[Service]
User=your_username
Group=your_username
WorkingDirectory=/home/your_username/bots/Flame_Of_Styx_bot

# Перезагрузите systemd
sudo systemctl daemon-reload

# Перезапустите сервис
sudo systemctl restart antispam-bot.service
```

### Вариант 3: Создание нового systemd unit файла
```bash
# Создайте новый unit файл
sudo nano /etc/systemd/system/antispam-bot.service

# Добавьте содержимое:
[Unit]
Description=AntiSpam Bot for Telegram
After=network.target

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/home/your_username/bots/Flame_Of_Styx_bot
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/your_username/bots/Flame_Of_Styx_bot/venv/bin
Environment=PYTHONPATH=/home/your_username/bots/Flame_Of_Styx_bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/your_username/bots/Flame_Of_Styx_bot/venv/bin/python /home/your_username/bots/Flame_Of_Styx_bot/bot.py
Restart=always
RestartSec=10
TimeoutStartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=antispam-bot

[Install]
WantedBy=multi-user.target

# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите и запустите сервис
sudo systemctl enable antispam-bot.service
sudo systemctl start antispam-bot.service
```

## 🔍 Проверка исправления

```bash
# Проверьте статус сервиса
sudo systemctl status antispam-bot.service

# Проверьте логи
sudo journalctl -u antispam-bot.service -f -n 20

# Проверьте права доступа
ls -la ~/bots/Flame_Of_Styx_bot/.env
```

## 📝 Примечание

Проблема возникает из-за того, что:
- Файл `.env` принадлежит пользователю `your_username`
- Systemd сервис запускается от другого пользователя (обычно root)
- Нужно либо изменить права доступа, либо настроить systemd на запуск от правильного пользователя

## 🚀 После исправления

Бот должен запуститься без ошибок и начать работать нормально.
