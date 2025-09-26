# 📚 Индекс документации

Полный индекс документации AntiSpam Bot.

## 🚀 Быстрый старт

- **[README.md](../README.md)** - Основная информация о проекте
- **[QUICK_INSTALL.md](../QUICK_INSTALL.md)** - Быстрая установка
- **[QUICKSTART.md](../QUICKSTART.md)** - Быстрый старт
- **[SETUP_GUIDE.md](../SETUP_GUIDE.md)** - Подробное руководство по настройке

## 👑 Администрирование

- **[ADMIN_GUIDE_NEW.md](ADMIN_GUIDE_NEW.md)** - Руководство администратора
- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - Полное руководство администратора
- **[COMMANDS.md](../COMMANDS.md)** - Справочник команд
- **[DEBUG_COMMANDS.md](DEBUG_COMMANDS.md)** - Команды для отладки

## 🏗️ Архитектура и разработка

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Архитектура системы
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Руководство для разработчиков
- **[DEVELOPER_CHECKLIST.md](DEVELOPER_CHECKLIST.md)** - Чек-лист разработчика
- **[DEVELOPER_QUESTIONS.md](DEVELOPER_QUESTIONS.md)** - Вопросы разработчика
- **[CODE_EXAMPLES.md](CODE_EXAMPLES.md)** - Примеры кода
- **[BEST_PRACTICES.md](BEST_PRACTICES.md)** - Лучшие практики

## ⚙️ Конфигурация и развертывание

- **[CONFIGURATION.md](CONFIGURATION.md)** - Конфигурация системы
- **[CONFIG.md](CONFIG.md)** - Настройка конфигурации
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Развертывание
- **[INSTALLATION.md](INSTALLATION.md)** - Установка
- **[HOT_RELOAD.md](HOT_RELOAD.md)** - Hot-reload настроек

## 🔒 Безопасность

- **[SECURITY.md](SECURITY.md)** - Безопасность системы
- **[SECURITY_GUIDELINES.md](SECURITY_GUIDELINES.md)** - Руководство по безопасности
- **[SECURITY_FIXES.md](SECURITY_FIXES.md)** - Исправления безопасности

## 🐳 Docker и DevOps

- **[DEVOPS.md](DEVOPS.md)** - DevOps практики
- **[GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)** - GitHub Actions
- **[docker-compose.yml](../docker-compose.yml)** - Docker Compose конфигурация
- **[Dockerfile](../Dockerfile)** - Docker образ

## 🔧 Устранение неполадок

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Устранение неполадок
- **[BUGFIXES_HISTORY.md](BUGFIXES_HISTORY.md)** - История исправлений
- **[CHECKLISTS.md](CHECKLISTS.md)** - Чек-листы

## 📊 Мониторинг и логи

- **[API.md](API.md)** - API документация
- **[SUSPICIOUS_PROFILES.md](SUSPICIOUS_PROFILES.md)** - Система подозрительных профилей
- **[LETSENCRYPT.md](LETSENCRYPT.md)** - Let's Encrypt SSL

## 📖 Дополнительные ресурсы

- **[OFFICIAL_DOCUMENTATION.md](OFFICIAL_DOCUMENTATION.md)** - Официальная документация
- **[POWERSHELL_SETUP.md](POWERSHELL_SETUP.md)** - Настройка PowerShell
- **[ROADMAP.md](ROADMAP.md)** - План развития
- **[TODO.md](TODO.md)** - Список задач

## 🎯 Основные функции

### Антиспам защита
- Автоматическое обнаружение спама
- Фильтрация бот-ссылок
- Медиа-антиспам
- Система подозрительных профилей

### Управление каналами
- Разделение на нативные и иностранные каналы
- Автоматическое определение типа канала
- Уведомления о добавлении/удалении бота

### Модерация
- Автоматическое удаление спама
- Блокировка пользователей
- Управление банами
- Синхронизация с Telegram API

### Мониторинг
- Просмотр логов через команды
- Статистика работы бота
- Настройка лимитов
- Hot-reload конфигурации

## 🔧 Команды бота

### Админские команды
- `/status` - статистика работы
- `/settings` - настройки системы
- `/logs [уровень]` - просмотр логов
- `/channels` - управление каналами
- `/suspicious` - подозрительные профили
- `/unban` - разблокировка пользователей
- `/setlimits` - настройка лимитов
- `/help` - справка по командам

### Автоматические действия
- Обнаружение бот-ссылок
- Анализ подозрительных профилей
- Удаление спама
- Блокировка пользователей

## 🏗️ Архитектура

### Двухслойная архитектура
- **Anti-spam Router** - перехватывает все сообщения
- **Admin Router** - обрабатывает админские команды

### Middleware
- **DependencyInjectionMiddleware** - внедрение зависимостей
- **RateLimitMiddleware** - ограничение частоты
- **SuspiciousProfileMiddleware** - анализ профилей
- **LoggingMiddleware** - логирование

### Сервисы
- **LinkService** - проверка ссылок
- **ProfileService** - анализ профилей
- **ModerationService** - модерация
- **ChannelService** - управление каналами
- **BotService** - управление ботами
- **HelpService** - справка
- **LimitsService** - управление лимитами

## 🔒 Безопасность

### Принципы безопасности
- Валидация всех входных данных
- Безопасное логирование
- Защита от инъекций
- Контроль доступа

### Рекомендации
- Регулярное обновление зависимостей
- Мониторинг логов
- Резервное копирование
- Тестирование безопасности

## 📞 Поддержка

### Получение помощи
- [GitHub Issues](../../issues)
- [Документация](docs/)
- [Устранение неполадок](TROUBLESHOOTING.md)

### Контакты
- **Разработчик:** @ncux_ad
- **GitHub:** [ncux-ad/Flame_Of_Styx_bot](https://github.com/ncux-ad/Flame_Of_Styx_bot)

---

**Создано с ❤️ для защиты Telegram сообществ**