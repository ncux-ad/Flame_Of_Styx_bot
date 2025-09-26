#!/usr/bin/env python3
"""Script to fix log injection vulnerabilities in Python code."""

import os
import re
from pathlib import Path


def fix_log_injection_in_file(file_path: Path) -> bool:
    """Fix log injection vulnerabilities in a single file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Pattern to match logger calls with f-strings
        pattern = r'logger\.(info|debug|warning|error|critical)\(f"([^"]*)"\)'

        def replace_log_call(match):
            level = match.group(1)
            message = match.group(2)

            # Extract variables from f-string
            variables = re.findall(r"\{([^}]+)\}", message)

            if not variables:
                # No variables, just escape the message
                safe_message = message.replace('"', '\\"')
                return f'logger.{level}("{safe_message}")'

            # Create safe format call
            safe_message = message.replace("{", "{{").replace("}", "}}")
            for var in variables:
                safe_message = safe_message.replace(f"{{{{{var}}}}}", f"{{{var}}}")

            # Create sanitized variable calls
            var_calls = []
            for var in variables:
                var_calls.append(f"{var}=sanitize_for_logging({var})")

            return f'logger.{level}(safe_format_message("{safe_message}", {", ".join(var_calls)}))'

        # Apply replacements
        content = re.sub(pattern, replace_log_call, content)

        # Add import if needed
        if "from app.utils.security import" not in content and "logger." in content:
            # Find the last import statement
            import_lines = []
            other_lines = []
            in_imports = True

            for line in content.split("\n"):
                if in_imports and (line.startswith("import ") or line.startswith("from ")):
                    import_lines.append(line)
                else:
                    in_imports = False
                    other_lines.append(line)

            # Add security import
            if import_lines:
                import_lines.append(
                    "from app.utils.security import sanitize_for_logging, safe_format_message"
                )
                content = "\n".join(import_lines + other_lines)

        # Write back if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return False


def main():
    """Main function to fix all log injection vulnerabilities."""
    app_dir = Path("app")
    fixed_files = []

    # Find all Python files
    for py_file in app_dir.rglob("*.py"):
        if fix_log_injection_in_file(py_file):
            fixed_files.append(py_file)
            print(f"Fixed log injection in: {py_file}")

    print(f"\nFixed log injection vulnerabilities in {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")


if __name__ == "__main__":
    main()
