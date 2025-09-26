#!/bin/bash

# Тест логики --skip-docker
echo "=== Тест логики --skip-docker ==="

# Симулируем переменные
INSTALLATION_TYPE="systemd"
SKIP_DOCKER="true"

# Функция установки Docker (только если нужен)
install_docker() {
    # Пропускаем Docker если явно отключен или не нужен
    if [ "$SKIP_DOCKER" = "true" ]; then
        echo "✅ Docker пропущен (--skip-docker)"
        return 0
    fi
    
    if [ "$INSTALLATION_TYPE" != "docker" ]; then
        echo "✅ Docker не требуется для установки типа: $INSTALLATION_TYPE"
        return 0
    fi
    
    echo "❌ Docker будет установлен"
    return 1
}

# Тест 1: --skip-docker с systemd
echo "Тест 1: --skip-docker с systemd"
INSTALLATION_TYPE="systemd"
SKIP_DOCKER="true"
install_docker

# Тест 2: без --skip-docker с systemd
echo "Тест 2: без --skip-docker с systemd"
INSTALLATION_TYPE="systemd"
SKIP_DOCKER="false"
install_docker

# Тест 3: --skip-docker с docker
echo "Тест 3: --skip-docker с docker"
INSTALLATION_TYPE="docker"
SKIP_DOCKER="true"
install_docker

# Тест 4: без --skip-docker с docker
echo "Тест 4: без --skip-docker с docker"
INSTALLATION_TYPE="docker"
SKIP_DOCKER="false"
install_docker

echo "=== Конец теста ==="
