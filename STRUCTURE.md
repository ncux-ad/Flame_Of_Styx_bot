# 📁 Структура проекта Flame_Of_Styx_bot

## 🎯 Обзор
Telegram бот для защиты от спама с поддержкой каналов, групп комментариев и продвинутой системой модерации.

---

## 🐍 Основной код Python

### 📂 `app/` - Основное приложение
Главная директория с модулями приложения.

#### 🔐 `app/auth/` - Система авторизации
- **`authorization.py`** - Логика авторизации пользователей и проверки прав доступа

#### 🔍 `app/filters/` - Фильтры сообщений
- **`is_admin.py`** - Фильтр для проверки администраторов
- **`is_admin_or_silent.py`** - Фильтр для администраторов или тихих пользователей

#### ⚡ `app/handlers/` - Обработчики команд и событий
- **`admin.py`** - Обработчики административных команд
- **`antispam.py`** - Основная логика антиспам защиты
- **`channels.py`** - Обработка каналов и групп комментариев

#### ⌨️ `app/keyboards/` - Клавиатуры интерфейса
- **`inline.py`** - Inline клавиатуры для команд
- **`reply.py`** - Reply клавиатуры для ответов

#### 🔧 `app/middlewares/` - Промежуточное ПО
- **`dependency_injection.py`** - Внедрение зависимостей
- **`logging.py`** - Логирование запросов и событий
- **`ratelimit.py`** - Ограничение частоты запросов
- **`suspicious_profile.py`** - Анализ подозрительных профилей

#### 📊 `app/models/` - Модели данных
- **`bot.py`** - Модель бота
- **`channel.py`** - Модель каналов
- **`moderation_log.py`** - Логи модерации
- **`secure_models.py`** - Безопасные модели данных
- **`secure_repr.py`** - Безопасное представление объектов
- **`suspicious_profile.py`** - Модель подозрительных профилей
- **`user.py`** - Модель пользователей

#### 🛠️ `app/services/` - Бизнес-логика
- **`bots.py`** - Сервисы для работы с ботами
- **`channels.py`** - Сервисы для работы с каналами
- **`config_watcher.py`** - Мониторинг изменений конфигурации
- **`help.py`** - Сервисы помощи и справки
- **`limits.py`** - Управление лимитами
- **`links.py`** - Обработка ссылок
- **`moderation.py`** - Сервисы модерации
- **`profiles.py`** - Работа с профилями пользователей

#### 🔒 `app/utils/` - Утилиты
- **`security.py`** - Утилиты безопасности

---

## 🐳 Docker и развертывание

### 📦 Docker конфигурация
- **`Dockerfile`** - Основной Docker образ
- **`docker-compose.yml`** - Основная конфигурация Docker Compose
- **`docker-compose.dev.yml`** - Конфигурация для разработки
- **`docker-compose.prod.yml`** - Конфигурация для продакшена

### 🌐 Nginx конфигурация
- **`nginx/nginx.conf`** - Основная конфигурация Nginx
- **`nginx/certbot.conf`** - Конфигурация для Let's Encrypt
- **`nginx/certbot-scripts/`** - Скрипты для работы с SSL сертификатами
  - `certbot-init.sh` - Инициализация Certbot
  - `certbot-renew.sh` - Обновление сертификатов
  - `certbot-status.sh` - Проверка статуса сертификатов

### 📊 Мониторинг
- **`monitoring/prometheus.yml`** - Конфигурация Prometheus
- **`monitoring/alertmanager.yml`** - Конфигурация Alertmanager
- **`monitoring/antispam_rules.yml`** - Правила для антиспам системы
- **`monitoring/docker-compose.monitoring.yml`** - Docker Compose для мониторинга

---

## 📚 Документация

