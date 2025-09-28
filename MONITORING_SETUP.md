# 🔍 УСТАНОВКА МОНИТОРИНГА НА СЕРВЕРЕ

Пошаговая инструкция по установке мониторинга Netdata + Uptime Kuma на сервере.

## 📋 Требования

- **Docker** и **Docker Compose** установлены
- **Порты 19999 и 3001** свободны
- **Права sudo** для управления сервисами

## 🚀 **БЫСТРАЯ УСТАНОВКА (рекомендуется)**

### **🐳 Docker версия (простая установка):**
```bash
# 1. Перейдите в директорию проекта
cd /path/to/Flame_Of_Styx_bot

# 2. Запустите быстрый скрипт установки
chmod +x scripts/quick-setup-monitoring.sh
./scripts/quick-setup-monitoring.sh
```

### **🔧 Systemd версия (без Docker):**
```bash
# 1. Перейдите в директорию проекта
cd /path/to/Flame_Of_Styx_bot

# 2. Запустите systemd установку
chmod +x scripts/setup-monitoring-systemd.sh
./scripts/setup-monitoring-systemd.sh
```

### **Windows (PowerShell):**
```powershell
# 1. Перейдите в директорию проекта
cd D:\soft\000_Projects\Flame_Of_Styx_bot

# 2. Запустите PowerShell скрипт
.\scripts\quick-setup-monitoring.ps1
```

**Готово!** Мониторинг будет установлен и запущен автоматически.

## 📊 **СРАВНЕНИЕ ВЕРСИЙ**

| Характеристика | 🐳 Docker | 🔧 Systemd |
|---|---|---|
| **Сложность установки** | ⭐ Простая | ⭐⭐ Средняя |
| **Зависимости** | Docker + Docker Compose | Node.js + системные пакеты |
| **Производительность** | ⭐⭐ Хорошая | ⭐⭐⭐ Отличная |
| **Изоляция** | ⭐⭐⭐ Полная | ⭐ Базовая |
| **Обновления** | ⭐⭐⭐ Очень простые | ⭐⭐ Простые |
| **Ресурсы** | ⭐⭐ Больше | ⭐⭐⭐ Меньше |
| **Интеграция с системой** | ⭐ Базовая | ⭐⭐⭐ Полная |
| **Рекомендуется для** | Тестирование, разработка | Продакшн, серверы |

### **💡 Рекомендации:**
- **Docker** - если у вас уже есть Docker или нужна простота
- **Systemd** - если нужна максимальная производительность и интеграция

---

## 🔧 **РУЧНАЯ УСТАНОВКА**

### Шаг 1: Подключение к серверу
```bash
# Подключиться к серверу
ssh your-user@your-server-ip

# Перейти в директорию бота
cd ~/bots/Flame_Of_Styx_bot
```

### Шаг 2: Обновление кода
```bash
# Остановить бота (если запущен)
sudo systemctl stop antispam-bot

# Обновить код
git pull origin master

# Активировать виртуальное окружение
source venv/bin/activate

# Обновить зависимости
pip install -r requirements.txt
```

### Шаг 3: Установка мониторинга
```bash
# Сделать скрипт исполняемым
chmod +x scripts/setup-monitoring.sh

# Запустить установку
./scripts/setup-monitoring.sh
```

### Шаг 4: Проверка установки
```bash
# Проверить статус сервисов
cd monitoring
docker-compose ps

# Должно показать:
# netdata     Up   0.0.0.0:19999->19999/tcp
# uptime-kuma Up   0.0.0.0:3001->3001/tcp
```

### Шаг 5: Настройка автозапуска
```bash
# Создать systemd сервис для мониторинга
sudo tee /etc/systemd/system/monitoring.service > /dev/null <<EOF
[Unit]
Description=Monitoring Services (Netdata + Uptime Kuma)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$(whoami)/bots/Flame_Of_Styx_bot/monitoring
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable monitoring.service

# Запустить сервис
sudo systemctl start monitoring.service
```

### Шаг 6: Запуск бота
```bash
# Запустить бота
sudo systemctl start antispam-bot

# Проверить статус
sudo systemctl status antispam-bot
sudo systemctl status monitoring
```

## 🔧 Настройка

### Netdata (http://your-server:19999)
1. **Открыть** http://your-server:19999
2. **Настроить алерты**:
   - CPU > 80% → Warning
   - Memory > 85% → Warning  
   - Disk > 90% → Critical
3. **Настроить уведомления** (опционально)

### Uptime Kuma (http://your-server:3001)
1. **Открыть** http://your-server:3001
2. **Создать аккаунт** администратора
3. **Добавить мониторинг бота**:
   - **Name**: AntiSpam Bot
   - **URL**: http://localhost:8000/health (если есть health endpoint)
   - **Type**: HTTP(s)
   - **Interval**: 60 seconds
4. **Настроить уведомления**

## 📊 Доступ к мониторингу

После установки мониторинг будет доступен по адресам:

- **Netdata**: http://your-server-ip:19999
- **Uptime Kuma**: http://your-server-ip:3001

