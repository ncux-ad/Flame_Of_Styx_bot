#!/usr/bin/env python3
"""
Simple diagnostic script for GitHub Actions
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run command and return result."""
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
    except Exception as e:
        print(f"ERROR: {description} - {e}")
        return False, str(e)

def check_file_exists(filepath, description):
    """Check if file exists."""
    if Path(filepath).exists():
        print(f"EXISTS: {description}")
        return True
    else:
        print(f"NOT FOUND: {description}")
        return False

def main():
    """Main diagnostic function."""
    print("DIAGNOSTIC GITHUB ACTIONS")
    print("=" * 50)
    
    # Check 1: Python imports
    print("\n1. Checking Python imports...")
    imports = [
        "from app.config import load_config, Settings",
        "from app.services.redis import RedisService",
        "from app.handlers.admin import admin_router"
    ]
    
    for import_stmt in imports:
        success, output = run_command(f"python -c \"{import_stmt}\"", f"Import: {import_stmt}")
        if not success:
            print(f"   FAILED: {import_stmt}")
    
    # Check 2: Config loading
    print("\n2. Checking config loading...")
    test_env = {
        'BOT_TOKEN': '123456789:test_token_123456789',
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
            print(f"OK: Config loading - {result.stdout.strip()}")
        else:
            print(f"FAILED: Config loading - {result.stderr}")
    except Exception as e:
        print(f"ERROR: Config loading - {e}")
    
    # Check 3: Workflow files
    print("\n3. Checking workflow files...")
    workflow_files = [
        ".github/workflows/lint.yml",
        ".github/workflows/tests.yml",
        ".github/workflows/deploy.yml",
        ".github/workflows/basic-test.yml"
    ]
    
    for workflow_file in workflow_files:
        check_file_exists(workflow_file, f"Workflow: {workflow_file}")
    
    # Check 4: Test files
    print("\n4. Checking test files...")
    test_files = [
        "tests/__init__.py",
        "tests/test_config.py",
        "tests/test_redis.py",
        "tests/test_imports.py"
    ]
    
    for test_file in test_files:
        check_file_exists(test_file, f"Test: {test_file}")
    
    # Check 5: Dependencies
    print("\n5. Checking dependencies...")
    deps = ["aiogram", "pydantic-settings", "sqlalchemy", "aiohttp"]
    for dep in deps:
        success, output = run_command(f"python -c \"import {dep.replace('-', '_')}\"", f"Package: {dep}")
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
