# 📋 ЧЕКЛИСТ ПРОВЕРКИ МОНИТОРИНГА

## 🎯 **БЫСТРАЯ ПРОВЕРКА (5 минут)**

### ✅ **Шаг 1: Автоматический тест**
```bash
# Запустить автоматический тест
chmod +x scripts/run_monitoring_tests.sh
./scripts/run_monitoring_tests.sh

# Результат должен быть: "🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!"
```

### ✅ **Шаг 2: Проверка веб-интерфейсов**
- [ ] **Netdata**: http://your-server:19999 - открывается и показывает метрики
- [ ] **Uptime Kuma**: http://your-server:3001 - открывается интерфейс

---

## 🔧 **ДЕТАЛЬНАЯ ПРОВЕРКА (15 минут)**

### ✅ **Docker версия**
```bash
# Проверить статус контейнеров
docker-compose -f monitoring/docker-compose.monitoring.yml ps

# Должно показать:
# netdata        Up      0.0.0.0:19999->19999/tcp
# uptime-kuma    Up      0.0.0.0:3001->3001/tcp

# Проверить логи
docker-compose -f monitoring/docker-compose.monitoring.yml logs --tail=20
```

### ✅ **SystemD версия**
```bash
# Проверить статус сервисов
systemctl status netdata
systemctl status uptime-kuma

# Должно показать: Active: active (running)

# Проверить порты
netstat -tlnp | grep -E "(19999|3001)"
```

### ✅ **Проверка ресурсов**
```bash
# Использование памяти
free -h

# Использование CPU
top -bn1 | grep -E "(netdata|uptime-kuma)"

# Место на диске
df -h
```

---

## 📊 **ФУНКЦИОНАЛЬНАЯ ПРОВЕРКА (10 минут)**

### ✅ **Netdata функциональность**
- [ ] **API работает**: `curl http://localhost:19999/api/v1/info`
- [ ] **Метрики CPU**: Графики CPU загрузки отображаются
- [ ] **Метрики RAM**: Графики памяти отображаются  
- [ ] **Метрики диска**: Графики дискового пространства отображаются
- [ ] **Сетевые метрики**: Графики сетевого трафика отображаются

### ✅ **Uptime Kuma функциональность**
- [ ] **Веб-интерфейс**: Открывается без ошибок
- [ ] **Создание мониторов**: Можно добавить новый HTTP монитор
- [ ] **Тестовый монитор**: Добавить http://httpbin.org/status/200 - должен быть UP

---

## 🚨 **ПРОВЕРКА АЛЕРТОВ (5 минут)**

### ✅ **Netdata алерты**
```bash
# Проверить конфигурацию алертов
curl "http://localhost:19999/api/v1/alarms"

# Должно вернуть JSON с алертами (может быть пустой)
```

### ✅ **Uptime Kuma уведомления**
- [ ] **Настройка уведомлений**: Добавить Telegram/Email уведомления
- [ ] **Тест уведомлений**: Отправить тестовое уведомление

---

## 🔍 **ДИАГНОСТИКА ПРОБЛЕМ**

### ❌ **Netdata не запускается**
```bash
# Проверить логи
journalctl -u netdata -f

# Проверить права доступа
ls -la /opt/netdata/
sudo chown -R netdata:netdata /opt/netdata/

# Проверить порт
sudo lsof -i :19999
```

### ❌ **Uptime Kuma не запускается**
```bash
# Проверить логи
journalctl -u uptime-kuma -f

# Проверить Node.js
node --version

# Проверить порт
sudo lsof -i :3001
```

### ❌ **Высокое потребление ресурсов**
```bash
# Ограничить ресурсы Netdata
echo "memory limit = 256" >> /etc/netdata/netdata.conf

# Ограничить частоту обновления
echo "update every = 5" >> /etc/netdata/netdata.conf

# Перезапустить
systemctl restart netdata
```

---

## 🎯 **ОПТИМИЗАЦИЯ ДЛЯ СЛАБЫХ VPS**

### ✅ **Netdata оптимизация**
```bash
# Редактировать конфигурацию
sudo nano /etc/netdata/netdata.conf

# Добавить настройки:
[global]
    memory limit = 256
    update every = 5
    history = 3600

[plugins]
    python.d = no
    charts.d = no
    node.d = no
```

### ✅ **Uptime Kuma оптимизация**
```bash
# Ограничить память через systemd
sudo systemctl edit uptime-kuma

# Добавить:
[Service]
MemoryLimit=128M
CPUQuota=25%
```

---

## 📈 **МОНИТОРИНГ БОТА**

### ✅ **Добавить мониторинг бота в Uptime Kuma**
1. **Открыть** Uptime Kuma: http://your-server:3001
2. **Добавить монитор**:
   - **Name**: AntiSpam Bot Health
   - **Type**: HTTP(s)
   - **URL**: http://localhost:8000/health (если есть health endpoint)
   - **Interval**: 60 seconds
3. **Настроить уведомления** при падении бота

### ✅ **Мониторинг процесса бота**
```bash
# Добавить в Netdata мониторинг процесса
echo "python3 bot.py" >> /etc/netdata/apps_groups.conf

# Перезапустить Netdata
systemctl restart netdata
```

---

## 🔐 **БЕЗОПАСНОСТЬ**

### ✅ **Ограничить доступ**
```bash
# Настроить firewall (только для локального доступа)
sudo ufw allow from 127.0.0.1 to any port 19999
sudo ufw allow from 127.0.0.1 to any port 3001

# Или через nginx proxy с авторизацией
```

### ✅ **Обновления**
```bash
# Обновить Netdata
bash <(curl -Ss https://my-netdata.io/kickstart.sh) --dont-wait

# Обновить Uptime Kuma (Docker)
docker-compose -f monitoring/docker-compose.monitoring.yml pull
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

---

## 📊 **ИТОГОВЫЙ ЧЕКЛИСТ**

- [ ] ✅ Автоматический тест прошел успешно
- [ ] 🌐 Netdata доступен на порту 19999
- [ ] 📊 Uptime Kuma доступен на порту 3001
- [ ] 💾 Потребление памяти < 512MB
- [ ] 🔄 Сервисы автоматически запускаются при перезагрузке
- [ ] 🚨 Настроены базовые алерты
- [ ] 🤖 Добавлен мониторинг бота
- [ ] 🔐 Настроена базовая безопасность

---

## 🆘 **ЭКСТРЕННЫЕ КОМАНДЫ**

```bash
# Полная перезагрузка мониторинга
sudo systemctl restart netdata uptime-kuma

# Очистка логов (если места мало)
sudo journalctl --vacuum-time=7d

# Проверка места на диске
df -h
du -sh /var/log/
du -sh /opt/netdata/
du -sh /opt/uptime-kuma/

# Экстренная остановка (если система тормозит)
sudo systemctl stop netdata uptime-kuma
```

---

**💡 Совет**: Сохраните этот чеклист и проверяйте мониторинг раз в неделю!
