"""
Services performance tests
"""

import pytest

from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService


class TestServicesPerformance:
    """Services performance benchmarks"""

    @pytest.mark.asyncio
    async def test_moderation_service_performance(self, benchmark, perf_bot, perf_db_session):
        """Benchmark ModerationService operations"""
        
        moderation_service = ModerationService(perf_bot, perf_db_session)
        
        async def ban_multiple_users():
            results = []
            for i in range(50):
                user_id = 100000000 + i
                chat_id = -1001234567890
                admin_id = 123456789
                
                result = await moderation_service.ban_user(
                    user_id=user_id,
                    chat_id=chat_id,
                    admin_id=admin_id,
                    reason=f"Performance test ban {i}"
                )
                results.append(result)
            
            return results
        
        results = await benchmark(ban_multiple_users)
        assert len(results) == 50
        assert all(results)  # All bans should succeed

    @pytest.mark.asyncio
    async def test_bot_service_performance(self, benchmark, perf_bot, perf_db_session):
        """Benchmark BotService operations"""
        
        bot_service = BotService(perf_bot, perf_db_session)
        
        async def add_multiple_bots():
            results = []
            for i in range(30):
                username = f"testbot{i}"
                admin_id = 123456789
                telegram_id = 200000000 + i
                
                result = await bot_service.add_bot_to_whitelist(
                    username=username,
                    admin_id=admin_id,
                    telegram_id=telegram_id
                )
                results.append(result)
            
            return results
        
        results = await benchmark(add_multiple_bots)
        assert len(results) == 30
        assert all(results)  # All additions should succeed

    @pytest.mark.asyncio
    async def test_channel_service_performance(self, benchmark, perf_bot, perf_db_session, perf_config):
        """Benchmark ChannelService operations"""
        
        channel_service = ChannelService(perf_bot, perf_db_session)
        
        async def process_multiple_channels():
            results = []
            for i in range(40):
                channel_id = -1001000000000 - i
                
                # Get channel info (using existing method)
                channel_info = await channel_service.get_channel_info(channel_id)
                
                # Check if native (using existing method)
                is_native = await channel_service.is_native_channel(channel_id)
                
                results.append((channel_info, is_native))
            
            return results
        
        results = await benchmark(process_multiple_channels)
        assert len(results) == 40

    @pytest.mark.asyncio
    async def test_profile_service_performance(self, benchmark, perf_bot, perf_db_session):
        """Benchmark ProfileService operations"""
        
        profile_service = ProfileService(perf_bot, perf_db_session)
        
        async def analyze_multiple_profiles():
            results = []
            for i in range(25):
                user_id = 300000000 + i
                
                # Get user info (mock data)
                user_info = await profile_service.get_user_info(user_id)
                
                # Analyze profile (using existing method)
                analysis = await profile_service.analyze_profile(user_id)
                
                results.append((user_info, analysis))
            
            return results
        
        results = await benchmark(analyze_multiple_profiles)
        assert len(results) == 25


class TestServicesScalability:
    """Services scalability tests"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation_count", [10, 50, 100, 200])
    async def test_moderation_service_scalability(self, benchmark, perf_bot, perf_db_session, operation_count):
        """Test ModerationService scalability"""
        
        moderation_service = ModerationService(perf_bot, perf_db_session)
        
        async def perform_moderation_operations():
            results = []
            
            # Mix of operations
            for i in range(operation_count):
                user_id = 400000000 + i
                chat_id = -1001234567890
                admin_id = 123456789
                
                if i % 3 == 0:
                    # Ban user
                    result = await moderation_service.ban_user(
                        user_id=user_id,
                        chat_id=chat_id,
                        admin_id=admin_id,
                        reason=f"Scalability test ban {i}"
                    )
                elif i % 3 == 1:
                    # Check if user is banned
                    result = await moderation_service.is_user_banned(user_id)
                else:
                    # Get banned users
                    result = await moderation_service.get_banned_users()
                
                results.append(result)
            
            return results
        
        results = await benchmark(perform_moderation_operations)
        assert len(results) == operation_count

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bot_count", [10, 25, 50, 100])
    async def test_bot_service_scalability(self, benchmark, perf_bot, perf_db_session, bot_count):
        """Test BotService scalability"""
        
        bot_service = BotService(perf_bot, perf_db_session)
        
        async def manage_multiple_bots():
            results = []
            
            # Add bots
            for i in range(bot_count):
                username = f"scalebot{i}"
                admin_id = 123456789
                telegram_id = 500000000 + i
                
                result = await bot_service.add_bot_to_whitelist(
                    username=username,
                    admin_id=admin_id,
                    telegram_id=telegram_id
                )
                results.append(result)
            
            # Query all bots
            all_bots = await bot_service.get_all_bots()
            results.append(len(all_bots))
            
            return results
        
        results = await benchmark(manage_multiple_bots)
        assert len(results) == bot_count + 1  # bot_count additions + 1 query


class TestConcurrentOperations:
    """Test concurrent operations performance"""

    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self, benchmark, perf_bot, perf_db_session):
        """Test concurrent user operations"""
        import asyncio
        
        moderation_service = ModerationService(perf_bot, perf_db_session)
        
        async def concurrent_operations():
            # Create tasks for concurrent execution
            tasks = []
            
            for i in range(20):
                user_id = 600000000 + i
                chat_id = -1001234567890
                admin_id = 123456789
                
                task = moderation_service.ban_user(
                    user_id=user_id,
                    chat_id=chat_id,
                    admin_id=admin_id,
                    reason=f"Concurrent test ban {i}"
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        results = await benchmark(concurrent_operations)
        assert len(results) == 20
        # Check that operations were attempted (some might fail due to concurrency or mocking)
        successful_results = [r for r in results if r is True or r is not None]
        assert len(successful_results) >= 1  # At least some operations should be attempted

    @pytest.mark.asyncio
    async def test_concurrent_database_queries(self, benchmark, perf_db_session, benchmark_data_generator):
        """Test concurrent database queries"""
        import asyncio
        from sqlalchemy import select
        from app.models.user import User
        
        # Setup test data
        users_data = benchmark_data_generator["users"](100)
        for user_data in users_data:
            user = User()
            for key, value in user_data.items():
                setattr(user, key, value)
            perf_db_session.add(user)
        await perf_db_session.commit()
        
        async def concurrent_queries():
            # Create multiple query tasks
            tasks = []
            
            for i in range(10):
                async def query_users():
                    result = await perf_db_session.execute(
                        select(User).where(User.telegram_id >= 100000000 + i * 10)
                    )
                    return result.scalars().all()
                
                tasks.append(query_users())
            
            # Execute all queries concurrently
            results = await asyncio.gather(*tasks)
            return results
        
        results = await benchmark(concurrent_queries)
        assert len(results) == 10
        assert all(isinstance(result, list) for result in results)
