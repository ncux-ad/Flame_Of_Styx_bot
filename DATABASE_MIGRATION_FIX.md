# 🔧 ИСПРАВЛЕНИЕ ОШИБКИ БАЗЫ ДАННЫХ

## 🐛 ПРОБЛЕМА:
```
ERROR - Error getting all channels: (sqlite3.OperationalError) no such column: channels.linked_chat_id
```

## ✅ РЕШЕНИЕ:

### 1. Подключитесь к серверу:
```bash
ssh ncux11@your_server
```

### 2. Перейдите в директорию бота:
```bash
cd ~/bots/Flame_Of_Styx_bot
```

### 3. Активируйте виртуальное окружение:
```bash
source venv/bin/activate
```

### 4. Установите alembic (если не установлен):
```bash
pip install alembic
```

### 5. Примените миграцию базы данных:
```bash
alembic upgrade head
```

### 6. Перезапустите бота:
```bash
sudo systemctl restart antispam-bot
```

### 7. Проверьте статус:
```bash
sudo systemctl status antispam-bot
```

## 🔍 ОБЪЯСНЕНИЕ:

Поля `linked_chat_id` и `is_comment_group` были добавлены в модель, но миграция не была применена к базе данных на сервере.

После применения миграции команды `/status` и `/channels` будут работать корректно.

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:

После применения миграции:
- ✅ Команда `/status` будет работать
- ✅ Команда `/channels` будет работать  
- ✅ Статистика будет показывать правильные данные
- ✅ Группы комментариев будут отображаться

## 🚨 АЛЬТЕРНАТИВНЫЙ СПОСОБ:

Если миграция не применяется, используйте ручной скрипт:
```bash
sudo bash scripts/manual_database_fix.sh
```

## 🚨 ВАЖНО:

Если миграция не применяется, проверьте:
1. Права доступа к базе данных
2. Наличие файла миграции в `alembic/versions/`
3. Корректность подключения к базе данных
4. Установлен ли alembic: `pip install alembic`
