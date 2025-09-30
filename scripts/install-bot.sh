#!/bin/bash
# Умная установка бота с опциональным мониторингом

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для красивого вывода
print_header() {
    echo -e "${BLUE}🚀 AntiSpam Bot Installation${NC}"
    echo -e "${BLUE}============================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

print_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

print_header

# Проверяем, что мы на сервере
if [[ "$USER" == "root" ]]; then
    print_error "Не запускайте скрипт от root! Используйте обычного пользователя."
    exit 1
fi

# Проверяем, что мы в правильной директории
if [[ ! -f "bot.py" ]]; then
    print_error "Запустите скрипт из корневой директории проекта!"
    exit 1
fi

print_success "Проверки пройдены"

# Останавливаем бота если запущен
print_step "Останавливаем бота (если запущен)..."
if systemctl is-active --quiet antispam-bot; then
    sudo systemctl stop antispam-bot
    print_success "Бот остановлен"
else
    print_info "Бот не был запущен"
fi

# Обновляем код
print_step "Обновляем код..."
git pull origin master
print_success "Код обновлен"

# Устанавливаем зависимости
print_step "Устанавливаем зависимости..."
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    pip install -r requirements.txt
    print_success "Зависимости обновлены"
else
    print_info "Создаем виртуальное окружение..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    print_success "Виртуальное окружение создано"
fi

# Настраиваем systemd сервис для бота
print_step "Настраиваем systemd сервис для бота..."
sudo tee /etc/systemd/system/antispam-bot.service > /dev/null <<EOF
[Unit]
Description=AntiSpam Bot for Telegram
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable antispam-bot.service

print_success "Systemd сервис настроен"

# Настройка безопасности (модульный подход)
echo ""
print_info "🔒 Настройка безопасности:"
echo ""

if [[ -f "scripts/install/install-security.sh" ]]; then
    print_step "Запускаем модуль безопасности..."
    source scripts/install/install-security.sh
    if install_security; then
        print_success "Модуль безопасности установлен"
    else
        print_warning "Модуль безопасности установлен с предупреждениями"
    fi
else
    print_warning "Модуль безопасности не найден, используем fallback..."
    # Fallback для базовой настройки
    mkdir -p logs/{general,encrypted,security,reports}
    print_success "Базовая структура логов создана"
fi

# Спрашиваем про мониторинг
echo ""
print_info "📊 Настройка мониторинга:"
echo ""
echo "Выберите вариант установки мониторинга:"
echo "  1) 💪 VPS версия (рекомендуется для слабого VPS)"
echo "  2) 🔧 Systemd версия (стандартная)"
echo "  3) 🐳 Docker версия (если есть Docker)"
echo "  4) ❌ Без мониторинга"
echo ""
read -p "Введите номер (1-4): " choice

case $choice in
    1)
        print_step "Устанавливаем VPS версию мониторинга..."
        chmod +x scripts/setup-monitoring-vps.sh
        ./scripts/setup-monitoring-vps.sh
        MONITORING_INSTALLED=true
        MONITORING_TYPE="VPS"
        ;;
    2)
        print_step "Устанавливаем systemd версию мониторинга..."
        chmod +x scripts/setup-monitoring-systemd.sh
        ./scripts/setup-monitoring-systemd.sh
        MONITORING_INSTALLED=true
        MONITORING_TYPE="Systemd"
        ;;
    3)
        print_step "Устанавливаем Docker версию мониторинга..."
        chmod +x scripts/setup-monitoring-simple.sh
        ./scripts/setup-monitoring-simple.sh
        MONITORING_INSTALLED=true
        MONITORING_TYPE="Docker"
        ;;
    4)
        print_info "Мониторинг не установлен"
        MONITORING_INSTALLED=false
        MONITORING_TYPE="None"
        ;;
    *)
        print_error "Неверный выбор. Мониторинг не установлен."
        MONITORING_INSTALLED=false
        MONITORING_TYPE="None"
        ;;
