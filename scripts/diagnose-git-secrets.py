#!/usr/bin/env python3
"""
Диагностический скрипт для Git Secrets
Проверяет, какие паттерны срабатывают в проекте
"""

import os
import re
import subprocess
from pathlib import Path

def check_git_secrets_patterns():
    """Проверяем, какие паттерны Git Secrets срабатывают."""
    print("=== GIT SECRETS DIAGNOSTIC ===")
    
    # Паттерны из Git Secrets (только те, что реально используются)
    patterns = [
        # Telegram Bot Tokens
        r'[0-9]{8,10}:[A-Za-z0-9_-]{35}',
        # Database URLs
        r'postgresql://[^:]+:[^@]+@[^/]+/[^/]+',
        r'mysql://[^:]+:[^@]+@[^/]+/[^/]+',
        # Redis URLs
        r'redis://[^:]+:[^@]+@[^/]+',
        # JWT Tokens
        r'eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
    ]
    
    # Файлы для проверки
    files_to_check = [
        'app/config.py',
        'bot.py',
        'requirements.txt',
        'pyproject.toml',
        '.github/workflows/deploy.yml',
        '.github/workflows/lint.yml',
        '.github/workflows/tests.yml',
        '.github/workflows/basic-test.yml',
        '.github/workflows/minimal.yml',
        '.github/workflows/simple.yml',
        '.github/workflows/ultra-simple.yml',
        '.github/workflows/import-test.yml',
        '.github/workflows/check.yml',
        '.github/workflows/git-secrets.yml',
    ]
    
    matches_found = []
    
    for file_path in files_to_check:
        if not Path(file_path).exists():
            continue
            
        print(f"\nChecking {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            matches_found.append({
                                'file': file_path,
                                'line': line_num,
                                'pattern': pattern,
                                'content': line.strip()
                            })
                            print(f"  MATCH: Line {line_num}")
                            print(f"    Pattern: {pattern}")
                            print(f"    Content: {line.strip()}")
                            
        except Exception as e:
            print(f"  ERROR reading {file_path}: {e}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total matches found: {len(matches_found)}")
    
    if matches_found:
        print("\nDetailed matches:")
        for match in matches_found:
            print(f"  {match['file']}:{match['line']} - {match['pattern']}")
            print(f"    {match['content']}")
    
    return matches_found

def check_specific_patterns():
    """Проверяем конкретные проблемные паттерны."""
    print("\n=== CHECKING SPECIFIC PATTERNS ===")
    
    # Проверяем тестовые токены
    test_tokens = [
        "123456789:test_token_123456789",
        "BOT_TOKEN: 123456789:test_token_123456789",
        "BOT_TOKEN=123456789:test_token_123456789",
    ]
    
    for token in test_tokens:
        print(f"\nTesting token: {token}")
        
        # Проверяем против паттерна Telegram токенов
        telegram_pattern = r'[0-9]{8,10}:[A-Za-z0-9_-]{35}'
        if re.search(telegram_pattern, token):
            print(f"  MATCHES Telegram pattern: {telegram_pattern}")
        else:
            print(f"  Does NOT match Telegram pattern")
        
        # Проверяем против паттерна токенов
        token_pattern = r'token[_-]?[=:]\s*[A-Za-z0-9!@#$%^&*()_+-=]{30,}'
        if re.search(token_pattern, token, re.IGNORECASE):
            print(f"  MATCHES token pattern: {token_pattern}")
        else:
            print(f"  Does NOT match token pattern")

def main():
    """Основная функция диагностики."""
    matches = check_git_secrets_patterns()
    check_specific_patterns()
    
    if matches:
        print(f"\n=== RECOMMENDATIONS ===")
        print("1. Add more specific allowed patterns to .gitsecrets")
        print("2. Update .gitsecrets to exclude test patterns")
        print("3. Check if matches are false positives")
        
        # Предлагаем исправления
        print(f"\n=== SUGGESTED FIXES ===")
        print("Add these patterns to .gitsecrets as allowed:")
        print("  test_token_[A-Za-z0-9_]+")
        print("  BOT_TOKEN=123456789:test_token_")
        print("  ADMIN_IDS=123456789")
        print("  DB_PATH=test.db")
        print("  REDIS_URL=redis://localhost:6379/0")

if __name__ == "__main__":
    main()
