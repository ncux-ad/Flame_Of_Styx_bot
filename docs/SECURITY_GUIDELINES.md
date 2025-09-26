# 🔒 Руководство по безопасности для разработчиков

## 🎯 Принципы безопасности

### 1. 🔐 **Принцип минимальных привилегий**
- Используйте только необходимые права доступа
- Ограничивайте доступ к чувствительным данным
- Регулярно пересматривайте права доступа

### 2. 🛡️ **Defense in Depth**
- Многоуровневая защита
- Не полагайтесь на одну меру безопасности
- Реализуйте несколько уровней защиты

### 3. 🔍 **Принцип "Не доверяй, проверяй"**
- Валидируйте все входные данные
- Проверяйте права доступа на каждом уровне
- Логируйте все подозрительные действия

## 🚨 Уязвимости и защита

### 1. 🎯 **Injection атаки**

#### **A) SQL Injection**
```python
# ❌ НЕПРАВИЛЬНО - уязвимо к SQL injection
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ ПРАВИЛЬНО - используйте ORM или параметризованные запросы
result = await db.execute(
    select(User).where(User.id == user_id)
)
```

#### **B) Command Injection**
```python
# ❌ НЕПРАВИЛЬНО - уязвимо к command injection
os.system(f"echo {user_input}")

# ✅ ПРАВИЛЬНО - используйте безопасные методы
import subprocess
subprocess.run(['echo', user_input], shell=False)
```

### 2. 🔐 **Аутентификация и авторизация**

#### **A) Проверка прав доступа**
```python
# ✅ ПРАВИЛЬНО - проверяйте права на каждом уровне
async def admin_command(message: Message, data: dict = None):
    # Проверка через фильтр
    if not data or not data.get('is_admin'):
        return

    # Дополнительная проверка в коде
    admin_ids = data.get('admin_ids', [])
    if message.from_user.id not in admin_ids:
        logger.warning(f"Unauthorized access attempt: {message.from_user.id}")
        return
```

#### **B) Валидация токенов**
```python
# ✅ ПРАВИЛЬНО - строгая валидация токенов
@validator("bot_token")
def validate_token(cls, v):
    if not v or len(v) < 20:
        raise ValueError("BOT_TOKEN некорректный")
    if ':' not in v or len(v.split(':')[0]) < 8:
        raise ValueError("BOT_TOKEN должен быть в формате 'bot_id:token'")
    return v
```

### 3. 🛡️ **Защита данных**

#### **A) Шифрование чувствительных данных**
```python
# ✅ ПРАВИЛЬНО - шифрование паролей и токенов
import hashlib
import secrets

def hash_password(password: str) -> str:
    salt = secrets.token_hex(32)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)

# ✅ ПРАВИЛЬНО - безопасное хранение секретов
import os
from cryptography.fernet import Fernet

def encrypt_secret(secret: str) -> str:
    key = os.environ.get('ENCRYPTION_KEY')
    f = Fernet(key)
    return f.encrypt(secret.encode()).decode()
```

#### **B) Безопасная передача данных**
```python
# ✅ ПРАВИЛЬНО - использование HTTPS
import ssl
import aiohttp

async def make_secure_request(url: str):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=ssl_context) as response:
            return await response.text()
```

### 4. 🔍 **Логирование и мониторинг**

#### **A) Безопасное логирование**
```python
# ✅ ПРАВИЛЬНО - не логируйте чувствительные данные
logger.info(f"User {user_id} performed action")  # OK
logger.info(f"User {user_id} used token {token}")  # ❌ НЕ ЛОГИРУЙТЕ ТОКЕНЫ

# ✅ ПРАВИЛЬНО - логируйте подозрительную активность
if not is_admin:
    logger.warning(f"Non-admin user {user_id} attempted admin action: {action}")
```

#### **B) Мониторинг безопасности**
```python
# ✅ ПРАВИЛЬНО - мониторинг аномальной активности
class SecurityMonitor:
    def __init__(self):
        self.failed_attempts = {}
        self.blocked_ips = set()

    async def check_security(self, user_id: int, action: str):
        # Проверка на подозрительную активность
        if self._is_suspicious_activity(user_id, action):
            await self._handle_security_threat(user_id, action)

    def _is_suspicious_activity(self, user_id: int, action: str) -> bool:
        # Логика определения подозрительной активности
        attempts = self.failed_attempts.get(user_id, 0)
        return attempts > 5
```

## 🛠️ Инструменты безопасности

### 1. 🔍 **Статический анализ кода**

#### **A) Bandit - поиск уязвимостей**
```bash
# Установка
pip install bandit

# Запуск анализа
bandit -r app/ -f json -o security-report.json

# Анализ с исключениями
bandit -r app/ -f json -o security-report.json -s B101,B601
```

#### **B) Safety - проверка зависимостей**
```bash
# Установка
pip install safety

# Проверка уязвимостей
safety check --json --output safety-report.json

# Проверка с обновлениями
safety check --json --output safety-report.json --update
```

### 2. 🐳 **Безопасность Docker**

