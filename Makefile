# Makefile for AntiSpam Bot
# Удобные команды для разработки и безопасности

.PHONY: help install test security clean docker-build docker-up docker-down logs

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)AntiSpam Bot - Команды для разработки$(NC)"
	@echo "=================================="
	@echo ""
	@echo "$(GREEN)Основные команды:$(NC)"
	@echo "  make install     - Установить зависимости"
	@echo "  make test        - Запустить тесты"
	@echo "  make security    - Проверить безопасность"
	@echo "  make clean       - Очистить временные файлы"
	@echo ""
	@echo "$(GREEN)Docker команды:$(NC)"
	@echo "  make docker-build - Собрать Docker образ"
	@echo "  make docker-up    - Запустить контейнеры"
	@echo "  make docker-down  - Остановить контейнеры"
	@echo "  make logs         - Показать логи"
	@echo ""
	@echo "$(GREEN)Безопасность:$(NC)"
	@echo "  make security-check    - Проверка безопасности"
	@echo "  make security-scan     - Сканирование уязвимостей"
	@echo "  make security-report   - Генерация отчета"
	@echo ""

install: ## Установить зависимости
	@echo "$(YELLOW)Установка зависимостей...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "$(GREEN)Зависимости установлены!$(NC)"

test: ## Запустить тесты
	@echo "$(YELLOW)Запуск тестов...$(NC)"
	python -m pytest tests/ -v --cov=app --cov-report=html
	@echo "$(GREEN)Тесты завершены!$(NC)"

security: security-check security-scan ## Полная проверка безопасности
	@echo "$(GREEN)Проверка безопасности завершена!$(NC)"

security-check: ## Проверка безопасности конфигурации
	@echo "$(YELLOW)Проверка безопасности...$(NC)"
	@if [ -f scripts/security-check.sh ]; then \
		chmod +x scripts/security-check.sh && ./scripts/security-check.sh; \
	elif [ -f scripts/security-check.ps1 ]; then \
		powershell -ExecutionPolicy Bypass -File scripts/security-check.ps1; \
	else \
		echo "$(RED)Скрипт проверки безопасности не найден!$(NC)"; \
		exit 1; \
	fi

security-scan: ## Сканирование уязвимостей в коде
	@echo "$(YELLOW)Сканирование уязвимостей...$(NC)"
	@if command -v bandit >/dev/null 2>&1; then \
		echo "$(BLUE)Запуск Bandit...$(NC)"; \
		bandit -r app/ -f json -o bandit-report.json -ll || true; \
		echo "$(GREEN)Bandit завершен!$(NC)"; \
	else \
		echo "$(YELLOW)Bandit не установлен. Установите: pip install bandit$(NC)"; \
	fi
	@if command -v safety >/dev/null 2>&1; then \
		echo "$(BLUE)Запуск Safety...$(NC)"; \
		safety check --ignore 77745,77744,76752,77680,78162 --json > safety-report.json; \
		echo "$(GREEN)Safety завершен!$(NC)"; \
	else \
		echo "$(YELLOW)Safety не установлен. Установите: pip install safety$(NC)"; \
	fi

security-report: ## Генерация отчета по безопасности
	@echo "$(YELLOW)Генерация отчета по безопасности...$(NC)"
	@if [ -f "security-report.json" ]; then \
		echo "$(GREEN)Отчет по безопасности: security-report.json$(NC)"; \
		python -c "import json; data=json.load(open('security-report.json')); print(f'Статус: {data[\"security_status\"]}'); print(f'Проблем: {data[\"summary\"][\"total_issues\"]}'); print(f'Предупреждений: {data[\"summary\"][\"total_warnings\"]}'); print(f'Рекомендаций: {data[\"summary\"][\"total_recommendations\"]}')"; \
	else \
		echo "$(RED)Отчет не найден. Запустите: make security-check$(NC)"; \
	fi

clean: ## Очистить временные файлы
	@echo "$(YELLOW)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "htmlcov" -delete
	rm -f security-report.json bandit-report.json safety-report.json
	@echo "$(GREEN)Очистка завершена!$(NC)"

docker-build: ## Собрать Docker образ
	@echo "$(YELLOW)Сборка Docker образа...$(NC)"
	docker-compose build
	@echo "$(GREEN)Docker образ собран!$(NC)"

docker-up: ## Запустить контейнеры
	@echo "$(YELLOW)Запуск контейнеров...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Контейнеры запущены!$(NC)"

docker-down: ## Остановить контейнеры
	@echo "$(YELLOW)Остановка контейнеров...$(NC)"
	docker-compose down
	@echo "$(GREEN)Контейнеры остановлены!$(NC)"

logs: ## Показать логи
	@echo "$(YELLOW)Показ логов...$(NC)"
	docker-compose logs -f antispam-bot

restart: docker-down docker-up ## Перезапустить контейнеры
	@echo "$(GREEN)Контейнеры перезапущены!$(NC)"

