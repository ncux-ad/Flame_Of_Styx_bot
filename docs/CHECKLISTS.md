# Чек-листы AntiSpam Bot для обязательного исполнения!

## 🚀 Быстрые чек-листы для администратора

### 📋 Развертывание обновлений

#### Перед обновлением
- [ ] **Резервная копия БД**: `sudo -u antispam cp /opt/antispam-bot/data/bot.db /opt/antispam-bot/data/bot.db.backup.$(date +%Y%m%d_%H%M%S)`
- [ ] **Резервная копия .env**: `sudo -u antispam cp /opt/antispam-bot/.env /opt/antispam-bot/.env.backup.$(date +%Y%m%d_%H%M%S)`
- [ ] **Проверка статуса**: `sudo systemctl status antispam-bot`
- [ ] **Проверка ресурсов**: `htop`, `df -h`, `free -h`
- [ ] **Проверка логов**: `sudo journalctl -u antispam-bot --since "1 hour ago" | grep -i error`

#### Процесс обновления
- [ ] **Остановка сервиса**: `sudo systemctl stop antispam-bot`
- [ ] **Обновление кода**: `cd /opt/antispam-bot && git pull origin main`
- [ ] **Обновление зависимостей**: `source venv/bin/activate && pip install -r requirements.txt`
- [ ] **Миграции БД** (если есть): `alembic upgrade head`
- [ ] **Запуск сервиса**: `sudo systemctl start antispam-bot`

#### После обновления
- [ ] **Статус сервиса**: `sudo systemctl status antispam-bot`
- [ ] **Логи за 5 минут**: `sudo journalctl -u antispam-bot --since "5 minutes ago"`
- [ ] **Проверка ошибок**: `sudo journalctl -u antispam-bot --since "5 minutes ago" | grep -i error`
- [ ] **Тест бота**: отправить `/start` боту
- [ ] **Тест админки**: отправить `/help`, `/status`

---

### 🔍 Ежедневные проверки

#### Утренняя проверка (9:00)
- [ ] **Статус сервиса**: `sudo systemctl status antispam-bot`
- [ ] **Логи за ночь**: `sudo journalctl -u antispam-bot --since "yesterday 18:00"`
- [ ] **Использование памяти**: `ps aux | grep python | grep bot`
- [ ] **Использование диска**: `df -h`
- [ ] **Размер логов**: `du -sh /opt/antispam-bot/logs/`

#### Вечерняя проверка (18:00)
- [ ] **Статус сервиса**: `sudo systemctl status antispam-bot`
- [ ] **Логи за день**: `sudo journalctl -u antispam-bot --since "today 09:00"`
- [ ] **Количество ошибок**: `sudo journalctl -u antispam-bot --since "today 09:00" | grep -i error | wc -l`
- [ ] **Производительность**: `htop`

---

### 🚨 Устранение неполадок

#### Бот не отвечает
- [ ] **Статус сервиса**: `sudo systemctl status antispam-bot`
- [ ] **Логи в реальном времени**: `sudo journalctl -u antispam-bot -f`
- [ ] **Проверка токена**: `cat /opt/antispam-bot/.env | grep BOT_TOKEN`
- [ ] **Проверка сети**: `ping google.com`
- [ ] **Проверка Telegram API**: `curl -s https://api.telegram.org/bot$BOT_TOKEN/getMe`

#### Высокое использование ресурсов
- [ ] **Использование памяти**: `ps aux | grep python | grep bot`
- [ ] **Использование CPU**: `top -p $(pgrep -f "python.*bot.py")`
- [ ] **Размер логов**: `du -sh /opt/antispam-bot/logs/`
- [ ] **Перезапуск**: `sudo systemctl restart antispam-bot`

#### Проблемы с базой данных
- [ ] **Целостность БД**: `sqlite3 /opt/antispam-bot/data/bot.db "PRAGMA integrity_check;"`
- [ ] **Размер БД**: `ls -lh /opt/antispam-bot/data/bot.db`
- [ ] **Блокировки**: `lsof /opt/antispam-bot/data/bot.db`

---

### 📊 Еженедельные проверки

