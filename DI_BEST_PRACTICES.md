# Руководство по лучшим практикам Dependency Injection в aiogram 3

## ✅ Что исправлено в проекте

### 1. Правильная сигнатура middleware
```python
class DependencyInjectionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # middleware logic
        return await handler(event, data)  # ✅ Правильно
```

### 2. Правильная сигнатура обработчиков
```python
@router.message(Command("start"))
async def handle_start_command(message: Message, data: dict = None) -> None:
    # Получаем сервисы из data
    if data:
        service = data.get('service_name')
```

## 📚 Основные принципы DI в aiogram 3

### 1. Middleware должен передавать данные через `data` словарь
- ✅ `return await handler(event, data)`
- ❌ `return await handler(event, **data)`

### 2. Обработчики должны принимать `data: dict = None`
- ✅ `async def handler(message: Message, data: dict = None)`
- ❌ `async def handler(message: Message, **kwargs)`

### 3. Регистрация middleware для всех типов обновлений
```python
# Регистрируем для всех типов обновлений
dp.message.middleware(DependencyInjectionMiddleware())
dp.callback_query.middleware(DependencyInjectionMiddleware())
dp.my_chat_member.middleware(DependencyInjectionMiddleware())
# ... и так далее
```

## 🔧 Альтернативные подходы

### 1. Использование aiogram3-di (рекомендуется для новых проектов)
```python
from aiogram3_di import setup_di, Depends

# Настройка DI
setup_di(dp)

# В обработчиках
@router.message()
async def handler(
    message: Message,
    service: Service = Depends(get_service)
) -> None:
    pass
```

### 2. Передача зависимостей через контекст Dispatcher
```python
# При создании Dispatcher
dp = Dispatcher(foo=42, bar="baz")

# В обработчиках
@router.message()
async def handler(message: Message, foo: int, bar: str) -> None:
    pass
```

## ⚠️ Частые ошибки

### 1. Неправильная передача данных в middleware
```python
# ❌ Неправильно
return await handler(event, **filtered_data)

# ✅ Правильно
return await handler(event, data)
```

### 2. Неправильная сигнатура обработчиков
```python
# ❌ Неправильно
async def handler(message: Message, service: Service = None, **kwargs)

# ✅ Правильно
async def handler(message: Message, data: dict = None)
    service = data.get('service') if data else None
```

### 3. Регистрация middleware только для message
```python
# ❌ Неправильно
dp.message.middleware(DependencyInjectionMiddleware())

# ✅ Правильно
dp.message.middleware(DependencyInjectionMiddleware())
dp.callback_query.middleware(DependencyInjectionMiddleware())
# ... для всех типов обновлений
```

## 🎯 Рекомендации для проекта

1. **Текущая реализация работает правильно** - используйте `data: dict = None`
2. **Рассмотрите aiogram3-di** для новых функций
3. **Документируйте все сервисы** в `DependencyInjectionMiddleware`
4. **Тестируйте middleware** с разными типами обновлений

## 📖 Полезные ссылки

- [Официальная документация aiogram 3 - Middlewares](https://docs.aiogram.dev/en/v3.1.0/dispatcher/middlewares.html)
- [Официальная документация aiogram 3 - Dependency Injection](https://docs.aiogram.dev/en/v3.19.0/dispatcher/dependency_injection.html)
- [aiogram3-di на PyPI](https://pypi.org/project/aiogram3-di/)
- [Руководство по aiogram 3](https://mastergroosha.github.io/aiogram-3-guide/filters-and-middlewares/)
