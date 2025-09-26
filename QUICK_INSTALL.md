# ⚡ Быстрая установка AntiSpam Bot

## 🚀 Одна команда для установки

```bash
# Скачивание и установка
git clone https://github.com/your-repo/antispam-bot.git
cd antispam-bot
sudo bash install.sh
```

## 📋 Что нужно подготовить

### 1. **Домен**
- Купите домен (GoDaddy, Namecheap, etc.)
- Настройте DNS: `your-domain.com` → `YOUR_SERVER_IP`

### 2. **Telegram Bot Token**
- Напишите @BotFather
- Создайте бота: `/newbot`
- Скопируйте токен

### 3. **Admin ID**
- Напишите @userinfobot
- Скопируйте ваш ID

## 🎯 Варианты установки

### Docker (рекомендуется)
```bash
sudo bash scripts/install-docker.sh
```

### systemd (прямая установка)
```bash
sudo bash scripts/install-systemd.sh
```

## ⚙️ После установки

### Команды управления
```bash
# Запуск/остановка
sudo antispam-bot start
sudo antispam-bot stop
sudo antispam-bot restart

# Статус и логи
sudo antispam-bot status
sudo antispam-bot logs

# Обновление
sudo antispam-bot update
```

### Проверка работы
```bash
# Статус
sudo antispam-bot status

# Логи
sudo antispam-bot logs

# Веб-интерфейс
curl https://your-domain.com
```

## 🔧 Настройка

### Конфигурация
- **Docker**: `/opt/antispam-bot/.env.prod`
- **systemd**: `/etc/antispam-bot/.env`

### Основные параметры
```bash
DOMAIN=your-domain.com
EMAIL=your-email@example.com
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
```

## 🚨 Проблемы?

### DNS не работает
```bash
nslookup your-domain.com
dig your-domain.com
```

### Порты не открыты
```bash
sudo ufw allow 80
sudo ufw allow 443
```

### Логи ошибок
```bash
sudo antispam-bot logs
journalctl -u antispam-bot -f
```

## 📞 Поддержка

- **GitHub**: [Issues](https://github.com/your-repo/issues)
- **Email**: admin@antispam-bot.com
- **Telegram**: @your_support

## ✅ Готово!

После установки у вас будет:
- 🤖 Рабочий Telegram бот
- 🔐 SSL сертификат от Let's Encrypt
- 🔄 Автоматическое обновление
- 📊 Мониторинг и логи
- 🛡️ Встроенная безопасность
