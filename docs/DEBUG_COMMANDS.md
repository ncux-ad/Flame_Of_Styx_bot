# 🔍 Команды для отладки

## 🐳 Docker команды

### Основные команды
```bash
# Запуск бота
docker-compose up -d

# Остановка бота
docker-compose down

# Перезапуск бота
docker-compose restart

# Просмотр логов
docker logs antispam-bot

# Просмотр логов в реальном времени
docker logs antispam-bot -f

# Последние 50 строк логов
docker logs antispam-bot --tail=50

# Статус контейнеров
docker ps

# Статистика ресурсов
docker stats antispam-bot

# Вход в контейнер
docker exec -it antispam-bot /bin/bash
```

### Отладка Docker
```bash
# Сборка образа с отладкой
docker build --no-cache -t antispam-bot .

# Запуск с переменными окружения
docker run -e BOT_TOKEN="your_token" -e ADMIN_IDS="123,456" antispam-bot

# Просмотр всех контейнеров (включая остановленные)
docker ps -a

# Удаление всех контейнеров
docker rm $(docker ps -aq)

# Очистка неиспользуемых образов
docker image prune -a
```

## 🐍 Python команды

### Локальный запуск
```bash
# Активация виртуального окружения
.\venv\Scripts\activate.ps1

# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python bot.py

# Запуск с переменными окружения
$env:BOT_TOKEN="your_token"; $env:ADMIN_IDS="123,456"; python bot.py
```

### Отладка Python
```bash
# Проверка синтаксиса
python -m py_compile bot.py

# Проверка импортов
python -c "import app.handlers.admin"

# Запуск с отладкой
python -m pdb bot.py

# Проверка зависимостей
pip list

# Обновление зависимостей
pip install --upgrade -r requirements.txt
```

## 🌐 API Telegram команды

### Проверка API
```bash
# Проверка токена
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Получение обновлений
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"

# Проверка доступности API
ping api.telegram.org

# Проверка с таймаутом
curl --connect-timeout 10 "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Отладка API
```bash
# Подробный вывод
curl -v "https://api.telegram.org/bot<TOKEN>/getMe"

# Сохранение ответа в файл
curl "https://api.telegram.org/bot<TOKEN>/getMe" > response.json

# Проверка заголовков
curl -I "https://api.telegram.org/bot<TOKEN>/getMe"
```

## 📊 Логи и мониторинг

### Просмотр логов
```bash
# Все логи
docker logs antispam-bot

# Логи с фильтром
docker logs antispam-bot 2>&1 | grep "ERROR"

# Логи за последний час
docker logs antispam-bot --since 1h

# Логи между датами
docker logs antispam-bot --since "2025-09-12T10:00:00" --until "2025-09-12T11:00:00"
```

### Анализ логов
```bash
# Поиск ошибок
docker logs antispam-bot | grep -i error

# Поиск предупреждений
docker logs antispam-bot | grep -i warning

# Подсчет ошибок
docker logs antispam-bot | grep -c "ERROR"

# Уникальные ошибки
docker logs antispam-bot | grep "ERROR" | sort | uniq
```

## 🔧 Системные команды

### Процессы
```bash
# Поиск процессов Python
Get-Process python

# Остановка всех процессов Python
Get-Process python | Stop-Process -Force

# Поиск процессов по порту
netstat -ano | findstr :8000
```

### Сеть
```bash
# Проверка DNS
nslookup api.telegram.org

# Проверка соединения
telnet api.telegram.org 443

# Проверка маршрута
tracert api.telegram.org
```

### Файловая система
```bash
# Размер файлов
dir /s *.py

# Поиск файлов
dir /s /b *.log

# Проверка прав доступа
icacls bot.py
```

## 🐛 Отладка ошибок

### Частые ошибки
```bash
# Ошибка токена
curl "https://api.telegram.org/bot<TOKEN>/getMe" | findstr "Unauthorized"

# Ошибка сети
ping api.telegram.org

# Ошибка Docker
docker logs antispam-bot | findstr "Error"

# Ошибка Python
python -c "import app" 2>&1
```

### Диагностика
```bash
# Проверка конфигурации
echo $BOT_TOKEN
echo $ADMIN_IDS
echo $DB_PATH

# Проверка файлов
ls -la .env
ls -la bot.py
ls -la app/

# Проверка прав
ls -la *.py
```

## 📈 Производительность

### Мониторинг ресурсов
```bash
# Использование CPU и памяти
docker stats antispam-bot

# Использование диска
docker system df

# Информация о контейнере
docker inspect antispam-bot
```

### Оптимизация
```bash
# Очистка Docker
docker system prune -a

# Очистка логов
docker logs antispam-bot --tail=0 > /dev/null

# Перезапуск с очисткой
docker-compose down && docker-compose up -d
```

## 🚨 Экстренные команды

### Быстрое восстановление
```bash
# Полная перезагрузка
docker-compose down && docker-compose up -d

# Очистка и перезапуск
docker system prune -f && docker-compose up -d

# Восстановление из бэкапа
cp .env.backup .env && docker-compose restart
```

### Аварийная остановка
```bash
# Остановка всех контейнеров
docker stop $(docker ps -q)

# Удаление всех контейнеров
docker rm $(docker ps -aq)

# Очистка системы
docker system prune -a --volumes
```

## 📝 Создание отчетов

### Сбор информации для отчета
```bash
# Создание отчета об ошибке
echo "=== Bot Status ===" > debug_report.txt
docker ps >> debug_report.txt
echo "=== Logs ===" >> debug_report.txt
docker logs antispam-bot --tail=100 >> debug_report.txt
echo "=== Configuration ===" >> debug_report.txt
echo $BOT_TOKEN >> debug_report.txt
echo $ADMIN_IDS >> debug_report.txt
```

### Экспорт логов
```bash
# Экспорт логов в файл
docker logs antispam-bot > bot_logs.txt

# Экспорт с временными метками
docker logs antispam-bot -t > bot_logs_timestamped.txt

# Экспорт только ошибок
docker logs antispam-bot 2>&1 | grep -i error > errors.txt
```

---

*Команды обновлены: 12 сентября 2025*