#### **A) Сканирование образов**
```bash
# Установка Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Сканирование образа
trivy image antispam-bot:latest

# Сканирование с отчетом
trivy image antispam-bot:latest --format json --output trivy-report.json
```

#### **B) Безопасная конфигурация Docker**
```dockerfile
# ✅ ПРАВИЛЬНО - использование non-root пользователя
FROM python:3.11-slim

# Создание пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . /app
WORKDIR /app

# Переключение на non-root пользователя
USER appuser

# Запуск приложения
CMD ["python", "bot.py"]
```

### 3. 🔒 **Управление секретами**

#### **A) Docker Secrets**
```yaml
# docker-compose.yml
version: '3.8'
services:
  antispam-bot:
    image: antispam-bot:latest
    secrets:
      - bot_token
      - admin_ids
    environment:
      - BOT_TOKEN_FILE=/run/secrets/bot_token
      - ADMIN_IDS_FILE=/run/secrets/admin_ids

secrets:
  bot_token:
    file: ./secrets/bot_token.txt
  admin_ids:
    file: ./secrets/admin_ids.txt
```

#### **B) HashiCorp Vault (для продакшена)**
```python
# Интеграция с Vault
import hvac

class VaultClient:
    def __init__(self, vault_url: str, token: str):
        self.client = hvac.Client(url=vault_url, token=token)

    def get_secret(self, path: str, key: str) -> str:
        secret = self.client.secrets.kv.v2.read_secret_version(path=path)
        return secret['data']['data'][key]
```

## 🚨 Реагирование на инциденты

### 1. 🔍 **Обнаружение атак**

#### **A) Мониторинг логов**
```bash
# Мониторинг попыток не-админов
tail -f logs/app.log | grep "Non-admin user"

# Мониторинг ошибок
tail -f logs/error.log | grep "ERROR"

# Мониторинг подозрительной активности
tail -f logs/security.log | grep "SUSPICIOUS"
```

#### **B) Автоматические алерты**
```python
# Система алертов
class SecurityAlert:
    def __init__(self):
        self.alert_threshold = 10
        self.time_window = 300  # 5 минут

    async def check_alerts(self):
        # Проверка на превышение порогов
        if self._exceeds_threshold():
            await self._send_alert()

    async def _send_alert(self):
        # Отправка уведомления админам
        for admin_id in self.admin_ids:
            await self.bot.send_message(
                chat_id=admin_id,
                text="🚨 Security Alert: Suspicious activity detected!"
            )
```

### 2. 🛡️ **Ответные действия**

#### **A) Автоматическая блокировка**
```python
# Автоматическая блокировка подозрительных пользователей
class AutoBlock:
    def __init__(self):
        self.blocked_users = set()
        self.block_duration = 3600  # 1 час

    async def block_user(self, user_id: int, reason: str):
        self.blocked_users.add(user_id)
        logger.warning(f"User {user_id} blocked: {reason}")

        # Уведомление админов
        await self._notify_admins(f"User {user_id} blocked: {reason}")

    async def check_blocked_users(self):
        # Проверка времени блокировки
        for user_id in list(self.blocked_users):
            if self._is_block_expired(user_id):
                self.blocked_users.remove(user_id)
```

## 📊 **Метрики безопасности**

### 1. 📈 **KPI безопасности**
```python
# Метрики безопасности
class SecurityMetrics:
    def __init__(self):
        self.metrics = {
            'failed_auth_attempts': 0,
            'blocked_users': 0,
            'suspicious_activities': 0,
            'security_alerts': 0
        }

    def increment_metric(self, metric_name: str):
        if metric_name in self.metrics:
            self.metrics[metric_name] += 1

    def get_security_report(self) -> dict:
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': self.metrics,
            'status': 'healthy' if self._is_healthy() else 'warning'
        }
```

### 2. 🔍 **Мониторинг в реальном времени**
```bash
# Скрипт мониторинга
#!/bin/bash
# security_monitor.sh

while true; do
    # Проверка логов на подозрительную активность
    if tail -n 100 logs/app.log | grep -q "Non-admin user"; then
        echo "ALERT: Unauthorized access attempts detected"
        # Отправка уведомления
        curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
             -d "chat_id=$ADMIN_CHAT_ID" \
             -d "text=Security Alert: Unauthorized access attempts"
    fi

    sleep 60
done
```

## 🚀 **Планы развития**

### 1. 🔮 **Будущие улучшения**
- [ ] **WAF (Web Application Firewall)** - защита на уровне приложения
- [ ] **SIEM интеграция** - централизованный мониторинг
- [ ] **Threat intelligence** - интеграция с базами угроз
- [ ] **Machine Learning** - ML для детекции аномалий
- [ ] **Zero Trust Architecture** - архитектура нулевого доверия

### 2. 🛠️ **Инструменты для внедрения**
- [ ] **OWASP ZAP** - тестирование на проникновение
- [ ] **Nessus** - сканирование уязвимостей
- [ ] **Metasploit** - тестирование на проникновение
- [ ] **Burp Suite** - анализ веб-приложений

---

**Следуйте этим рекомендациям для обеспечения максимальной безопасности бота!** 🛡️
