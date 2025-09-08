#!/usr/bin/env python3
"""Script to fix critical log injection vulnerabilities."""

import os
import re
import subprocess
from pathlib import Path


def fix_log_injection_in_file(file_path: Path) -> bool:
    """Fix log injection vulnerabilities in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Add security imports if not present
        if 'from app.utils.security import' not in content and 'logger.' in content:
            # Find the last import
            lines = content.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith(('import ', 'from ')):
                    import_end = i + 1

            # Insert security imports
            lines.insert(import_end, 'from app.utils.security import sanitize_for_logging, safe_format_message')
            content = '\n'.join(lines)

        # Fix specific log injection patterns
        patterns = [
            # Pattern 1: logger.info(f"text {var}")
            (r'logger\.(info|debug|warning|error|critical)\(f"([^"]*)"\)',
             lambda m: f'logger.{m.group(1)}(safe_format_message("{m.group(2).replace("{", "{{").replace("}", "}}")}", '
             + ', '.join([f'{var}=sanitize_for_logging({var})' for var in re.findall(r'\{([^}]+)\}', m.group(2))]) + '))'),

            # Pattern 2: logger.error(f"Error {var}: {e}")
            (r'logger\.error\(f"Error ([^:]+): \{e\}"\)',
             lambda m: f'logger.error(safe_format_message("Error {m.group(1)}: {{error}}", error=sanitize_for_logging(e)))'),
        ]

        for pattern, replacement in patterns:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return False


def main():
    """Main function to fix critical log injection vulnerabilities."""
    print("🚨 Fixing critical log injection vulnerabilities...")

    # Files with critical log injection issues
    critical_files = [
        'app/handlers/user.py',
        'app/services/links.py',
        'app/services/bots.py',
        'app/services/profiles.py',
        'app/services/channels.py',
        'app/services/moderation.py',
        'app/handlers/channels.py'
    ]

    fixed_files = []

    for file_path in critical_files:
        if Path(file_path).exists():
            if fix_log_injection_in_file(Path(file_path)):
                fixed_files.append(file_path)
                print(f"✅ Fixed log injection in: {file_path}")
            else:
                print(f"ℹ️  No changes needed in: {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

    print(f"\n🎉 Fixed log injection vulnerabilities in {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")


if __name__ == '__main__':
    main()
