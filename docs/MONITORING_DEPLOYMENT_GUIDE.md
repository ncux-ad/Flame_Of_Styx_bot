# 🚀 РУКОВОДСТВО ПО РАЗВЕРТЫВАНИЮ МОНИТОРИНГА

## 📋 **БЫСТРЫЙ СТАРТ (5 минут)**

### 🐳 **Вариант 1: Docker (Рекомендуется)**
```bash
# 1. Перейти в директорию проекта
cd /path/to/Flame_Of_Styx_bot

# 2. Запустить мониторинг
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# 3. Проверить статус
docker-compose -f monitoring/docker-compose.monitoring.yml ps

# 4. Открыть в браузере
# Netdata: http://your-server:19999
# Uptime Kuma: http://your-server:3001
```

### ⚙️ **Вариант 2: SystemD (Для слабых VPS)**
```bash
# 1. Запустить установку
chmod +x scripts/setup-monitoring-vps.sh
./scripts/setup-monitoring-vps.sh

# 2. Проверить статус
systemctl status netdata uptime-kuma

# 3. Открыть в браузере
# Netdata: http://your-server:19999
# Uptime Kuma: http://your-server:3001
```

---

## 🧪 **ТЕСТИРОВАНИЕ ПОСЛЕ УСТАНОВКИ**

### ✅ **Автоматический тест**
```bash
# Запустить полный тест
python3 scripts/test_monitoring_lightweight.py

# Или простой тест
python3 scripts/test_monitoring_simple.py

# Ожидаемый результат: "ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!"
```

### ✅ **Ручная проверка**
```bash
# Проверить доступность
curl http://localhost:19999/api/v1/info
curl http://localhost:3001/

# Проверить порты
netstat -tlnp | grep -E "(19999|3001)"
```

---

## 🔧 **НАСТРОЙКА МОНИТОРИНГА БОТА**

### 📊 **В Uptime Kuma**
1. Открыть http://your-server:3001
2. Создать аккаунт администратора
3. Добавить мониторы:

```
Monitor 1: AntiSpam Bot Process
- Type: HTTP(s)
- URL: http://localhost:8000/health (если есть health endpoint)
- Interval: 60 seconds

Monitor 2: Bot Log Check
- Type: Keyword
- URL: http://localhost/bot-status
- Keyword: "running"
- Interval: 300 seconds
```

### 📈 **В Netdata**
```bash
# Добавить мониторинг процесса бота
echo "python3: python3 bot.py" >> /etc/netdata/apps_groups.conf

# Перезапустить Netdata
systemctl restart netdata
```

---

## ⚡ **ОПТИМИЗАЦИЯ ДЛЯ СЛАБЫХ VPS**

### 🔧 **Netdata оптимизация**
```bash
# Редактировать конфигурацию
sudo nano /etc/netdata/netdata.conf

# Добавить настройки для экономии ресурсов:
[global]
    memory limit = 256
    update every = 5
    history = 1800
    
[plugins]
    python.d = no
    charts.d = no
    node.d = no
    
[web]
    web files owner = netdata
    web files group = netdata
```

### 🔧 **Uptime Kuma оптимизация**
```bash
# Ограничить ресурсы через systemd
sudo systemctl edit uptime-kuma

# Добавить:
[Service]
MemoryLimit=128M
CPUQuota=25%
Environment=NODE_OPTIONS="--max-old-space-size=96"
```

### 🔧 **Docker оптимизация**
```yaml
# В docker-compose.monitoring.yml добавить:
deploy:
  resources:
    limits:
      memory: 256M
      cpus: '0.5'
    reservations:
      memory: 128M
      cpus: '0.25'
```

---

## 🚨 **НАСТРОЙКА АЛЕРТОВ**

### 📧 **Uptime Kuma уведомления**
1. **Settings** → **Notifications**
2. Добавить уведомления:
   - **Telegram**: Bot Token + Chat ID
   - **Email**: SMTP настройки
   - **Discord**: Webhook URL

### 🔔 **Netdata алерты**
```bash
# Настроить алерты CPU/RAM
sudo nano /etc/netdata/health.d/cpu.conf

# Добавить:
alarm: cpu_usage
    on: system.cpu
lookup: average -3m unaligned of user,system,softirq,irq,guest
 units: %
 every: 10s
  warn: $this > 75
  crit: $this > 90
  info: CPU utilization
```

---

## 🔐 **БЕЗОПАСНОСТЬ**

