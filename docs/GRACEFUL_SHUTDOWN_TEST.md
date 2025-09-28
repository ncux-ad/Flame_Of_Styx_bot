# Тестирование Graceful Shutdown

## 🧪 Описание

Graceful shutdown обеспечивает корректное завершение работы бота при получении сигналов остановки (SIGTERM, SIGINT).

## 📋 Что тестируется

- Обработка сигналов SIGTERM и SIGINT
- Уведомления админов о запуске/остановке
- Выполнение shutdown callbacks
- Корректное закрытие ресурсов
- Timeout защита (30 секунд)

## 🚀 Запуск тестов

### Простой тест (рекомендуется)

```bash
# На сервере
cd ~/bots/Flame_Of_Styx_bot
python scripts/test-graceful-shutdown-simple.py
```

### Полный тест (требует aiogram)

```bash
# На сервере
cd ~/bots/Flame_Of_Styx_bot
python scripts/test-graceful-shutdown.py
```

## 📝 Процедура тестирования

1. **Запустите тест:**
   ```bash
   python scripts/test-graceful-shutdown-simple.py
   ```

2. **Дождитесь сообщения:**
   ```
   Bot is running... (Press Ctrl+C to test graceful shutdown)
   ```

3. **Нажмите Ctrl+C** для тестирования graceful shutdown

4. **Проверьте логи:**
   - Должно появиться сообщение о получении сигнала
   - Должно выполниться уведомление админов
   - Должны выполниться shutdown callbacks
   - Должно завершиться корректно

## ✅ Ожидаемый результат

```
2025-09-28 04:58:06,805 - __main__ - INFO - Starting test bot...
2025-09-28 04:58:06,805 - __main__ - INFO - Signal handlers configured for graceful shutdown
2025-09-28 04:58:06,805 - __main__ - INFO - Test bot started successfully
2025-09-28 04:58:06,805 - __main__ - INFO - Bot is running... (Press Ctrl+C to test graceful shutdown)
^C
2025-09-28 04:58:31,834 - __main__ - INFO - Received signal 2, initiating graceful shutdown...
2025-09-28 04:58:31,834 - __main__ - INFO - Starting graceful shutdown...
2025-09-28 04:58:31,834 - __main__ - INFO - Notification to admin 123456789: AntiSpam Bot остановлен - тестовый режим
2025-09-28 04:58:31,834 - __main__ - INFO - Shutdown notification sent to admins
2025-09-28 04:58:31,834 - __main__ - INFO - Executing 1 shutdown callbacks
2025-09-28 04:58:31,834 - __main__ - INFO - Test shutdown callback executed
2025-09-28 04:58:33,836 - __main__ - INFO - Test shutdown callback completed
2025-09-28 04:58:33,836 - __main__ - INFO - Shutdown callback executed: test_shutdown_callback
2025-09-28 04:58:33,836 - __main__ - INFO - Graceful shutdown completed successfully
2025-09-28 04:58:33,836 - __main__ - INFO - Test bot stopped
```

## 🔧 Тестирование в production

### Systemd сервис

```bash
# Остановка с graceful shutdown
sudo systemctl stop antispam-bot.service

# Проверка логов
sudo journalctl -u antispam-bot.service -f
```

### Docker

```bash
# Остановка с graceful shutdown
docker-compose -f docker-compose.prod.yml stop antispam-bot

# Проверка логов
docker-compose -f docker-compose.prod.yml logs antispam-bot
```

## ⚠️ Устранение проблем

### Проблема: "Token is invalid!"

**Решение:** Используйте простой тест:
```bash
python scripts/test-graceful-shutdown-simple.py
```

### Проблема: UnicodeEncodeError

**Решение:** Убедитесь, что используете исправленную версию скрипта.

### Проблема: Тест не останавливается

**Решение:** Нажмите Ctrl+C дважды для принудительной остановки.

## 📊 Результаты тестирования

- ✅ Обработка сигналов SIGTERM/SIGINT
- ✅ Уведомления админов
- ✅ Выполнение shutdown callbacks
- ✅ Timeout защита
- ✅ Корректное завершение

**Graceful shutdown работает корректно!** 🚀
