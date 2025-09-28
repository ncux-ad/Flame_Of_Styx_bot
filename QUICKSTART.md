# 🚀 Быстрый старт AntiSpam Bot

## 📋 Требования

- **Linux сервер** (Ubuntu 20.04+ рекомендуется)
- **Python 3.8+**
- **Git**
- **Права sudo**

## ⚡ Установка за 3 шага

### 1️⃣ Клонируйте репозиторий
```bash
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
cd Flame_Of_Styx_bot
```

### 2️⃣ Настройте переменные окружения
```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте конфигурацию
nano .env
```

**Обязательные параметры:**
```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DB_PATH=bot.db
```

### 3️⃣ Запустите умную установку
```bash
chmod +x scripts/install-bot.sh
./scripts/install-bot.sh
```

**Скрипт предложит выбрать мониторинг:**
- 💪 **VPS версия** (рекомендуется для слабого VPS)
- 🔧 **Systemd версия** (стандартная)
- 🐳 **Docker версия** (если есть Docker)
- ❌ **Без мониторинга**

## ✅ Готово!

Бот установлен и запущен! 

### 🤖 Управление ботом:
```bash
# Статус
sudo systemctl status antispam-bot

# Логи
sudo journalctl -u antispam-bot -f

# Перезапуск
sudo systemctl restart antispam-bot
```

### 📊 Мониторинг (если установлен):
- **Netdata**: http://your-server:19999
- **Uptime Kuma**: http://your-server:3001

## 🔧 Дополнительные команды

### Установка только мониторинга:
```bash
# VPS версия (рекомендуется)
./scripts/setup-monitoring-vps.sh

# Systemd версия
./scripts/setup-monitoring-systemd.sh

# Docker версия
./scripts/setup-monitoring-simple.sh
```

### Настройка firewall:
```bash
./scripts/setup-firewall.sh
```

## 🆘 Помощь

- **Документация**: [MONITORING_SETUP.md](MONITORING_SETUP.md)
- **Проблемы**: [Issues](https://github.com/ncux-ad/Flame_Of_Styx_bot/issues)
- **Поддержка**: [@ncux-ad](https://github.com/ncux-ad)

## 📝 Что дальше?

1. **Настройте права бота** в каналах
2. **Добавьте бота в каналы** как администратора
3. **Настройте мониторинг** (если установлен)
4. **Проверьте работу** бота

**Удачного использования! 🎉**