dev: ## Запуск в режиме разработки
	@echo "$(YELLOW)Запуск в режиме разработки...$(NC)"
	python bot.py

format: ## Форматирование кода
	@echo "$(YELLOW)Форматирование кода...$(NC)"
	black app/ tests/ scripts/
	isort app/ tests/ scripts/
	@echo "$(GREEN)Код отформатирован!$(NC)"

lint: ## Проверка кода линтерами
	@echo "$(YELLOW)Проверка кода...$(NC)"
	pylint app/ tests/ scripts/
	mypy app/
	@echo "$(GREEN)Проверка завершена!$(NC)"

pre-commit: format lint test security ## Pre-commit проверки
	@echo "$(GREEN)Pre-commit проверки завершены!$(NC)"

# Команды для CI/CD
ci-test: ## Тесты для CI
	python -m pytest tests/ -v --cov=app --cov-report=xml

ci-security: ## Безопасность для CI
	python scripts/security_check.py
	bandit -r app/ -f json -o bandit-report.json
	safety check --json --output safety-report.json

# Команды для мониторинга
monitor: ## Мониторинг в реальном времени
	@echo "$(YELLOW)Мониторинг бота...$(NC)"
	@echo "Логи:"
	docker-compose logs -f antispam-bot &
	@echo "Статистика:"
	watch -n 5 'docker stats antispam-bot --no-stream'

# Команды для развертывания
deploy-staging: ## Развертывание на staging
	@echo "$(YELLOW)Развертывание на staging...$(NC)"
	docker-compose -f docker-compose.staging.yml up -d
	@echo "$(GREEN)Развертывание на staging завершено!$(NC)"

deploy-prod: ## Развертывание на production
	@echo "$(YELLOW)Развертывание на production...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Развертывание на production завершено!$(NC)"

# Команды для резервного копирования
backup: ## Создание резервной копии
	@echo "$(YELLOW)Создание резервной копии...$(NC)"
	mkdir -p backups
	docker cp antispam-bot:/app/data/db.sqlite3 backups/db_$(shell date +%Y%m%d_%H%M%S).sqlite3
	@echo "$(GREEN)Резервная копия создана!$(NC)"

restore: ## Восстановление из резервной копии
	@echo "$(YELLOW)Восстановление из резервной копии...$(NC)"
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)Укажите файл резервной копии: make restore BACKUP_FILE=backups/db_20240101_120000.sqlite3$(NC)"; \
		exit 1; \
	fi
	docker cp $(BACKUP_FILE) antispam-bot:/app/data/db.sqlite3
	@echo "$(GREEN)Восстановление завершено!$(NC)"

# Команды для обновления
update: ## Обновление зависимостей
	@echo "$(YELLOW)Обновление зависимостей...$(NC)"
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt
	@echo "$(GREEN)Зависимости обновлены!$(NC)"

update-docker: ## Обновление Docker образа
	@echo "$(YELLOW)Обновление Docker образа...$(NC)"
	docker-compose pull
	docker-compose build --no-cache
	@echo "$(GREEN)Docker образ обновлен!$(NC)"

# Команды для отладки
debug: ## Запуск в режиме отладки
	@echo "$(YELLOW)Запуск в режиме отладки...$(NC)"
	PYTHONPATH=. python -m pdb bot.py

profile: ## Профилирование производительности
	@echo "$(YELLOW)Профилирование производительности...$(NC)"
	python -m cProfile -o profile.prof bot.py
	python -c "import pstats; pstats.Stats('profile.prof').sort_stats('cumulative').print_stats(20)"

# Команды для документации
docs: ## Генерация документации
	@echo "$(YELLOW)Генерация документации...$(NC)"
	@if command -v sphinx-build >/dev/null 2>&1; then \
		sphinx-build -b html docs/ docs/_build/html; \
		echo "$(GREEN)Документация сгенерирована в docs/_build/html/$(NC)"; \
	else \
		echo "$(YELLOW)Sphinx не установлен. Установите: pip install sphinx$(NC)"; \
	fi

# Команды для уведомлений
notify-success: ## Уведомление об успешном развертывании
	@echo "$(GREEN)✅ Развертывание успешно завершено!$(NC)"

notify-failure: ## Уведомление об ошибке развертывания
	@echo "$(RED)❌ Ошибка при развертывании!$(NC)"

# Команды для очистки Docker
docker-clean: ## Очистка Docker ресурсов
	@echo "$(YELLOW)Очистка Docker ресурсов...$(NC)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)Docker очищен!$(NC)"

# Команды для проверки состояния
status: ## Проверка состояния системы
	@echo "$(YELLOW)Проверка состояния системы...$(NC)"
	@echo "Docker контейнеры:"
	docker-compose ps
	@echo ""
	@echo "Использование диска:"
	df -h
	@echo ""
	@echo "Использование памяти:"
	free -h
	@echo ""
	@echo "Процессы Python:"
	ps aux | grep python | grep -v grep

