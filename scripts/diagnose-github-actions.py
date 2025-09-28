#!/usr/bin/env python3
"""
Диагностический скрипт для GitHub Actions
Проверяет все возможные проблемы с workflows
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, description):
    """Выполнить команду и вернуть результат."""
    print(f"CHECK: {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"OK: {description}")
            return True, result.stdout
        else:
            print(f"FAILED: {description}")
            print(f"   Error: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {description}")
        return False, "Command timed out"
    except Exception as e:
        print(f"ERROR: {description} - {e}")
        return False, str(e)

def check_file_exists(filepath, description):
    """Проверить существование файла."""
    if Path(filepath).exists():
        print(f"EXISTS: {description}")
        return True
    else:
        print(f"NOT FOUND: {description}")
        return False

def check_workflow_syntax():
    """Проверить синтаксис YAML файлов workflows."""
    print("\nCHECK: Workflow syntax...")
    
    workflow_files = [
        ".github/workflows/lint.yml",
        ".github/workflows/tests.yml", 
        ".github/workflows/deploy.yml",
        ".github/workflows/basic-test.yml",
        ".github/workflows/minimal.yml",
        ".github/workflows/simple.yml",
        ".github/workflows/import-test.yml",
        ".github/workflows/git-secrets.yml"
    ]
    
    all_valid = True
    for workflow_file in workflow_files:
        if Path(workflow_file).exists():
            success, output = run_command(f"python -c \"import yaml; yaml.safe_load(open('{workflow_file}'))\"", f"YAML syntax: {workflow_file}")
            if not success:
                all_valid = False
                print(f"   ❌ {workflow_file}: {output}")
        else:
            print(f"⚠️  {workflow_file} - NOT FOUND")
    
    return all_valid

def check_python_imports():
    """Проверить импорты Python модулей."""
    print("\n🔍 Проверка Python импортов...")
    
    test_imports = [
        "from app.config import load_config, Settings",
        "from app.services.redis import RedisService", 
        "from app.handlers.admin import admin_router",
        "from app.services.help import HelpService",
        "from app.middlewares.ratelimit import RateLimitMiddleware"
    ]
    
    all_valid = True
    for import_stmt in test_imports:
        success, output = run_command(f"python -c \"{import_stmt}\"", f"Import: {import_stmt}")
        if not success:
            all_valid = False
    
    return all_valid

def check_config_loading():
    """Проверить загрузку конфигурации."""
    print("\n🔍 Проверка загрузки конфигурации...")
    
    # Установить тестовые переменные окружения
    test_env = {
        'BOT_TOKEN': 'test_token_123456789',
        'ADMIN_IDS': '123456789', 
        'DB_PATH': 'test.db',
        'REDIS_ENABLED': 'false',
        'REDIS_URL': 'redis://localhost:6379/0'
    }
    
    env = os.environ.copy()
    env.update(test_env)
    
    try:
        result = subprocess.run(
            "python -c \"from app.config import load_config; config = load_config(); print(f'Config loaded: Redis={config.redis_enabled}')\"",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        
        if result.returncode == 0:
            print(f"✅ Config loading - OK: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Config loading - FAILED: {result.stderr}")
            return False
    except Exception as e:
        print(f"💥 Config loading - ERROR: {e}")
        return False

def check_dependencies():
    """Проверить установленные зависимости."""
    print("\n🔍 Проверка зависимостей...")
    
    required_packages = [
        "aiogram",
        "pydantic-settings", 
        "sqlalchemy",
        "aiosqlite",
        "alembic",
        "punq",
        "aiohttp"
    ]
    
    all_installed = True
    for package in required_packages:
        success, output = run_command(f"python -c \"import {package.replace('-', '_')}\"", f"Package: {package}")
        if not success:
            all_installed = False
    
    return all_installed

def check_test_files():
    """Проверить тестовые файлы."""
    print("\n🔍 Проверка тестовых файлов...")
    
    test_files = [
        "tests/__init__.py",
        "tests/test_config.py",
        "tests/test_redis.py", 
        "tests/test_imports.py"
    ]
    
    all_exist = True
    for test_file in test_files:
        if not check_file_exists(test_file, f"Test file: {test_file}"):
            all_exist = False
    
    return all_exist

def run_pytest():
    """Запустить pytest для проверки тестов."""
    print("\n🔍 Запуск pytest...")
    
    # Установить тестовые переменные окружения
    test_env = {
        'BOT_TOKEN': 'test_token_123456789',
        'ADMIN_IDS': '123456789',
        'DB_PATH': 'test.db', 
        'REDIS_ENABLED': 'false',
        'REDIS_URL': 'redis://localhost:6379/0'
    }
    
    env = os.environ.copy()
    env.update(test_env)
    
    success, output = run_command("python -m pytest tests/ -v --tb=short", "Pytest tests")
    if success:
        print("✅ Pytest - OK")
        return True
    else:
        print(f"❌ Pytest - FAILED: {output}")
        return False

def main():
    """Основная функция диагностики."""
    print("DIAGNOSTIC GITHUB ACTIONS")
    print("=" * 50)
    
    # Проверки
    checks = [
        ("Workflow YAML syntax", check_workflow_syntax),
        ("Python imports", check_python_imports),
        ("Config loading", check_config_loading),
        ("Dependencies", check_dependencies),
        ("Test files", check_test_files),
        ("Pytest execution", run_pytest)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"💥 {check_name} - EXCEPTION: {e}")
            results[check_name] = False
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("FINAL REPORT")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("SUCCESS: All checks passed! GitHub Actions should work.")
    else:
        print("WARNING: There are problems. Check errors above.")
        print("\nRecommendations:")
        print("1. Fix errors in workflows")
        print("2. Check dependencies: pip install -r requirements.txt")
        print("3. Make sure all files exist")
        print("4. Check environment variables in workflows")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