### 📖 `docs/` - Подробная документация
- **`ADMIN_GUIDE.md`** - Руководство администратора
- **`API.md`** - Документация API
- **`ARCHITECTURE.md`** - Архитектура системы
- **`BEST_PRACTICES.md`** - Лучшие практики разработки
- **`BUGFIXES_HISTORY.md`** - История исправлений багов
- **`CHECKLISTS.md`** - Чек-листы для разработки
- **`CODE_EXAMPLES.md`** - Примеры кода
- **`CONFIG.md`** - Конфигурация системы
- **`CONFIGURATION.md`** - Детальная конфигурация
- **`DEBUG_COMMANDS.md`** - Команды для отладки
- **`DEPLOYMENT.md`** - Руководство по развертыванию
- **`DEVELOPER_CHECKLIST.md`** - Чек-лист разработчика
- **`DEVELOPER_QUESTIONS.md`** - Вопросы разработчика
- **`DEVELOPMENT.md`** - Руководство по разработке
- **`DEVOPS.md`** - DevOps практики
- **`GITHUB_ACTIONS.md`** - GitHub Actions
- **`HOT_RELOAD.md`** - Горячая перезагрузка
- **`INDEX.md`** - Индекс документации
- **`INSTALLATION.md`** - Руководство по установке
- **`LETSENCRYPT.md`** - Настройка Let's Encrypt
- **`OFFICIAL_DOCUMENTATION.md`** - Официальная документация
- **`POWERSHELL_SETUP.md`** - Настройка PowerShell
- **`ROADMAP.md`** - Дорожная карта проекта
- **`SECURITY_FIXES.md`** - Исправления безопасности
- **`SECURITY_GUIDELINES.md`** - Руководство по безопасности
- **`SECURITY.md`** - Безопасность системы
- **`SUSPICIOUS_PROFILES.md`** - Работа с подозрительными профилями
- **`TODO.md`** - Список задач
- **`TROUBLESHOOTING.md`** - Устранение неполадок

---

## 🛠️ Скрипты и утилиты

### 📜 `scripts/` - Различные скрипты
- **`backup.sh`** - Скрипт резервного копирования
- **`deploy.sh`** - Скрипт развертывания
- **`docker-dev-smart.ps1`** - PowerShell скрипт для разработки
- **`docker-dev-smart.sh`** - Bash скрипт для разработки
- **`docker-dev.ps1`** - PowerShell скрипт Docker для разработки
- **`docker-dev.sh`** - Bash скрипт Docker для разработки
- **`fix_all_log_injection.py`** - Исправление всех уязвимостей логирования
- **`fix_critical_log_injection.py`** - Исправление критических уязвимостей
- **`fix_critical_vulnerabilities.py`** - Исправление критических уязвимостей
- **`fix_log_injection.py`** - Исправление уязвимостей логирования
- **`fix_remaining_vulnerabilities.py`** - Исправление оставшихся уязвимостей
- **`fix_security_vulnerabilities.py`** - Исправление уязвимостей безопасности
- **`healthcheck.sh`** - Проверка здоровья системы
- **`init-git.sh`** - Инициализация Git
- **`init-letsencrypt.sh`** - Инициализация Let's Encrypt
- **`install-docker.sh`** - Установка Docker
- **`install-python.sh`** - Установка Python
- **`install-systemd.sh`** - Установка systemd сервиса
- **`quick-docker.ps1`** - Быстрый запуск Docker (PowerShell)
- **`quick-docker.sh`** - Быстрый запуск Docker (Bash)
- **`restore.sh`** - Восстановление из резервной копии
- **`secure_shell_utils.sh`** - Безопасные утилиты shell
- **`security_check_safe.py`** - Безопасная проверка безопасности
- **`security_check.py`** - Проверка безопасности
- **`setup_secrets.sh`** - Настройка секретов
- **`setup-dev.sh`** - Настройка среды разработки
- **`setup-domain.sh`** - Настройка домена
- **`setup-git.sh`** - Настройка Git
- **`setup-wsl.sh`** - Настройка WSL
- **`uninstall.sh`** - Удаление системы
- **`update.sh`** - Обновление системы
- **`wsl-dev.sh`** - WSL для разработки
- **`wsl-docker.sh`** - WSL с Docker
- **`wsl-setup.ps1`** - PowerShell настройка WSL

### 🚀 Основные скрипты
- **`install.sh`** - Главный установочный скрипт (рефакторенный v2.0.0)
- **`install_backup.sh`** - Резервная копия установочного скрипта
- **`install_refactored.sh`** - Рефакторенная версия установочного скрипта

---

## ⚙️ Конфигурация

