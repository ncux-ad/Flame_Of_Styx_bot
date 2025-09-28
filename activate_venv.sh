#!/bin/bash
# Activate virtual environment for Linux/macOS
echo "Activating virtual environment..."
source venv/bin/activate
echo "Virtual environment activated!"
echo "Python path: $(which python)"
echo ""
echo "You can now run:"
echo "  python bot.py"
echo "  python -m pytest"
echo "  python -m black ."
echo "  python -m ruff check ."
echo "  python -m mypy ."
echo "  python -m safety check"
echo "  python -m bandit -r app/"
echo ""
exec bash
