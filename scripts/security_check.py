#!/usr/bin/env python3
"""
Security check script for AntiSpam Bot.
Проверяет безопасность конфигурации и кода.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityChecker:
    """Класс для проверки безопасности бота."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.issues = []
        self.warnings = []
        self.recommendations = []

    def run_all_checks(self) -> Dict[str, Any]:
        """Запуск всех проверок безопасности."""
        logger.info("🔍 Запуск проверки безопасности...")

        # Проверки конфигурации
        self.check_environment_variables()
        self.check_docker_security()
        self.check_file_permissions()

        # Проверки кода
        self.check_code_security()
        self.check_dependencies()

        # Проверки сети
        self.check_network_security()

        # Генерация отчета
        return self.generate_report()

    def check_environment_variables(self):
        """Проверка переменных окружения."""
        logger.info("🔐 Проверка переменных окружения...")

        # Проверка .env файла
        env_file = self.project_root / ".env"
        if env_file.exists():
            self.warnings.append("⚠️ .env файл найден в репозитории. Убедитесь, что он не содержит секретов.")

        # Проверка .env.example
        env_example = self.project_root / "env.example"
        if not env_example.exists():
            self.issues.append("❌ Отсутствует .env.example файл")
        else:
            self.recommendations.append("✅ .env.example файл найден")

        # Проверка .gitignore
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            with open(gitignore, 'r', encoding='utf-8') as f:
                content = f.read()
                if '.env' in content:
                    self.recommendations.append("✅ .env файл исключен из Git")
                else:
                    self.issues.append("❌ .env файл не исключен из .gitignore")
        else:
            self.issues.append("❌ Отсутствует .gitignore файл")

    def check_docker_security(self):
        """Проверка безопасности Docker."""
        logger.info("🐳 Проверка безопасности Docker...")

        # Проверка Dockerfile
        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            with open(dockerfile, 'r', encoding='utf-8') as f:
                content = f.read()

                # Проверка на использование root пользователя
                if "USER root" in content or "RUN useradd" not in content:
                    self.warnings.append("⚠️ Dockerfile может использовать root пользователя")

                # Проверка на копирование секретов
                if "COPY .env" in content:
                    self.issues.append("❌ Dockerfile копирует .env файл")

                # Проверка на обновление пакетов
                if "apt-get update" in content and "apt-get upgrade" not in content:
                    self.warnings.append("⚠️ Dockerfile обновляет пакеты, но не обновляет систему")
        else:
            self.issues.append("❌ Отсутствует Dockerfile")

        # Проверка docker-compose.yml
        compose_file = self.project_root / "docker-compose.yml"
        if compose_file.exists():
            with open(compose_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Проверка на хардкод секретов
                if "BOT_TOKEN=" in content and "your_telegram_bot_token_here" not in content:
                    self.issues.append("❌ BOT_TOKEN захардкожен в docker-compose.yml")

                # Проверка на использование volumes для секретов
                if "secrets:" not in content:
                    self.warnings.append("⚠️ docker-compose.yml не использует Docker secrets")
        else:
            self.issues.append("❌ Отсутствует docker-compose.yml")

    def check_file_permissions(self):
        """Проверка прав доступа к файлам."""
        logger.info("📁 Проверка прав доступа к файлам...")

        # Проверка прав на .env файл
        env_file = self.project_root / ".env"
        if env_file.exists():
            stat = env_file.stat()
            if stat.st_mode & 0o077:  # Проверка на права для группы и других
                self.issues.append(f"❌ .env файл имеет слишком открытые права: {oct(stat.st_mode)}")
            else:
                self.recommendations.append("✅ .env файл имеет корректные права доступа")

        # Проверка прав на скрипты
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.glob("*.py"):
                if not script.stat().st_mode & 0o111:  # Проверка на права выполнения
                    self.warnings.append(f"⚠️ Скрипт {script.name} не имеет прав на выполнение")

    def check_code_security(self):
        """Проверка безопасности кода."""
        logger.info("🔍 Проверка безопасности кода...")

        # Проверка на использование опасных функций (только в наших файлах)
        for py_file in self.project_root.rglob("*.py"):
            if py_file.name.startswith("__") or "venv" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # Проверка на опасные функции
                    if "os.system" in content:
                        self.issues.append(f"❌ {py_file.relative_to(self.project_root)} использует os.system")

                    if "eval(" in content:
                        self.issues.append(f"❌ {py_file.relative_to(self.project_root)} использует eval()")

                    if "exec(" in content:
                        self.issues.append(f"❌ {py_file.relative_to(self.project_root)} использует exec()")

                    # Проверка на логирование секретов
                    if "logger" in content and "token" in content.lower():
                        self.warnings.append(f"⚠️ {py_file.relative_to(self.project_root)} может логировать токены")

            except Exception as e:
                logger.warning(f"Ошибка при проверке {py_file}: {e}")

    def check_dependencies(self):
        """Проверка зависимостей на уязвимости."""
        logger.info("📦 Проверка зависимостей...")

        # Проверка requirements.txt
        requirements = self.project_root / "requirements.txt"
        if requirements.exists():
            self.recommendations.append("✅ requirements.txt найден")

            # Проверка на устаревшие пакеты
            with open(requirements, 'r', encoding='utf-8') as f:
                content = f.read()

                # Проверка на конкретные уязвимые пакеты
                vulnerable_packages = [
                    "requests<2.20.0",
                    "urllib3<1.24.0",
                    "pyyaml<5.1"
                ]

                for package in vulnerable_packages:
                    if package.split("<")[0] in content:
                        self.warnings.append(f"⚠️ Возможно уязвимый пакет: {package}")
        else:
            self.issues.append("❌ Отсутствует requirements.txt")

        # Проверка requirements-dev.txt
        dev_requirements = self.project_root / "requirements-dev.txt"
        if dev_requirements.exists():
            self.recommendations.append("✅ requirements-dev.txt найден")
        else:
            self.warnings.append("⚠️ Отсутствует requirements-dev.txt")

    def check_network_security(self):
        """Проверка сетевой безопасности."""
        logger.info("🌐 Проверка сетевой безопасности...")

        # Проверка nginx конфигурации
        nginx_conf = self.project_root / "nginx" / "nginx.conf"
        if nginx_conf.exists():
            with open(nginx_conf, 'r', encoding='utf-8') as f:
                content = f.read()

                # Проверка на SSL
                if "ssl_certificate" in content:
                    self.recommendations.append("✅ Nginx настроен для SSL")
                else:
                    self.warnings.append("⚠️ Nginx не настроен для SSL")

                # Проверка на заголовки безопасности
                security_headers = [
                    "X-Frame-Options",
                    "X-Content-Type-Options",
                    "X-XSS-Protection",
                    "Strict-Transport-Security"
                ]

                for header in security_headers:
                    if header in content:
                        self.recommendations.append(f"✅ Заголовок {header} настроен")
                    else:
                        self.warnings.append(f"⚠️ Заголовок {header} не настроен")
        else:
            self.warnings.append("⚠️ Отсутствует конфигурация Nginx")

    def generate_report(self) -> Dict[str, Any]:
        """Генерация отчета о безопасности."""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_recommendations = len(self.recommendations)

        # Определение статуса безопасности
        if total_issues == 0:
            if total_warnings == 0:
                security_status = "🟢 ОТЛИЧНО"
            else:
                security_status = "🟡 ХОРОШО"
        else:
            security_status = "🔴 ТРЕБУЕТ ВНИМАНИЯ"

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "security_status": security_status,
            "summary": {
                "total_issues": total_issues,
                "total_warnings": total_warnings,
                "total_recommendations": total_recommendations
            },
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations
        }

        # Сохранение отчета
        report_file = self.project_root / "security-report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 Отчет сохранен в {report_file}")

        return report

    def print_report(self, report: Dict[str, Any]):
        """Вывод отчета в консоль."""
        print("\n" + "="*60)
        print("🔒 ОТЧЕТ О БЕЗОПАСНОСТИ ANTI-SPAM BOT")
        print("="*60)

        print(f"\n📊 Статус безопасности: {report['security_status']}")
        print(f"📈 Всего проблем: {report['summary']['total_issues']}")
        print(f"⚠️ Предупреждений: {report['summary']['total_warnings']}")
        print(f"✅ Рекомендаций: {report['summary']['total_recommendations']}")

        if report['issues']:
            print("\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for issue in report['issues']:
                print(f"  {issue}")

        if report['warnings']:
            print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
            for warning in report['warnings']:
                print(f"  {warning}")

        if report['recommendations']:
            print("\n✅ РЕКОМЕНДАЦИИ:")
            for rec in report['recommendations']:
                print(f"  {rec}")

        print("\n" + "="*60)

        # Рекомендации по улучшению
        print("\n🚀 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
        print("1. Запустите: pip install bandit safety")
        print("2. Выполните: bandit -r app/")
        print("3. Выполните: safety check")
        print("4. Настройте Docker secrets для продакшена")
        print("5. Регулярно обновляйте зависимости")
        print("6. Настройте мониторинг безопасности")

        print("\n" + "="*60)

def main():
    """Главная функция."""
    checker = SecurityChecker()
    report = checker.run_all_checks()
    checker.print_report(report)

    # Возвращаем код выхода в зависимости от количества проблем
    if report['summary']['total_issues'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