#### Проверка базы данных
- [ ] **Размер БД**: `ls -lh /opt/antispam-bot/data/bot.db`
- [ ] **Целостность**: `sqlite3 /opt/antispam-bot/data/bot.db "PRAGMA integrity_check;"`
- [ ] **Количество пользователей**: `sqlite3 /opt/antispam-bot/data/bot.db "SELECT COUNT(*) FROM users;"`
- [ ] **Количество каналов**: `sqlite3 /opt/antispam-bot/data/bot.db "SELECT COUNT(*) FROM channels;"`
- [ ] **Количество логов**: `sqlite3 /opt/antispam-bot/data/bot.db "SELECT COUNT(*) FROM moderation_log;"`

#### Очистка логов
- [ ] **Сжатие старых логов**: `find /opt/antispam-bot/logs/ -name "*.log" -mtime +7 -exec gzip {} \;`
- [ ] **Удаление старых логов**: `find /opt/antispam-bot/logs/ -name "*.log.gz" -mtime +30 -delete`

---

### 🔧 Вопросы команде разработки

#### Перед развертыванием
- [ ] **Есть ли breaking changes?**
- [ ] **Нужны ли миграции БД?**
- [ ] **Изменились ли переменные окружения?**
- [ ] **Есть ли новые зависимости?**
- [ ] **Какие новые функции добавлены?**

#### После развертывания
- [ ] **Какие метрики отслеживать?**
- [ ] **Какие ошибки критичны?**
- [ ] **Как часто проверять логи?**
- [ ] **Есть ли алерты?**

#### При проблемах
- [ ] **Какие логи собрать?**
- [ ] **Есть ли известные проблемы?**
- [ ] **Как воспроизвести проблему?**
- [ ] **Есть ли временные решения?**

---

### 📈 Ключевые метрики

#### Производительность
- [ ] **Время отклика**: < 2 секунд
- [ ] **Использование памяти**: < 500MB
- [ ] **Использование CPU**: < 50%
- [ ] **Размер БД**: < 100MB
- [ ] **Ошибки в день**: < 10

#### Команды для проверки
```bash
# Время отклика (тест в Telegram)
# Использование памяти
ps aux | grep python | grep bot

# Использование CPU
top -p $(pgrep -f "python.*bot.py")

# Размер БД
du -h /opt/antispam-bot/data/bot.db

# Количество ошибок
sudo journalctl -u antispam-bot --since "today" | grep -i error | wc -l
```

---

### 🆘 Экстренные процедуры

#### Быстрый откат
- [ ] **Остановка сервиса**: `sudo systemctl stop antispam-bot`
- [ ] **Восстановление БД**: `sudo -u antispam cp /opt/antispam-bot/data/bot.db.backup.* /opt/antispam-bot/data/bot.db`
- [ ] **Восстановление .env**: `sudo -u antispam cp /opt/antispam-bot/.env.backup.* /opt/antispam-bot/.env`
- [ ] **Запуск сервиса**: `sudo systemctl start antispam-bot`

#### Восстановление из бэкапа
- [ ] **Остановка сервиса**: `sudo systemctl stop antispam-bot`
- [ ] **Восстановление файлов**: `sudo -u antispam tar -xzf backup_*.tar.gz -C /opt/antispam-bot/`
- [ ] **Проверка прав**: `sudo chown -R antispam:antispam /opt/antispam-bot`
- [ ] **Запуск сервиса**: `sudo systemctl start antispam-bot`

---

### 📞 Контакты

#### Команда разработки
- **Lead Developer**: [имя] - [контакт]
- **DevOps Engineer**: [имя] - [контакт]
- **QA Engineer**: [имя] - [контакт]

#### Экстренные контакты
- **24/7 Support**: [телефон]
- **Emergency Telegram**: [@username]
- **Incident Channel**: [ссылка]

---

### 📝 Быстрые команды

#### Управление сервисом
```bash
# Статус
sudo systemctl status antispam-bot

# Запуск
sudo systemctl start antispam-bot

# Остановка
sudo systemctl stop antispam-bot

# Перезапуск
sudo systemctl restart antispam-bot

# Логи
sudo journalctl -u antispam-bot -f
```

#### Мониторинг
```bash
# Использование ресурсов
htop

# Использование диска
df -h

# Использование памяти
free -h

# Процессы Python
ps aux | grep python
```

#### Логи
```bash
# Все логи
sudo journalctl -u antispam-bot

# Логи за последний час
sudo journalctl -u antispam-bot --since "1 hour ago"

# Только ошибки
sudo journalctl -u antispam-bot | grep -i error

# Логи в реальном времени
sudo journalctl -u antispam-bot -f
```

---

*Последнее обновление: [дата]*
*Версия: 1.0*
