#!/usr/bin/env python3
"""
Скрипт для исправления групп комментариев в базе данных.
Обновляет существующие записи, помечая их как группы комментариев.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.database import SessionLocal
from app.models.channel import Channel
from app.config import load_config

async def fix_comment_groups():
    """Исправляет группы комментариев в базе данных."""
    print("🔧 Исправление групп комментариев в базе данных...")
    
    # Загружаем конфигурацию
    config = load_config()
    print(f"📊 База данных: {config.db_path}")
    
    async with SessionLocal() as db:
        try:
            # Получаем все каналы
            result = await db.execute(select(Channel))
            channels = result.scalars().all()
            
            print(f"📋 Найдено каналов: {len(channels)}")
            
            # Список известных групп комментариев
            comment_group_ids = [
                -1003094131978,  # Test_FlameOfStyx_bot
            ]
            
            updated_count = 0
            
            for channel in channels:
                if channel.telegram_id in comment_group_ids:
                    print(f"🔄 Обновление группы комментариев: {channel.title} ({channel.telegram_id})")
                    
                    # Обновляем запись
                    await db.execute(
                        update(Channel)
                        .where(Channel.id == channel.id)
                        .values(
                            is_comment_group=True,
                            linked_chat_id=-1002451070110  # ID канала психиатра
                        )
                    )
                    updated_count += 1
            
            await db.commit()
            print(f"✅ Обновлено групп комментариев: {updated_count}")
            
            # Проверяем результат
            result = await db.execute(
                select(Channel).where(Channel.is_comment_group == True)
            )
            comment_groups = result.scalars().all()
            
            print(f"📊 Групп комментариев в базе: {len(comment_groups)}")
            for group in comment_groups:
                print(f"  • {group.title} ({group.telegram_id})")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(fix_comment_groups())
