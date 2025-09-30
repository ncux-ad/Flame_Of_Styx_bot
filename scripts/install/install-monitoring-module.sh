#!/bin/bash

# Модуль установки мониторинга
# Использование: source scripts/install/install-monitoring-module.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
log_info() {
    echo -e "${BLUE}[MONITORING]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[MONITORING]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[MONITORING]${NC} $1"
}

log_error() {
    echo -e "${RED}[MONITORING]${NC} $1"
}

# Установка VPS версии мониторинга
install_vps_monitoring() {
    log_info "Установка VPS версии мониторинга..."
    
    if [[ -f "scripts/setup-monitoring-vps.sh" ]]; then
        chmod +x scripts/setup-monitoring-vps.sh
        ./scripts/setup-monitoring-vps.sh
        log_success "VPS мониторинг установлен"
        return 0
    else
        log_error "Скрипт VPS мониторинга не найден"
        return 1
    fi
}

# Установка Systemd версии мониторинга
install_systemd_monitoring() {
    log_info "Установка Systemd версии мониторинга..."
    
    if [[ -f "scripts/setup-monitoring-systemd.sh" ]]; then
        chmod +x scripts/setup-monitoring-systemd.sh
        ./scripts/setup-monitoring-systemd.sh
        log_success "Systemd мониторинг установлен"
        return 0
    else
        log_error "Скрипт Systemd мониторинга не найден"
        return 1
    fi
}

# Установка Docker версии мониторинга
install_docker_monitoring() {
    log_info "Установка Docker версии мониторинга..."
    
    if [[ -f "scripts/install-monitoring-simple.sh" ]]; then
        chmod +x scripts/install-monitoring-simple.sh
        ./scripts/install-monitoring-simple.sh
        log_success "Docker мониторинг установлен"
        return 0
    else
        log_error "Скрипт Docker мониторинга не найден"
        return 1
    fi
}

# Интерактивный выбор типа мониторинга
choose_monitoring_type() {
    echo -e "${YELLOW}Выберите тип мониторинга:${NC}"
    echo "1) VPS версия (Glances + Healthcheck) - рекомендуется для слабых серверов"
    echo "2) Systemd версия (Glances + Uptime Kuma) - полный функционал"
    echo "3) Docker версия (Prometheus + Grafana) - для мощных серверов"
    echo "4) Пропустить мониторинг"
    
    read -p "Введите номер (1-4): " choice
    
    case $choice in
        1)
            if install_vps_monitoring; then
                echo "VPS"
            else
                echo "None"
            fi
            ;;
        2)
            if install_systemd_monitoring; then
                echo "Systemd"
            else
                echo "None"
            fi
            ;;
        3)
            if install_docker_monitoring; then
                echo "Docker"
            else
                echo "None"
            fi
            ;;
        4)
            log_info "Мониторинг пропущен"
            echo "None"
            ;;
        *)
            log_error "Неверный выбор. Мониторинг пропущен."
            echo "None"
            ;;
    esac
}

# Автоматический выбор типа мониторинга
auto_choose_monitoring() {
    # Проверяем доступность Docker
    if command -v docker &> /dev/null && docker ps &> /dev/null; then
        log_info "Docker доступен, выбираем Docker версию..."
        if install_docker_monitoring; then
            echo "Docker"
        else
            log_warning "Docker мониторинг не удался, пробуем VPS версию..."
            if install_vps_monitoring; then
                echo "VPS"
            else
                echo "None"
            fi
        fi
    else
        log_info "Docker недоступен, выбираем VPS версию..."
        if install_vps_monitoring; then
            echo "VPS"
        else
            log_warning "VPS мониторинг не удался, пробуем Systemd версию..."
            if install_systemd_monitoring; then
                echo "Systemd"
            else
                echo "None"
            fi
        fi
    fi
}

# Основная функция установки мониторинга
install_monitoring() {
    local mode=${1:-"interactive"}  # interactive или auto
    
    log_info "Установка модуля мониторинга..."
    log_info "==============================="
    
    if [[ "$mode" == "auto" ]]; then
        auto_choose_monitoring
    else
        choose_monitoring_type
    fi
}

# Если скрипт запущен напрямую
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    install_monitoring "$1"
fi