## 🔧 **УПРАВЛЕНИЕ МОНИТОРИНГОМ**

### **Автоматическое управление (рекомендуется):**

#### **🐳 Docker версия:**
```bash
# Использовать скрипт управления Docker
chmod +x scripts/monitoring-control.sh

# Команды управления
./scripts/monitoring-control.sh start     # Запустить
./scripts/monitoring-control.sh stop      # Остановить
./scripts/monitoring-control.sh restart   # Перезапустить
./scripts/monitoring-control.sh status    # Статус
./scripts/monitoring-control.sh logs      # Логи
./scripts/monitoring-control.sh check     # Проверка
./scripts/monitoring-control.sh update    # Обновить
```

#### **🔧 Systemd версия:**
```bash
# Использовать скрипт управления systemd
chmod +x scripts/monitoring-systemd-control.sh

# Команды управления
./scripts/monitoring-systemd-control.sh start     # Запустить
./scripts/monitoring-systemd-control.sh stop      # Остановить
./scripts/monitoring-systemd-control.sh restart   # Перезапустить
./scripts/monitoring-systemd-control.sh status    # Статус
./scripts/monitoring-systemd-control.sh logs      # Логи
./scripts/monitoring-systemd-control.sh enable    # Включить автозапуск
./scripts/monitoring-systemd-control.sh disable   # Отключить автозапуск
```

### **Проверка мониторинга:**
```bash
# Запустить полную проверку
chmod +x scripts/check-monitoring.sh
./scripts/check-monitoring.sh
```

### **Ручное управление:**
```bash
# Запустить мониторинг
sudo systemctl start monitoring

# Остановить мониторинг
sudo systemctl stop monitoring

# Перезапустить мониторинг
sudo systemctl restart monitoring

# Проверить статус
sudo systemctl status monitoring
```

## 🔧 Управление

### Основные команды
```bash
# Статус мониторинга
sudo systemctl status monitoring

# Остановить мониторинг
sudo systemctl stop monitoring

# Запустить мониторинг
sudo systemctl start monitoring

# Перезапустить мониторинг
sudo systemctl restart monitoring

# Логи мониторинга
cd ~/bots/Flame_Of_Styx_bot/monitoring
docker-compose logs -f
```

### Обновление мониторинга
```bash
# Остановить
sudo systemctl stop monitoring

# Обновить образы
cd ~/bots/Flame_Of_Styx_bot/monitoring
docker-compose pull

# Запустить
sudo systemctl start monitoring
```

## 🚨 Настройка алертов

### В Netdata
1. Перейдите в "Alerts" → "All Alerts"
2. Настройте пороги для:
   - **CPU Usage**: > 80%
   - **Memory Usage**: > 85%
   - **Disk Usage**: > 90%
3. Настройте уведомления (email, Slack, Discord)

### В Uptime Kuma
1. Перейдите в "Settings" → "Notifications"
2. Добавьте каналы:
   - **Email**
   - **Telegram Bot**
   - **Discord Webhook**
   - **Slack Webhook**

## 🔒 Безопасность

### Firewall (если используется)
```bash
# Разрешить доступ к мониторингу (только для вашего IP)
sudo ufw allow from YOUR_IP to any port 19999
sudo ufw allow from YOUR_IP to any port 3001

# Или разрешить всем (не рекомендуется)
sudo ufw allow 19999
sudo ufw allow 3001
```

### Nginx (опционально)
Если используете Nginx, можно настроить прокси:

```nginx
# /etc/nginx/sites-available/monitoring
server {
    listen 80;
    server_name monitoring.your-domain.com;
    
    location /netdata/ {
        proxy_pass http://127.0.0.1:19999/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /uptime/ {
        proxy_pass http://127.0.0.1:3001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🆘 Troubleshooting

### Проблемы с портами
```bash
# Проверить занятые порты
sudo netstat -tlnp | grep -E "(19999|3001)"

# Если порты заняты, остановить процессы
sudo lsof -ti:19999 | xargs sudo kill -9
sudo lsof -ti:3001 | xargs sudo kill -9
```

### Проблемы с Docker
```bash
# Проверить статус Docker
sudo systemctl status docker

# Перезапустить Docker
sudo systemctl restart docker

# Проверить логи
docker-compose logs
```

### Проблемы с правами
```bash
# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниться или выполнить
newgrp docker
```

## ✅ Проверка работы

После установки проверьте:

1. **Netdata доступен**: http://your-server:19999
2. **Uptime Kuma доступен**: http://your-server:3001
3. **Сервисы запущены**: `sudo systemctl status monitoring`
4. **Бот работает**: `sudo systemctl status antispam-bot`
5. **Логи чистые**: `docker-compose logs`

## 📞 Поддержка

При проблемах:
1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус: `sudo systemctl status monitoring`
3. Проверьте порты: `sudo netstat -tlnp | grep -E "(19999|3001)"`
4. Перезапустите: `sudo systemctl restart monitoring`
