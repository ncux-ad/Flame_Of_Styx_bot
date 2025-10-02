#!/bin/bash
# Автоматическое тестирование мониторинга для слабых VPS
# Оптимизировано для минимального потребления ресурсов

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции вывода
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Переменные
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.monitoring-test.yml"
TEST_TIMEOUT=60  # Короткий таймаут для слабых VPS
CLEANUP_ON_EXIT=true

# Функция очистки
cleanup() {
    if [ "$CLEANUP_ON_EXIT" = true ]; then
        print_step "Очищаем тестовые контейнеры..."
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.monitoring-test.yml down -v --remove-orphans 2>/dev/null || true
        print_info "Очистка завершена"
    fi
}

# Устанавливаем обработчик сигналов
trap cleanup EXIT INT TERM

# Проверка зависимостей
check_dependencies() {
    print_step "Проверяем зависимости..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен"
        exit 1
    fi
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен"
        exit 1
    fi
    
    # Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 не установлен"
        exit 1
    fi
    
    # aiohttp для Python теста
    if ! python3 -c "import aiohttp" 2>/dev/null; then
        print_warning "aiohttp не установлен, устанавливаем..."
        pip3 install aiohttp --user || {
            print_error "Не удалось установить aiohttp"
            exit 1
        }
    fi
    
    print_success "Все зависимости проверены"
}

# Проверка ресурсов системы
check_system_resources() {
    print_step "Проверяем системные ресурсы..."
    
    # Проверяем свободную память
    if command -v free &> /dev/null; then
        FREE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
        if [ "$FREE_MEM" -lt 512 ]; then
            print_warning "Мало свободной памяти: ${FREE_MEM}MB (рекомендуется >512MB)"
            print_info "Тест будет запущен с минимальными ресурсами"
        else
            print_success "Свободной памяти: ${FREE_MEM}MB"
        fi
    fi
    
    # Проверяем место на диске
    if command -v df &> /dev/null; then
        FREE_DISK=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//')
        if [ "${FREE_DISK%.*}" -lt 2 ]; then
            print_warning "Мало свободного места: ${FREE_DISK}GB"
        else
            print_success "Свободного места: ${FREE_DISK}GB"
        fi
    fi
}

# Запуск тестовых контейнеров
start_test_containers() {
    print_step "Запускаем тестовые контейнеры мониторинга..."
    
    cd "$PROJECT_ROOT"
    
    # Останавливаем существующие тестовые контейнеры
    docker-compose -f docker-compose.monitoring-test.yml down -v --remove-orphans 2>/dev/null || true
    
    # Запускаем новые контейнеры
    if docker-compose -f docker-compose.monitoring-test.yml up -d; then
        print_success "Тестовые контейнеры запущены"
    else
        print_error "Не удалось запустить тестовые контейнеры"
        return 1
    fi
    
    # Ждем запуска сервисов
    print_step "Ждем запуска сервисов (${TEST_TIMEOUT}s)..."
    sleep 10
    
    # Проверяем статус контейнеров
    if docker-compose -f docker-compose.monitoring-test.yml ps | grep -q "Up"; then
        print_success "Контейнеры запущены успешно"
        docker-compose -f docker-compose.monitoring-test.yml ps
    else
        print_error "Контейнеры не запустились"
        print_info "Логи контейнеров:"
        docker-compose -f docker-compose.monitoring-test.yml logs --tail=20
        return 1
    fi
}

# Ожидание готовности сервисов
wait_for_services() {
    print_step "Ожидаем готовности сервисов..."
    
    local max_attempts=12  # 60 секунд максимум
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        
        # Проверяем Netdata
        if curl -s -f "http://localhost:19998/api/v1/info" >/dev/null 2>&1; then
            print_success "Netdata готов (попытка $attempt)"
            break
        fi
        
        print_info "Ожидаем Netdata... (попытка $attempt/$max_attempts)"
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_warning "Netdata не готов после $max_attempts попыток"
    fi
    
    # Проверяем Uptime Kuma (более простая проверка)
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        
        if curl -s "http://localhost:3002/" >/dev/null 2>&1; then
            print_success "Uptime Kuma готов (попытка $attempt)"
            break
        fi
        
        print_info "Ожидаем Uptime Kuma... (попытка $attempt/$max_attempts)"
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_warning "Uptime Kuma не готов после $max_attempts попыток"
    fi
}

