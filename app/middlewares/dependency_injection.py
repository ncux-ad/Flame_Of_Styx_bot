"""
Dependency Injection middleware с использованием Aiogram встроенного DI.

Этот файл оставлен для совместимости, но теперь использует DIMiddleware.
"""

from app.middlewares.di_middleware import DIMiddleware

# Алиас для совместимости
DependencyInjectionMiddleware = DIMiddleware
