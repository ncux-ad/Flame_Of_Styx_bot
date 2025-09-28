#!/bin/bash
# Мастер-скрипт установки мониторинга с выбором вариантов

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🚀 Установка мониторинга для AntiSpam Bot${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${YELLOW}💡 Systemd - ОСНОВНОЙ вариант (оптимизировано для VPS)${NC}"
    echo -e "${YELLOW}💡 Docker - альтернативный вариант${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
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

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_menu() {
    echo -e "${CYAN}📋 Выберите вариант установки:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} ⚙️ Systemd (ОСНОВНОЙ - оптимизировано для VPS)"
    echo -e "   • Минимальное использование ресурсов"
    echo -e "   • Нет зависимости от Docker"
    echo -e "   • Полная сборка Uptime Kuma"
    echo ""
    echo -e "${GREEN}2)${NC} 🐳 Docker (альтернатива)"
    echo -e "   • Простая установка"
    echo -e "   • Изолированная среда"
    echo -e "   • Автоматическая сборка"
    echo ""
    echo -e "${GREEN}3)${NC} 🔧 Простая установка Uptime Kuma"
    echo -e "   • Без сборки фронтенда"
    echo -e "   • Только production зависимости"
    echo ""
    echo -e "${GREEN}4)${NC} 🔧 Принудительное исправление"
    echo -e "   • Исправляет существующие проблемы"
    echo -e "   • Переустанавливает с нуля"
    echo ""
    echo -e "${GREEN}5)${NC} 📊 Только Netdata"
    echo -e "   • Только мониторинг сервера"
    echo -e "   • Без Uptime Kuma"
    echo ""
    echo -e "${GREEN}6)${NC} 🚀 Простой мониторинг (РЕКОМЕНДУЕТСЯ)"
    echo -e "   • Netdata + встроенный healthcheck"
    echo -e "   • Без сложных зависимостей"
    echo ""
    echo -e "${GREEN}7)${NC} 🌐 Внешний мониторинг"
    echo -e "   • Netdata + внешние сервисы"
    echo -e "   • Uptime Robot, Healthcheck.io"
    echo ""
    echo -e "${GREEN}8)${NC} ❌ Отмена"
    echo ""
}

print_header

# Проверяем права
if [[ $EUID -eq 0 ]]; then
    print_error "Не запускайте скрипт от root! Используйте sudo при необходимости."
    exit 1
fi

# Проверяем систему
print_step "Проверяем систему..."
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    print_info "ОС: $NAME $VERSION"
else
    print_warning "Не удалось определить ОС"
fi

# Проверяем доступные команды
DOCKER_AVAILABLE=false
SYSTEMD_AVAILABLE=false

if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    DOCKER_AVAILABLE=true
    print_success "Docker доступен"
else
    print_info "Docker не установлен"
fi

if command -v systemctl &> /dev/null; then
    SYSTEMD_AVAILABLE=true
    print_success "Systemd доступен"
else
    print_warning "Systemd не доступен"
fi

echo ""

# Показываем меню
print_menu

# Читаем выбор пользователя
while true; do
    read -p "Введите номер варианта (1-5): " choice
    case $choice in
        1)
            if [[ "$SYSTEMD_AVAILABLE" == "true" ]]; then
                print_step "Запускаем Systemd установку (ОСНОВНОЙ - VPS оптимизация)..."
                chmod +x scripts/install-uptime-kuma-vps-optimized.sh
                ./scripts/install-uptime-kuma-vps-optimized.sh
                break
            else
                print_error "Systemd не доступен на этой системе"
                echo ""
                read -p "Нажмите Enter для продолжения..."
                print_menu
            fi
            ;;
        2)
            if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
                print_step "Запускаем Docker установку (альтернатива)..."
                chmod +x scripts/install-monitoring-simple.sh
                ./scripts/install-monitoring-simple.sh
                break
            else
                print_error "Docker не установлен. Установите Docker сначала:"
                echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
                echo "   sudo sh get-docker.sh"
                echo "   sudo usermod -aG docker $USER"
                echo ""
                read -p "Нажмите Enter для продолжения..."
                print_menu
            fi
            ;;
        3)
            print_step "Запускаем простую установку Uptime Kuma..."
            chmod +x scripts/install-uptime-kuma-simple.sh
            ./scripts/install-uptime-kuma-simple.sh
            break
            ;;
        4)
            print_step "Запускаем принудительное исправление..."
            chmod +x scripts/force-fix-uptime-kuma.sh
            ./scripts/force-fix-uptime-kuma.sh
            break
            ;;
        5)
            print_step "Устанавливаем только Netdata..."
            chmod +x scripts/install-netdata-only.sh
            ./scripts/install-netdata-only.sh
            break
            ;;
        6)
            print_step "Запускаем простой мониторинг..."
            chmod +x scripts/install-simple-monitoring.sh
            ./scripts/install-simple-monitoring.sh
            break
            ;;
        7)
            print_step "Запускаем внешний мониторинг..."
            chmod +x scripts/install-external-monitoring.sh
            ./scripts/install-external-monitoring.sh
            break
            ;;
        8)
            print_info "Установка отменена"
            exit 0
            ;;
        *)
            print_error "Неверный выбор. Введите число от 1 до 8."
            ;;
    esac
done

print_success "🎉 Установка мониторинга завершена!"