# Команды для тестирования производительности
benchmark: ## Тестирование производительности
	@echo "$(YELLOW)Тестирование производительности...$(NC)"
	python -m pytest tests/benchmark/ -v --benchmark-only
	@echo "$(GREEN)Тестирование производительности завершено!$(NC)"

# Команды для мониторинга безопасности
security-monitor: ## Мониторинг безопасности в реальном времени
	@echo "$(YELLOW)Мониторинг безопасности...$(NC)"
	@echo "Логи безопасности:"
	tail -f logs/security.log &
	@echo "Попытки не-админов:"
	tail -f logs/app.log | grep "Non-admin user" &
	@echo "Ошибки:"
	tail -f logs/error.log &

# Команды для обновления сертификатов
update-ssl: ## Обновление SSL сертификатов
	@echo "$(YELLOW)Обновление SSL сертификатов...$(NC)"
	@if [ -f "scripts/update_ssl.sh" ]; then \
		chmod +x scripts/update_ssl.sh; \
		./scripts/update_ssl.sh; \
	else \
		echo "$(RED)Скрипт обновления SSL не найден!$(NC)"; \
	fi

# Команды для проверки конфигурации
config-check: ## Проверка конфигурации
	@echo "$(YELLOW)Проверка конфигурации...$(NC)"
	python -c "from app.config import load_config; config = load_config(); print('✅ Конфигурация загружена успешно')"
	@echo "$(GREEN)Конфигурация корректна!$(NC)"

# Команды для инициализации
init: install config-check ## Инициализация проекта
	@echo "$(GREEN)Проект инициализирован!$(NC)"

# Команды для полной проверки
full-check: test security lint format ## Полная проверка проекта
	@echo "$(GREEN)Полная проверка завершена!$(NC)"

# Команды для быстрого старта
quick-start: install docker-build docker-up ## Быстрый старт
	@echo "$(GREEN)Быстрый старт завершен!$(NC)"

# Команды для остановки
stop: docker-down ## Остановка всех сервисов
	@echo "$(GREEN)Все сервисы остановлены!$(NC)"

# Команды для перезагрузки
reload: docker-down docker-up ## Перезагрузка всех сервисов
	@echo "$(GREEN)Все сервисы перезагружены!$(NC)"

# Команды Let's Encrypt
setup-domain: ## Настройка домена для Let's Encrypt
	@echo "$(YELLOW)Настройка домена...$(NC)"
	bash scripts/setup-domain.sh

letsencrypt-init: ## Инициализация Let's Encrypt сертификатов
	@echo "$(YELLOW)Инициализация Let's Encrypt...$(NC)"
	bash scripts/init-letsencrypt.sh

letsencrypt-status: ## Проверка статуса Let's Encrypt сертификатов
	@echo "$(YELLOW)Проверка статуса сертификатов...$(NC)"
	docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-status.sh

letsencrypt-renew: ## Обновление Let's Encrypt сертификатов
	@echo "$(YELLOW)Обновление сертификатов...$(NC)"
	docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-renew.sh

letsencrypt-logs: ## Просмотр логов Let's Encrypt
	@echo "$(YELLOW)Логи Let's Encrypt...$(NC)"
	docker-compose -f docker-compose.prod.yml logs certbot

# Команды для продакшена
prod-up: ## Запуск продакшена
	@echo "$(YELLOW)Запуск продакшена...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Остановка продакшена
	@echo "$(YELLOW)Остановка продакшена...$(NC)"
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Логи продакшена
	@echo "$(YELLOW)Логи продакшена...$(NC)"
	docker-compose -f docker-compose.prod.yml logs -f

# Команды установки
install: ## Интерактивная установка
	@echo "$(YELLOW)Запуск интерактивной установки...$(NC)"
	sudo bash install.sh

install-docker: ## Установка через Docker
	@echo "$(YELLOW)Установка через Docker...$(NC)"
	sudo bash scripts/install-docker.sh

install-systemd: ## Установка через systemd
	@echo "$(YELLOW)Установка через systemd...$(NC)"
	sudo bash scripts/install-systemd.sh

update: ## Обновление бота
	@echo "$(YELLOW)Обновление бота...$(NC)"
	sudo bash scripts/update.sh

uninstall: ## Удаление бота
	@echo "$(YELLOW)Удаление бота...$(NC)"
	sudo bash scripts/uninstall.sh

# Команды управления
bot-start: ## Запуск бота
	@echo "$(YELLOW)Запуск бота...$(NC)"
	sudo antispam-bot start

bot-stop: ## Остановка бота
	@echo "$(YELLOW)Остановка бота...$(NC)"
	sudo antispam-bot stop

bot-restart: ## Перезапуск бота
	@echo "$(YELLOW)Перезапуск бота...$(NC)"
	sudo antispam-bot restart

bot-status: ## Статус бота
	@echo "$(YELLOW)Статус бота...$(NC)"
	sudo antispam-bot status

bot-logs: ## Логи бота
	@echo "$(YELLOW)Логи бота...$(NC)"
	sudo antispam-bot logs
