# 🔄 Руководство по обновлению AntiSpam Bot

## 📋 **Доступные скрипты обновления**

### **1. 🆕 `update_bot.sh` (Рекомендуется)**
Современный скрипт с поддержкой модульной архитектуры:

```bash
# Обновить бота
sudo ./scripts/update_bot.sh

# Проверить доступные обновления
sudo ./scripts/update_bot.sh check

# Откатиться к предыдущей версии
sudo ./scripts/update_bot.sh rollback

# Показать логи
sudo ./scripts/update_bot.sh logs

# Показать статус
sudo ./scripts/update_bot.sh status

# Очистить старые резервные копии
sudo ./scripts/update_bot.sh cleanup
```

**Особенности:**
- ✅ Автоматическое определение типа установки (Docker/systemd)
- ✅ Создание резервных копий перед обновлением
- ✅ Поддержка модульной архитектуры
- ✅ Проверка статуса после обновления
- ✅ Автоматическая очистка старых бэкапов

### **2. 🔧 `update.sh` (Классический)**
Универсальный скрипт обновления:

```bash
# Обновить бота
sudo ./scripts/update.sh

# Проверить обновления
sudo ./scripts/update.sh check

# Откатиться
sudo ./scripts/update.sh rollback

# Показать логи
sudo ./scripts/update.sh logs
```

### **3. 🐧 `update_systemd.sh` (Только systemd)**
Скрипт для обновления systemd конфигурации:

```bash
sudo ./scripts/update_systemd.sh
```

## 🔍 **Определение директории бота**

Перед обновлением определите, где установлен бот:

```bash
# Поиск директории бота
find /opt /home -name "bot.py" -path "*/Flame_Of_Styx_bot/*" 2>/dev/null
find /opt /home -name "bot.py" -path "*/antispam-bot/*" 2>/dev/null

# Или проверьте systemd сервис
sudo systemctl show antispam-bot.service | grep ExecStart

# Или проверьте Docker контейнер
docker ps | grep antispam
```

**Возможные пути:**
- `~/bots/Flame_Of_Styx_bot` - для user профиля
- `/opt/antispam-bot` - для prod профиля
- `/opt/Flame_Of_Styx_bot` - альтернативный prod путь
- Текущая директория (если запускаете из папки бота)

## 🚀 **Быстрое обновление**

### **Для systemd установки:**
```bash
# Перейдите в директорию бота (определите правильный путь)
cd ~/bots/Flame_Of_Styx_bot  # для user профиля
# или
cd /opt/antispam-bot         # для prod профиля

sudo systemctl stop antispam-bot
git pull origin master
sudo systemctl start antispam-bot
```

### **Для Docker установки:**
```bash
# Перейдите в директорию бота (определите правильный путь)
cd ~/bots/Flame_Of_Styx_bot  # для user профиля
# или
cd /opt/antispam-bot         # для prod профиля

sudo systemctl stop antispam-bot-docker
git pull origin master
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
sudo systemctl start antispam-bot-docker
```

## 📊 **Проверка обновлений**

### **Проверка доступных обновлений:**
```bash
# Перейдите в директорию бота
cd ~/bots/Flame_Of_Styx_bot  # для user профиля
# или
cd /opt/antispam-bot         # для prod профиля

git fetch origin
git log HEAD..origin/master --oneline
```

### **Проверка текущей версии:**
```bash
# Перейдите в директорию бота
cd ~/bots/Flame_Of_Styx_bot  # для user профиля
# или
cd /opt/antispam-bot         # для prod профиля

git rev-parse HEAD
git log -1 --pretty=format:"%h - %an, %ar : %s"
```

## 🔄 **Процесс обновления**

### **1. Подготовка:**
- Создание резервной копии
- Проверка доступных обновлений
- Остановка сервиса

### **2. Обновление:**
- Получение нового кода
- Обновление зависимостей
- Запуск сервиса

### **3. Проверка:**
- Проверка статуса сервиса
- Проверка логов
- Очистка старых бэкапов

## 🛡️ **Безопасность**

### **Резервные копии:**
- Автоматическое создание перед обновлением
- Хранение в `/opt/antispam-bot-backups/`
- Автоматическая очистка старых копий (7+ дней)

### **Откат:**
```bash
# Откатиться к последней резервной копии
sudo ./scripts/update_bot.sh rollback

# Или вручную
sudo systemctl stop antispam-bot
sudo rm -rf /opt/antispam-bot
sudo cp -r /opt/antispam-bot-backups/backup-YYYYMMDD-HHMMSS /opt/antispam-bot
sudo systemctl start antispam-bot
```

## 🔍 **Диагностика проблем**

### **Проверка статуса:**
```bash
sudo systemctl status antispam-bot
sudo journalctl -u antispam-bot -f
```

### **Проверка логов:**
```bash
# Последние 50 строк
sudo journalctl -u antispam-bot -n 50

# Логи за последний час
sudo journalctl -u antispam-bot --since "1 hour ago"

# Логи с ошибками
sudo journalctl -u antispam-bot -p err
```

### **Проверка конфигурации:**
```bash
# Проверка .env файла
sudo cat /opt/antispam-bot/.env

# Проверка systemd сервиса
sudo systemctl show antispam-bot.service
```

## 📋 **Чек-лист обновления**

### **Перед обновлением:**
- [ ] Проверить доступные обновления
- [ ] Создать резервную копию
- [ ] Проверить статус сервиса
- [ ] Убедиться в наличии свободного места

### **После обновления:**
- [ ] Проверить статус сервиса
- [ ] Проверить логи на ошибки
- [ ] Протестировать основные функции
- [ ] Проверить команды бота

## ⚠️ **Важные замечания**

### **Обновление зависимостей:**
- Python зависимости обновляются автоматически
- Docker образы пересобираются при обновлении
- Конфигурация сохраняется

### **Конфигурация:**
- `.env` файл не изменяется при обновлении
- systemd конфигурация может обновиться
- Резервные копии включают конфигурацию

### **Модульная архитектура:**
- Новые модули загружаются автоматически
- Старые модули заменяются новыми
- Обратная совместимость сохраняется

## 🆘 **Поддержка**

При возникновении проблем:

1. **Проверьте логи:** `sudo journalctl -u antispam-bot -f`
2. **Проверьте статус:** `sudo systemctl status antispam-bot`
3. **Выполните откат:** `sudo ./scripts/update_bot.sh rollback`
4. **Обратитесь за помощью:** [@ncux-ad](https://github.com/ncux-ad)

---

**Обновление бота теперь простое и безопасное!** 🎉