esac

# Запускаем бота
print_step "Запускаем бота..."
sudo systemctl start antispam-bot

# Ждем запуска
sleep 3

# Проверяем статус
print_step "Проверяем статус..."
if systemctl is-active --quiet antispam-bot; then
    print_success "Бот запущен успешно"
else
    print_error "Не удалось запустить бота"
    sudo journalctl -u antispam-bot -n 10 --no-pager
    exit 1
fi

# Показываем результат
echo ""
print_success "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo ""

if [[ "$MONITORING_INSTALLED" == "true" ]]; then
    print_info "📊 Мониторинг установлен ($MONITORING_TYPE версия):"
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo -e "  • ${GREEN}Netdata${NC}: http://${SERVER_IP}:19999"
    echo -e "  • ${GREEN}Uptime Kuma${NC}: http://${SERVER_IP}:3001"
    echo ""
    print_info "🔧 Управление мониторингом:"
    if [[ "$MONITORING_TYPE" == "VPS" ]]; then
        echo -e "  • ${YELLOW}Статус${NC}: ./scripts/monitoring-vps-control.sh status"
        echo -e "  • ${YELLOW}Логи${NC}: ./scripts/monitoring-vps-control.sh logs"
        echo -e "  • ${YELLOW}Ресурсы${NC}: ./scripts/monitoring-vps-control.sh resources"
    elif [[ "$MONITORING_TYPE" == "Systemd" ]]; then
        echo -e "  • ${YELLOW}Статус${NC}: ./scripts/monitoring-systemd-control.sh status"
        echo -e "  • ${YELLOW}Логи${NC}: ./scripts/monitoring-systemd-control.sh logs"
    elif [[ "$MONITORING_TYPE" == "Docker" ]]; then
        echo -e "  • ${YELLOW}Статус${NC}: ./scripts/monitoring-control.sh status"
        echo -e "  • ${YELLOW}Логи${NC}: ./scripts/monitoring-control.sh logs"
    fi
else
    print_info "📊 Мониторинг не установлен"
    echo -e "  • ${YELLOW}Для установки${NC}: запустите один из скриптов мониторинга"
    echo -e "  • ${YELLOW}VPS версия${NC}: ./scripts/setup-monitoring-vps.sh"
    echo -e "  • ${YELLOW}Systemd версия${NC}: ./scripts/setup-monitoring-systemd.sh"
    echo -e "  • ${YELLOW}Docker версия${NC}: ./scripts/setup-monitoring-simple.sh"
fi

echo ""
print_info "🤖 Управление ботом:"
echo -e "  • ${YELLOW}Статус${NC}: sudo systemctl status antispam-bot"
echo -e "  • ${YELLOW}Логи${NC}: sudo journalctl -u antispam-bot -f"
echo -e "  • ${YELLOW}Перезапуск${NC}: sudo systemctl restart antispam-bot"
echo -e "  • ${YELLOW}Остановка${NC}: sudo systemctl stop antispam-bot"
echo ""

print_info "🔒 Управление безопасностью:"
echo -e "  • ${YELLOW}Проверка безопасности${NC}: ./scripts/security-check.sh"
echo -e "  • ${YELLOW}Анализ спама${NC}: /spam_analysis (в боте)"
echo -e "  • ${YELLOW}Логи безопасности${NC}: /var/log/flame-of-styx/security/"
echo -e "  • ${YELLOW}Отчеты безопасности${NC}: reports/security/"
echo ""

if [[ "$MONITORING_INSTALLED" == "true" ]]; then
    print_info "💡 Для SSH туннеля (рекомендуется):"
    echo -e "  ssh -L 19999:localhost:19999 -L 3001:localhost:3001 ${USER}@${SERVER_IP}"
    echo -e "  Затем откройте http://localhost:19999 и http://localhost:3001"
fi

echo ""
print_success "Готово! Бот установлен и запущен! 🚀"