### 🔧 Основные конфигурационные файлы
- **`app/config.py`** - Основная конфигурация приложения
- **`app/database.py`** - Конфигурация базы данных
- **`.env.example`** - Пример переменных окружения
- **`env.template`** - Шаблон переменных окружения
- **`requirements.txt`** - Python зависимости
- **`pyproject.toml`** - Конфигурация проекта Python
- **`mypy.ini`** - Конфигурация MyPy (статический анализатор)
- **`pytest.ini`** - Конфигурация pytest
- **`alembic.ini`** - Конфигурация Alembic (миграции БД)

### 🗄️ База данных
- **`alembic/`** - Миграции базы данных
  - **`env.py`** - Конфигурация Alembic
  - **`versions/`** - Файлы миграций
    - `e2b091aa88ca_add_linked_chat_id_and_is_comment_group_.py` - Миграция для связанных чатов

---

## 🧪 Тестирование

### 📋 `tests/` - Тесты
- **`conftest.py`** - Конфигурация pytest
- **`test_bot.py`** - Тесты основного функционала бота
- **`test_security.py`** - Тесты безопасности

### 🔬 Тестовые скрипты
- **`test_*.py`** - Различные тестовые скрипты
- **`test_skip_docker.sh`** - Тест логики --skip-docker
- **`test_channel.sh`** - Тест работы с каналами
- **`test_simple.sh`** - Простые тесты
- **`test_fix.sh`** - Тесты исправлений

---

## 🏗️ Системные файлы

### 🔧 Systemd
- **`systemd/antispam-bot.service`** - Systemd unit файл
- **`systemd/install.sh`** - Скрипт установки systemd

### 📊 Мониторинг и статистика
- **`check_stats.py`** - Проверка статистики
- **`security-report.json`** - Отчет о безопасности
- **`limits.json.example`** - Пример лимитов

### 🛠️ Утилиты разработки
- **`format_code.py`** - Форматирование кода
- **`commit.py`** - Утилита для коммитов
- **`Makefile`** - Makefile для автоматизации

---

## 📄 Документация проекта

### 📋 Основные документы
- **`README.md`** - Основное описание проекта
- **`CHANGELOG.md`** - История изменений
- **`CONTRIBUTING.md`** - Руководство для контрибьюторов
- **`LICENSE`** - Лицензия проекта
- **`PROJECT_STATUS_REPORT.md`** - Отчет о статусе проекта
- **`FIXES_SUMMARY.md`** - Сводка исправлений
- **`SECURITY_FIXES_COMPLETE.md`** - Полный список исправлений безопасности
- **`SECURITY_FIXES_SUMMARY.md`** - Сводка исправлений безопасности

### 🚀 Быстрые руководства
- **`QUICK_INSTALL.md`** - Быстрая установка
- **`QUICK_LINKS.md`** - Быстрые ссылки
- **`QUICK_START_LETSENCRYPT.md`** - Быстрый старт с Let's Encrypt
- **`QUICKSTART.md`** - Быстрый старт
- **`SETUP_GUIDE.md`** - Руководство по настройке
- **`WSL_SETUP.md`** - Настройка WSL

### 🔧 Специальные инструкции
- **`CHANNEL_FIX_INSTRUCTIONS.md`** - Инструкции по исправлению каналов
- **`DI_BEST_PRACTICES.md`** - Лучшие практики внедрения зависимостей

---

## 🎯 Архитектурные принципы

### 📦 Модульность
Проект построен по принципу модульной архитектуры с четким разделением ответственности:
- **Handlers** - обработка пользовательских команд
- **Services** - бизнес-логика
- **Models** - работа с данными
- **Middlewares** - промежуточная обработка

### 🔒 Безопасность
- Централизованная система авторизации
- Защита от инъекций в логи
- Безопасные модели данных
- Анализ подозрительных профилей

### 🚀 Масштабируемость
- Поддержка Docker и systemd
- Мониторинг с Prometheus
- Горячая перезагрузка
- Миграции базы данных

### 🛠️ Разработка
- Полная документация
- Автоматизированные тесты
- CI/CD с GitHub Actions
- Статический анализ кода

---

## 📈 Статистика проекта

- **Общее количество файлов**: 100+
- **Строки кода**: 10,000+
- **Модули Python**: 20+
- **Скрипты**: 30+
- **Документация**: 25+ файлов
- **Тесты**: 10+ файлов

---

*Последнее обновление: 2025-09-23*
*Версия проекта: 2.0.0*
