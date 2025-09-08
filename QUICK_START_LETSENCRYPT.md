# 🚀 Быстрый старт с Let's Encrypt

## 📋 Что нужно сделать:

### 1. **Настройте домен**
```bash
# Автоматическая настройка
make setup-domain

# Или вручную
export DOMAIN="your-domain.com"
export EMAIL="your-email@example.com"
```

### 2. **Настройте DNS**
Убедитесь, что ваш домен указывает на сервер:
```bash
# Проверка DNS
nslookup your-domain.com
dig your-domain.com
```

### 3. **Инициализируйте Let's Encrypt**
```bash
make letsencrypt-init
```

### 4. **Запустите продакшен**
```bash
make prod-up
```

## ⚠️ Важно!

**Домен ОБЯЗАТЕЛЬНО нужно указывать!** Без домена Let's Encrypt не сможет выдать сертификат.

## 🔧 Настройка домена

### Вариант 1: Автоматическая настройка
```bash
make setup-domain
```

### Вариант 2: Ручная настройка
```bash
# Создайте .env.prod файл
cp env.prod.example .env.prod
nano .env.prod

# Установите переменные
export DOMAIN="your-domain.com"
export EMAIL="your-email@example.com"
```

## 🌐 DNS настройки

### A запись
```
your-domain.com    A    YOUR_SERVER_IP
www.your-domain.com A    YOUR_SERVER_IP
```

### Проверка
```bash
# Проверка IP
curl ifconfig.me

# Проверка DNS
nslookup your-domain.com
```

## 🚨 Частые ошибки

### 1. Домен не настроен
```
❌ Домен не настроен!
Установите переменную DOMAIN:
export DOMAIN="your-domain.com"
```

### 2. DNS не настроен
```
⚠️ IP адреса не совпадают!
Домен: 1.2.3.4
Сервер: 5.6.7.8
```

### 3. Порты не открыты
```
⚠️ Порт 80 не открыт
⚠️ Порт 443 не открыт
```

## 📞 Поддержка

Если что-то не работает:
1. Проверьте DNS: `nslookup your-domain.com`
2. Проверьте порты: `netstat -tuln | grep -E ":80|:443"`
3. Проверьте логи: `make letsencrypt-logs`
4. Создайте issue в GitHub

## 🎯 Готово!

После настройки у вас будет:
- ✅ SSL сертификат от Let's Encrypt
- ✅ Автоматическое обновление
- ✅ HTTPS редирект
- ✅ Современные SSL настройки
