# 🔍 Мониторинг AntiSpam Bot

Простая и эффективная система мониторинга для AntiSpam Bot.

## 📊 Компоненты

### Netdata
- **Назначение**: Мониторинг сервера (CPU, RAM, диск, сеть)
- **Порт**: 19999
- **URL**: http://localhost:19999
- **Функции**:
  - Мониторинг ресурсов в реальном времени
  - Алерты при превышении лимитов
  - Исторические данные
  - Веб-интерфейс

### Uptime Kuma
- **Назначение**: Мониторинг доступности бота
- **Порт**: 3001
- **URL**: http://localhost:3001
- **Функции**:
  - Проверка доступности бота
  - Уведомления о недоступности
  - История uptime
  - Статус-страница

## 🚀 Установка

### Linux/macOS
```bash
# Запустить скрипт установки
chmod +x scripts/setup-monitoring.sh
./scripts/setup-monitoring.sh
```

### Windows
```powershell
# Запустить PowerShell скрипт
.\scripts\setup-monitoring.ps1
```

### Ручная установка
```bash
# Перейти в директорию мониторинга
cd monitoring

# Запустить сервисы
docker-compose up -d

# Проверить статус
docker-compose ps
```

## ⚙️ Управление

### Основные команды
```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f

# Статус сервисов
docker-compose ps

# Перезапуск
docker-compose restart
```

### Обновление
```bash
# Остановить сервисы
docker-compose down

# Обновить образы
docker-compose pull

# Запустить с новыми образами
docker-compose up -d
```

## 🔧 Настройка

### Netdata
1. Откройте http://localhost:19999
2. Настройте алерты в разделе "Alerts"
3. Настройте уведомления (email, Slack, Discord)
4. Опционально: подключите к Netdata Cloud

### Uptime Kuma
1. Откройте http://localhost:3001
2. Создайте аккаунт администратора
3. Добавьте мониторинг бота:
   - **Name**: AntiSpam Bot
   - **URL**: http://your-bot-endpoint/health
   - **Type**: HTTP(s)
   - **Interval**: 60 seconds
4. Настройте уведомления

## 📈 Мониторинг бота

### Health Check Endpoint
Добавьте в бота endpoint для проверки здоровья:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### Метрики для мониторинга
- **CPU Usage**: < 80%
- **Memory Usage**: < 85%
- **Disk Usage**: < 90%
- **Bot Response Time**: < 5s
- **Error Rate**: < 1%

## 🚨 Алерты

### Настройка алертов в Netdata
1. Перейдите в "Alerts" → "All Alerts"
2. Настройте пороги:
   - CPU > 80% → Warning
   - Memory > 85% → Warning
   - Disk > 90% → Critical
3. Настройте уведомления

### Настройка алертов в Uptime Kuma
1. Перейдите в "Settings" → "Notifications"
2. Добавьте каналы уведомлений:
   - Email
   - Telegram
   - Discord
   - Slack
3. Настройте условия срабатывания

## 📝 Логи

### Расположение логов
- **Netdata**: `/var/lib/netdata/`
- **Uptime Kuma**: `monitoring/uptime-kuma-data/`
- **Docker**: `docker-compose logs`

### Ротация логов
Логи автоматически ротируются:
- Максимальный размер: 10MB
- Количество файлов: 5
- Сжатие старых логов

## 🔒 Безопасность

### Доступ
- **Netdata**: Только локальный доступ (127.0.0.1:19999)
- **Uptime Kuma**: Настройте аутентификацию
- **Firewall**: Закройте порты от внешнего доступа

### Рекомендации
1. Используйте HTTPS в продакшене
2. Настройте аутентификацию
3. Ограничьте доступ по IP
4. Регулярно обновляйте образы

## 🆘 Troubleshooting

### Проблемы с запуском
```bash
# Проверить логи
docker-compose logs

# Проверить порты
netstat -tlnp | grep -E "(19999|3001)"

# Перезапустить сервисы
docker-compose restart
```

### Проблемы с производительностью
```bash
# Проверить использование ресурсов
docker stats

# Очистить неиспользуемые образы
docker system prune
```

### Проблемы с доступом
1. Проверьте, что порты не заняты
2. Проверьте настройки firewall
3. Проверьте логи сервисов

## 📚 Дополнительные ресурсы

- [Netdata Documentation](https://docs.netdata.cloud/)
- [Uptime Kuma Documentation](https://github.com/louislam/uptime-kuma)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