# Запуск Python тестов
run_python_tests() {
    print_step "Запускаем Python тесты мониторинга..."
    
    # Создаем временную версию тестера с правильными портами
    local temp_test_file="/tmp/test_monitoring_temp.py"
    
    # Копируем тестер и меняем порты
    sed 's/localhost:19999/localhost:19998/g; s/localhost:3001/localhost:3002/g' \
        "$SCRIPT_DIR/test_monitoring_lightweight.py" > "$temp_test_file"
    
    # Запускаем тесты
    if python3 "$temp_test_file"; then
        print_success "Python тесты прошли успешно"
        local test_result=0
    else
        local exit_code=$?
        if [ $exit_code -eq 1 ]; then
            print_warning "Python тесты прошли частично"
        else
            print_error "Python тесты провалились"
        fi
        local test_result=$exit_code
    fi
    
    # Удаляем временный файл
    rm -f "$temp_test_file"
    
    return $test_result
}

# Проверка производительности
check_performance() {
    print_step "Проверяем производительность контейнеров..."
    
    # Получаем статистику Docker
    if docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
       netdata-test uptime-kuma-test 2>/dev/null; then
        print_success "Статистика ресурсов получена"
    else
        print_warning "Не удалось получить статистику ресурсов"
    fi
}

# Проверка логов
check_logs() {
    print_step "Проверяем логи контейнеров..."
    
    print_info "=== Логи Netdata (последние 10 строк) ==="
    docker-compose -f docker-compose.monitoring-test.yml logs --tail=10 netdata-test || true
    
    print_info "=== Логи Uptime Kuma (последние 10 строк) ==="
    docker-compose -f docker-compose.monitoring-test.yml logs --tail=10 uptime-kuma-test || true
}

# Генерация отчета
generate_report() {
    print_step "Генерируем итоговый отчет..."
    
    local report_file="monitoring_test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "ОТЧЕТ О ТЕСТИРОВАНИИ МОНИТОРИНГА"
        echo "================================"
        echo "Дата: $(date)"
        echo "Хост: $(hostname)"
        echo ""
        
        echo "СИСТЕМНАЯ ИНФОРМАЦИЯ:"
        echo "- OS: $(uname -s -r)"
        echo "- Память: $(free -h | awk 'NR==2{print $2 " всего, " $7 " свободно"}')"
        echo "- Диск: $(df -h / | awk 'NR==2{print $4 " свободно"}')"
        echo ""
        
        echo "СТАТУС КОНТЕЙНЕРОВ:"
        docker-compose -f docker-compose.monitoring-test.yml ps || echo "Контейнеры недоступны"
        echo ""
        
        echo "СТАТИСТИКА РЕСУРСОВ:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
            netdata-test uptime-kuma-test 2>/dev/null || echo "Статистика недоступна"
        echo ""
        
        echo "РЕЗУЛЬТАТЫ ТЕСТОВ:"
        if [ -f "monitoring_test_results.json" ]; then
            echo "Подробные результаты сохранены в monitoring_test_results.json"
        else
            echo "Файл результатов не найден"
        fi
        
    } > "$report_file"
    
    print_success "Отчет сохранен в $report_file"
}

# Основная функция
main() {
    echo "🔍 АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ МОНИТОРИНГА"
    echo "Оптимизировано для слабых VPS серверов"
    echo "========================================"
    echo ""
    
    # Проверяем аргументы
    if [ "${1:-}" = "--no-cleanup" ]; then
        CLEANUP_ON_EXIT=false
        print_info "Очистка после тестов отключена"
    fi
    
    # Выполняем проверки и тесты
    check_dependencies
    check_system_resources
    
    if start_test_containers; then
        wait_for_services
        
        # Запускаем тесты
        local test_exit_code=0
        run_python_tests || test_exit_code=$?
        
        # Дополнительные проверки
        check_performance
        check_logs
        generate_report
        
        # Итоговый результат
        echo ""
        echo "========================================"
        if [ $test_exit_code -eq 0 ]; then
            print_success "🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!"
            echo "Мониторинг готов к использованию на продакшене."
        elif [ $test_exit_code -eq 1 ]; then
            print_warning "⚠️ ТЕСТЫ ПРОШЛИ ЧАСТИЧНО"
            echo "Некоторые компоненты мониторинга могут работать нестабильно."
        else
            print_error "❌ ТЕСТЫ ПРОВАЛИЛИСЬ"
            echo "Мониторинг требует дополнительной настройки."
        fi
        echo "========================================"
        
        return $test_exit_code
    else
        print_error "Не удалось запустить тестовые контейнеры"
        return 1
    fi
}

# Запуск
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
