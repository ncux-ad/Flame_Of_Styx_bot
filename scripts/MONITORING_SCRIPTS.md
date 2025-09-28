# 📊 Скрипты мониторинга

## 🚀 Главный скрипт

### `install-monitoring.sh`
**Мастер-скрипт с выбором вариантов установки**

```bash
chmod +x scripts/install-monitoring.sh
./scripts/install-monitoring.sh
```

**Варианты установки:**
1. 🐳 **Docker** (рекомендуется) - простая установка
2. ⚙️ **Systemd** - оптимизировано для VPS
3. 🔧 **Принудительное исправление** - исправляет проблемы
4. 📊 **Только Netdata** - системный мониторинг
5. ❌ **Отмена**

---

## 🔧 Специализированные скрипты

### Docker версии

#### `install-monitoring-simple.sh`
**Простая Docker установка (рекомендуется)**
```bash
chmod +x scripts/install-monitoring-simple.sh
./scripts/install-monitoring-simple.sh
```

**Особенности:**
- ✅ Работает всегда
- ✅ Изолированная среда
- ✅ Автоматическая сборка
- ✅ Простая установка

#### `install-monitoring-docker-fallback.sh`
**Docker fallback для сложных случаев**
```bash
chmod +x scripts/install-monitoring-docker-fallback.sh
./scripts/install-monitoring-docker-fallback.sh
```

### Systemd версии

#### `build-uptime-kuma.sh`
**Полная сборка Uptime Kuma с фронтендом**
```bash
chmod +x scripts/build-uptime-kuma.sh
./scripts/build-uptime-kuma.sh
```

**Особенности:**
- ✅ Полная сборка фронтенда
- ✅ Оптимизировано для VPS
- ✅ Нет зависимости от Docker

#### `setup-monitoring-vps.sh`
**VPS-оптимизированная установка**
```bash
chmod +x scripts/setup-monitoring-vps.sh
./scripts/setup-monitoring-vps.sh
```

**Особенности:**
- ✅ Ограничения ресурсов
- ✅ Отключены тяжелые плагины
- ✅ Минимальная история

#### `force-fix-uptime-kuma.sh`
**Принудительное исправление Uptime Kuma**
```bash
chmod +x scripts/force-fix-uptime-kuma.sh
./scripts/force-fix-uptime-kuma.sh
```

**Особенности:**
- ✅ Полная переустановка
- ✅ Root метод установки
- ✅ Тестирование запуска

### Только Netdata

#### `install-netdata-only.sh`
**Установка только Netdata**
```bash
chmod +x scripts/install-netdata-only.sh
./scripts/install-netdata-only.sh
```

**Особенности:**
- ✅ Только системный мониторинг
- ✅ Без Uptime Kuma
- ✅ Минимальная установка

---

## 🛠️ Управление мониторингом

### Docker версия
```bash
cd monitoring
docker-compose ps          # статус
docker-compose logs        # логи
docker-compose down        # остановить
docker-compose up -d       # запустить
```

### Systemd версия
```bash
# Netdata
sudo systemctl status netdata
sudo systemctl restart netdata

# Uptime Kuma
sudo systemctl status uptime-kuma
sudo systemctl restart uptime-kuma
```

---

## 🔍 Диагностика

### Проверка портов
```bash
netstat -tlnp | grep -E ":(19999|3001)"
```

### Проверка логов
```bash
# Docker
docker-compose logs

# Systemd
sudo journalctl -u netdata -f
sudo journalctl -u uptime-kuma -f
```

### Проверка доступности
```bash
curl -s http://localhost:19999 | head -5
curl -s http://localhost:3001 | head -5
```

---

## 📋 Рекомендации

### Для слабого VPS
1. **Docker версия** - если есть Docker
2. **Systemd VPS версия** - если нет Docker
3. **Только Netdata** - если очень слабый VPS

### Для мощного сервера
1. **Docker версия** - для простоты
2. **Systemd версия** - для производительности

### При проблемах
1. **Принудительное исправление** - исправляет большинство проблем
2. **Docker fallback** - если systemd не работает

---

## 🎯 Результат

После установки мониторинг будет доступен по адресам:
- **Netdata**: http://your-server:19999
- **Uptime Kuma**: http://your-server:3001
