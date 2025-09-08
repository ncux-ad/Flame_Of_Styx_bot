# Руководство по внесению вклада

Спасибо за интерес к проекту AntiSpam Bot! Это руководство поможет вам внести свой вклад в развитие проекта.

## 🚀 Быстрый старт

1. **Fork** репозитория
2. **Clone** вашу копию: `git clone https://github.com/your-username/antispam-bot.git`
3. **Создайте ветку** для ваших изменений: `git checkout -b feature/your-feature`
4. **Установите зависимости**: `pip install -e ".[dev]"`
5. **Установите pre-commit**: `pre-commit install`

## 📋 Процесс разработки

### 1. Настройка окружения

```bash
# Клонирование
git clone https://github.com/your-username/antispam-bot.git
cd antispam-bot

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -e ".[dev]"

# Настройка pre-commit
pre-commit install

# Настройка .env
cp env.example .env
# Отредактируйте .env файл
```

### 2. Локальная разработка

```bash
# Запуск через Docker (рекомендуется)
docker-compose up -d

# Или напрямую
python bot.py
```

### 3. Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=app --cov-report=html

# Запуск конкретного теста
pytest tests/test_bot.py::TestBot::test_settings_validation
```

### 4. Линтеры и форматирование

```bash
# Форматирование кода
black .

# Проверка стиля
ruff check .

# Проверка типов
mypy app/

# Проверка безопасности
safety check
bandit -r app/
```

## 📝 Стиль кода

### Python

- **PEP 8** - основной стандарт
- **Black** - автоматическое форматирование
- **Ruff** - линтер и сортировка импортов
- **MyPy** - проверка типов

### Документация

- **Docstrings** - для всех функций и классов
- **Type hints** - обязательны для всех функций
- **Комментарии** - для сложной логики

### Примеры

```python
async def ban_user(
    self, 
    user_id: int, 
    chat_id: int, 
    admin_id: int,
    reason: Optional[str] = None
) -> bool:
    """Ban user from chat.
    
    Args:
        user_id: Telegram user ID
        chat_id: Chat ID where to ban
        admin_id: Admin who performed the action
        reason: Optional ban reason
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Error banning user {user_id}: {e}")
        return False
```

## 🧪 Тестирование

### Структура тестов

```
tests/
├── conftest.py          # Фикстуры
├── test_bot.py          # Основные тесты
├── test_services/       # Тесты сервисов
├── test_handlers/       # Тесты обработчиков
└── test_models/         # Тесты моделей
```

### Написание тестов

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestModerationService:
    """Test moderation service."""
    
    @pytest.mark.asyncio
    async def test_ban_user_success(self, mock_bot, mock_db):
        """Test successful user ban."""
        service = ModerationService(mock_bot, mock_db)
        
        result = await service.ban_user(
            user_id=123456789,
            chat_id=-1001234567890,
            admin_id=987654321,
            reason="Spam"
        )
        
        assert result is True
        mock_bot.ban_chat_member.assert_called_once()
```

### Покрытие кода

- **Минимум 80%** покрытия для новых функций
- **100%** покрытия для критических компонентов
- Используйте `pytest --cov=app` для проверки

## 📋 Pull Request

### Перед отправкой PR

1. **Обновите документацию** если нужно
2. **Добавьте тесты** для новой функциональности
3. **Проверьте линтеры**: `black . && ruff check . && mypy app/`
4. **Запустите тесты**: `pytest`
5. **Обновите CHANGELOG.md** если нужно

### Шаблон PR

```markdown
## Описание
Краткое описание изменений

## Тип изменений
- [ ] Исправление бага
- [ ] Новая функция
- [ ] Изменение документации
- [ ] Рефакторинг
- [ ] Тесты

## Чек-лист
- [ ] Код следует стилю проекта
- [ ] Добавлены тесты
- [ ] Обновлена документация
- [ ] Все тесты проходят
- [ ] Линтеры не выдают ошибок

## Связанные issues
Closes #123
```

## 🐛 Сообщение об ошибках

### Шаблон issue

```markdown
## Описание ошибки
Четкое описание проблемы

## Шаги для воспроизведения
1. Перейти к '...'
2. Нажать на '...'
3. Прокрутить до '...'
4. Увидеть ошибку

## Ожидаемое поведение
Что должно было произойти

## Фактическое поведение
Что произошло на самом деле

## Скриншоты
Если применимо

## Окружение
- OS: [e.g. Windows 10, Ubuntu 20.04]
- Python: [e.g. 3.11.0]
- aiogram: [e.g. 3.12.0]

## Дополнительная информация
Любая другая информация
```

## 💡 Предложения функций

### Шаблон feature request

```markdown
## Описание функции
Четкое описание желаемой функции

## Проблема
Какую проблему решает эта функция?

## Предлагаемое решение
Как вы видите реализацию?

## Альтернативы
Другие варианты решения

## Дополнительная информация
Любая другая информация
```

## 📚 Документация

### Обновление документации

- **README.md** - основная информация
- **docs/** - подробная документация
- **Docstrings** - документация кода
- **Комментарии** - объяснение сложной логики

### Стиль документации

- **Markdown** для файлов документации
- **Google style** для docstrings
- **Примеры кода** где возможно
- **Диаграммы** для сложных процессов

## 🔧 Инструменты разработки

### Обязательные

- **Python 3.11+**
- **Git**
- **Docker** (для локальной разработки)

### Рекомендуемые

- **VS Code** с расширениями Python
- **PyCharm** Professional
- **GitHub Desktop**

### Расширения VS Code

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-python.mypy-type-checker",
    "ms-vscode.vscode-json"
  ]
}
```

## 📞 Получение помощи

- **GitHub Issues** - для багов и предложений
- **Discussions** - для вопросов
- **Telegram** - для быстрой помощи (если есть)

## 📄 Лицензия

Проект использует MIT лицензию. Внося вклад, вы соглашаетесь с условиями лицензии.

---

Спасибо за ваш вклад в развитие AntiSpam Bot! 🚀