### 🛡️ **Ограничить доступ**
```bash
# Настроить firewall
sudo ufw allow from YOUR_IP to any port 19999
sudo ufw allow from YOUR_IP to any port 3001

# Или через nginx с авторизацией
sudo apt install nginx apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

### 🔒 **Nginx конфигурация**
```nginx
# /etc/nginx/sites-available/monitoring
server {
    listen 80;
    server_name monitoring.yourdomain.com;
    
    location /netdata/ {
        proxy_pass http://localhost:19999/;
        auth_basic "Monitoring";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
    
    location /uptime/ {
        proxy_pass http://localhost:3001/;
        auth_basic "Monitoring";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

---

## 📊 **МОНИТОРИНГ МЕТРИК**

### 🎯 **Ключевые метрики для отслеживания**
1. **CPU Usage** < 80%
2. **Memory Usage** < 85%
3. **Disk Usage** < 90%
4. **Bot Process** - Running
5. **Network Latency** < 100ms
6. **Error Rate** < 1%

### 📈 **Дашборды**
```bash
# Импорт готовых дашбордов в Netdata
curl -o /etc/netdata/python.d/telegram_bot.conf \
  https://raw.githubusercontent.com/netdata/netdata/master/collectors/python.d.plugin/telegram/telegram.conf
```

---

## 🔄 **ОБСЛУЖИВАНИЕ**

### 🧹 **Еженедельное обслуживание**
```bash
#!/bin/bash
# weekly_maintenance.sh

# Очистка логов
sudo journalctl --vacuum-time=7d

# Проверка места на диске
df -h

# Обновление Netdata
bash <(curl -Ss https://my-netdata.io/kickstart.sh) --dont-wait

# Перезапуск сервисов
systemctl restart netdata uptime-kuma

# Тест мониторинга
python3 scripts/test_monitoring_simple.py
```

### 📦 **Резервное копирование**
```bash
# Бэкап конфигураций
tar -czf monitoring_backup_$(date +%Y%m%d).tar.gz \
  /etc/netdata/ \
  /opt/uptime-kuma/data/ \
  monitoring/

# Автоматический бэкап (crontab)
0 2 * * 0 /path/to/backup_monitoring.sh
```

---

## 🆘 **УСТРАНЕНИЕ НЕПОЛАДОК**

### ❌ **Netdata не запускается**
```bash
# Проверить логи
journalctl -u netdata -f

# Проверить конфигурацию
/usr/sbin/netdata -D

# Проверить права доступа
sudo chown -R netdata:netdata /var/lib/netdata/
sudo chown -R netdata:netdata /var/cache/netdata/
```

### ❌ **Uptime Kuma не запускается**
```bash
# Проверить логи
journalctl -u uptime-kuma -f

# Проверить Node.js
node --version
npm --version

# Переустановить зависимости
cd /opt/uptime-kuma
npm install --production
```

### ❌ **Высокое потребление ресурсов**
```bash
# Проверить потребление
htop
docker stats

# Ограничить ресурсы
systemctl edit netdata
# Добавить:
[Service]
MemoryLimit=256M
CPUQuota=50%
```

---

## 📞 **ПОДДЕРЖКА**

### 🔗 **Полезные ссылки**
- [Netdata Documentation](https://learn.netdata.cloud/)
- [Uptime Kuma GitHub](https://github.com/louislam/uptime-kuma)
- [Docker Compose Reference](https://docs.docker.com/compose/)

### 🐛 **Отчеты об ошибках**
```bash
# Собрать диагностическую информацию
python3 scripts/test_monitoring_simple.py > monitoring_debug.log 2>&1
systemctl status netdata uptime-kuma >> monitoring_debug.log
docker-compose -f monitoring/docker-compose.monitoring.yml logs >> monitoring_debug.log
```

---

## ✅ **ЧЕКЛИСТ ГОТОВНОСТИ К ПРОДАКШЕНУ**

- [ ] ✅ Мониторинг запущен и доступен
- [ ] 📊 Метрики собираются корректно
- [ ] 🚨 Настроены алерты и уведомления
- [ ] 🔐 Настроена базовая безопасность
- [ ] 🤖 Добавлен мониторинг бота
- [ ] 📦 Настроено резервное копирование
- [ ] 🧪 Автоматические тесты проходят
- [ ] 📚 Документация актуальна

**🎉 Поздравляем! Мониторинг готов к использованию!**
