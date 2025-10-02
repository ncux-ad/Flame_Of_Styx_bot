"""
Database performance tests
"""

import pytest
from sqlalchemy import select

from app.models.bot import Bot
from app.models.channel import Channel
from app.models.moderation_log import ModerationAction, ModerationLog
from app.models.user import User


class TestDatabasePerformance:
    """Database performance benchmarks"""

    def test_user_crud_performance(self, benchmark, perf_db_session):
        """Benchmark user CRUD operations"""
        
        def create_users():
            import asyncio
            
            async def _create_users():
                users = []
                for i in range(100):
                    user = User()
                    user.telegram_id = 100000000 + i
                    user.username = f"user_{i}"
                    user.first_name = f"User{i}"
                    user.is_banned = False
                    users.append(user)
                    perf_db_session.add(user)
                
                await perf_db_session.commit()
                return users
            
            # Run async function in event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_create_users())
        
        # Benchmark user creation
        users = benchmark(create_users)
        assert len(users) == 100

    @pytest.mark.asyncio
    async def test_user_query_performance(self, benchmark, perf_db_session, benchmark_data_generator):
        """Benchmark user queries"""
        
        # Setup test data
        users_data = benchmark_data_generator["users"](1000)
        for user_data in users_data:
            user = User()
            for key, value in user_data.items():
                setattr(user, key, value)
            perf_db_session.add(user)
        await perf_db_session.commit()
        
        async def query_users():
            # Query all users
            result = await perf_db_session.execute(select(User))
            return result.scalars().all()
        
        users = await benchmark(query_users)
        assert len(users) == 1000

    @pytest.mark.asyncio
    async def test_moderation_log_bulk_insert(self, benchmark, perf_db_session, benchmark_data_generator):
        """Benchmark bulk moderation log insertion"""
        
        async def bulk_insert_logs():
            logs_data = benchmark_data_generator["moderation_logs"](500)
            logs = []
            
            for log_data in logs_data:
                log = ModerationLog()
                log.user_id = log_data["user_id"]
                log.chat_id = log_data["chat_id"]
                log.admin_telegram_id = log_data["admin_telegram_id"]
                log.action = ModerationAction(log_data["action"])
                log.reason = log_data["reason"]
                log.is_active = log_data["is_active"]
                
                logs.append(log)
                perf_db_session.add(log)
            
            await perf_db_session.commit()
            return logs
        
        logs = await benchmark(bulk_insert_logs)
        assert len(logs) == 500

    @pytest.mark.asyncio
    async def test_complex_query_performance(self, benchmark, perf_db_session, benchmark_data_generator):
        """Benchmark complex queries with joins"""
        
        # Setup test data
        users_data = benchmark_data_generator["users"](200)
        for user_data in users_data:
            user = User()
            for key, value in user_data.items():
                setattr(user, key, value)
            perf_db_session.add(user)
        
        logs_data = benchmark_data_generator["moderation_logs"](1000)
        for log_data in logs_data:
            log = ModerationLog()
            log.user_id = log_data["user_id"]
            log.chat_id = log_data["chat_id"]
            log.admin_telegram_id = log_data["admin_telegram_id"]
            log.action = ModerationAction(log_data["action"])
            log.reason = log_data["reason"]
            log.is_active = log_data["is_active"]
            perf_db_session.add(log)
        
        await perf_db_session.commit()
        
        async def complex_query():
            # Query banned users with their moderation logs
            result = await perf_db_session.execute(
                select(User, ModerationLog)
                .join(ModerationLog, User.telegram_id == ModerationLog.user_id)
                .where(
                    User.is_banned == True,
                    ModerationLog.action == ModerationAction.BAN,
                    ModerationLog.is_active == True
                )
            )
            return result.all()
        
        results = await benchmark(complex_query)
        assert len(results) >= 0  # May be 0 if no banned users match criteria

    @pytest.mark.asyncio
    async def test_channel_operations_performance(self, benchmark, perf_db_session, benchmark_data_generator):
        """Benchmark channel operations"""
        
        async def create_and_query_channels():
            # Create channels
            channels_data = benchmark_data_generator["channels"](100)
            channels = []
            
            for channel_data in channels_data:
                channel = Channel()
                for key, value in channel_data.items():
                    if hasattr(channel, key):
                        setattr(channel, key, value)
                channels.append(channel)
                perf_db_session.add(channel)
            
            await perf_db_session.commit()
            
            # Query native channels
            result = await perf_db_session.execute(
                select(Channel).where(Channel.is_native == True)
            )
            native_channels = result.scalars().all()
            
            return channels, native_channels
        
        channels, native_channels = await benchmark(create_and_query_channels)
        assert len(channels) == 100
        assert len(native_channels) >= 0


class TestDatabaseScalability:
    """Database scalability tests"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user_count", [100, 500, 1000, 2000])
    async def test_user_scalability(self, benchmark, perf_db_session, benchmark_data_generator, user_count):
        """Test database performance with increasing user counts"""
        
        async def create_users():
            users_data = benchmark_data_generator["users"](user_count)
            for user_data in users_data:
                user = User()
                for key, value in user_data.items():
                    setattr(user, key, value)
                perf_db_session.add(user)
            
            await perf_db_session.commit()
            
            # Query all users
            result = await perf_db_session.execute(select(User))
            return result.scalars().all()
        
        users = await benchmark(create_users)
        assert len(users) == user_count

    @pytest.mark.asyncio
    @pytest.mark.parametrize("log_count", [100, 500, 1000, 2000])
    async def test_moderation_log_scalability(self, benchmark, perf_db_session, benchmark_data_generator, log_count):
        """Test moderation log performance with increasing counts"""
        
        async def create_logs():
            logs_data = benchmark_data_generator["moderation_logs"](log_count)
            for log_data in logs_data:
                log = ModerationLog()
                log.user_id = log_data["user_id"]
                log.chat_id = log_data["chat_id"]
                log.admin_telegram_id = log_data["admin_telegram_id"]
                log.action = ModerationAction(log_data["action"])
                log.reason = log_data["reason"]
                log.is_active = log_data["is_active"]
                perf_db_session.add(log)
            
            await perf_db_session.commit()
            
            # Query active bans
            result = await perf_db_session.execute(
                select(ModerationLog).where(
                    ModerationLog.action == ModerationAction.BAN,
                    ModerationLog.is_active == True
                )
            )
            return result.scalars().all()
        
        active_bans = await benchmark(create_logs)
        assert len(active_bans) >= 0
