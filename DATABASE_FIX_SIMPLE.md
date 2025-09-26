# 🔧 ПРОСТОЕ ИСПРАВЛЕНИЕ БАЗЫ ДАННЫХ

## 🐛 ПРОБЛЕМА:
```
[ERROR] Файл базы данных не найден: bot.db
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

### 3. Найдите файл базы данных:
```bash
find . -name "*.db" -o -name "*.sqlite3"
```

### 4. Используйте правильный скрипт:
```bash
sudo bash scripts/fix_database_simple.sh
```

## 🔍 ОБЪЯСНЕНИЕ:

База данных называется `db.sqlite3`, а не `bot.db`. Скрипт исправлен для поиска правильного файла.

## 📋 АЛЬТЕРНАТИВНО - РУЧНОЕ ИСПРАВЛЕНИЕ:

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Установите alembic (если не установлен)
pip install alembic

# Примените миграцию
alembic upgrade head

# Перезапустите бота
sudo systemctl restart antispam-bot
```

## ✅ РЕЗУЛЬТАТ:

После выполнения команды `/status` и `/channels` будут работать корректно.
