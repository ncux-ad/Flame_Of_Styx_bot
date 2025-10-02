"""
Utils and validation performance tests
"""

import pytest
from unittest.mock import MagicMock

from app.utils.security import sanitize_for_logging, sanitize_user_input, safe_format_message
from app.utils.validation import InputValidator


class TestSecurityUtilsPerformance:
    """Security utils performance benchmarks"""

    def test_sanitize_for_logging_performance(self, benchmark):
        """Benchmark sanitize_for_logging function"""
        
        def sanitize_multiple_strings():
            test_strings = [
                "Normal user message",
                "Message with sensitive data: password123",
                "Long message " * 100,
                "Message with special chars: @#$%^&*()",
                "Message with numbers: 123456789",
                "Mixed content: user@example.com, phone: +1234567890",
                "HTML content: <script>alert('xss')</script>",
                "SQL injection: '; DROP TABLE users; --",
                "Unicode content: 🚀 Привет мир! 你好世界",
                "Empty string: ",
            ]
            
            results = []
            for _ in range(50):  # Process each string 50 times
                for test_string in test_strings:
                    result = sanitize_for_logging(test_string)
                    results.append(result)
            
            return results
        
        results = benchmark(sanitize_multiple_strings)
        assert len(results) == 500  # 10 strings * 50 iterations

    def test_sanitize_user_input_performance(self, benchmark):
        """Benchmark sanitize_user_input function"""
        
        def sanitize_user_inputs():
            test_inputs = [
                "Regular user input",
                "<script>alert('malicious')</script>",
                "Very long input " * 200,
                "Input with\nnewlines\nand\ttabs",
                "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
                "Unicode: 🎉🚀💻🔥⭐",
                "Mixed: Hello 世界 🌍",
                "",  # Empty input
                " " * 100,  # Whitespace only
                "A" * 2000,  # Very long input
            ]
            
            results = []
            for _ in range(30):  # Process each input 30 times
                for test_input in test_inputs:
                    result = sanitize_user_input(test_input)
                    results.append(result)
            
            return results
        
        results = benchmark(sanitize_user_inputs)
        assert len(results) == 300  # 10 inputs * 30 iterations

    def test_safe_format_message_performance(self, benchmark):
        """Benchmark safe_format_message function"""
        
        def format_multiple_messages():
            templates = [
                "Hello {name}!",
                "User {user_id} sent message: {message}",
                "Error in {module}: {error}",
                "Processing {count} items from {source}",
                "Status: {status}, Time: {timestamp}, User: {user}",
            ]
            
            test_data = [
                {"name": "John", "user_id": 123, "message": "Hello world"},
                {"module": "auth", "error": "Invalid token"},
                {"count": 100, "source": "database"},
                {"status": "success", "timestamp": "2024-01-01", "user": "admin"},
                {"name": "Alice", "message": "Test message with special chars: @#$"},
            ]
            
            results = []
            for _ in range(40):  # 40 iterations
                for template in templates:
                    for data in test_data:
                        try:
                            result = safe_format_message(template, **data)
                            results.append(result)
                        except:
                            results.append(template)  # Fallback
            
            return results
        
        results = benchmark(format_multiple_messages)
        assert len(results) == 1000  # 5 templates * 5 data sets * 40 iterations


class TestValidationPerformance:
    """Validation performance benchmarks"""

    def test_input_validator_performance(self, benchmark):
        """Benchmark InputValidator performance"""
        
        validator = InputValidator()
        
        def validate_multiple_messages():
            # Create test messages
            test_messages = []
            for i in range(100):
                message = MagicMock()
                message.text = f"Test message {i} with some content"
                message.from_user = MagicMock()
                message.from_user.id = 100000000 + i
                message.from_user.first_name = f"User{i}"
                message.from_user.last_name = "Test"
                message.from_user.username = f"user{i}"
                message.chat = MagicMock()
                message.chat.id = -1001234567890
                message.chat.title = "Test Chat"
                test_messages.append(message)
            
            results = []
            for message in test_messages:
                result = validator.validate_message(message)
                results.append(result)
            
            return results
        
        results = benchmark(validate_multiple_messages)
        assert len(results) == 100

    def test_validation_detailed_performance(self, benchmark):
        """Benchmark detailed validation performance"""
        
        validator = InputValidator()
        
        def validate_complex_messages():
            # Create complex test messages
            test_cases = [
                "Normal message",
                "Message with email: user@example.com",
                "Message with phone: +1234567890",
                "Message with URL: https://example.com",
                "Message with @username mention",
                "Long message " * 50,
                "Message with special chars: !@#$%^&*()",
                "Message with unicode: 🚀 Привет мир!",
                "HTML content: <script>alert('test')</script>",
                "Mixed content with multiple patterns",
            ]
            
            results = []
            for _ in range(20):  # 20 iterations
                for text in test_cases:
                    # Create mock message
                    message = MagicMock()
                    message.text = text
                    message.from_user = MagicMock()
                    message.from_user.id = 123456789
                    message.from_user.first_name = "TestUser"
                    message.from_user.last_name = "Performance"
                    message.from_user.username = "testuser"
                    message.chat = MagicMock()
                    message.chat.id = -1001234567890
                    message.chat.title = "Test Chat"
                    
                    # Validate message
                    validation_result = validator.validate_message(message)
                    results.append(validation_result)
            
            return results
        
        results = benchmark(validate_complex_messages)
        assert len(results) == 200  # 10 texts * 20 iterations


class TestUtilsScalability:
    """Utils scalability tests"""

    @pytest.mark.parametrize("input_size", [100, 500, 1000, 2000])
    def test_sanitization_scalability(self, benchmark, input_size):
        """Test sanitization performance with increasing input sizes"""
        
        def sanitize_large_inputs():
            # Create inputs of varying sizes
            test_input = "Test content with special chars: <script>alert('xss')</script> " * input_size
            
            results = []
            for _ in range(10):  # 10 iterations
                sanitized = sanitize_user_input(test_input)
                logged = sanitize_for_logging(sanitized)
                results.append((sanitized, logged))
            
            return results
        
        results = benchmark(sanitize_large_inputs)
        assert len(results) == 10

    @pytest.mark.parametrize("validation_count", [50, 100, 200, 500])
    def test_validation_scalability(self, benchmark, validation_count):
        """Test validation performance with increasing validation counts"""
        
        validator = InputValidator()
        
        def validate_multiple_inputs():
            results = []
            
            for i in range(validation_count):
                # Create test message
                message = MagicMock()
                message.text = f"Scalability test message {i}"
                message.from_user = MagicMock()
                message.from_user.id = 100000000 + i
                message.from_user.first_name = f"User{i}"
                message.from_user.last_name = "Test"
                message.from_user.username = f"user{i}"
                message.chat = MagicMock()
                message.chat.id = -1001234567890
                message.chat.title = "Test Chat"
                
                # Validate
                result = validator.validate_message(message)
                results.append(result)
            
            return results
        
        results = benchmark(validate_multiple_inputs)
        assert len(results) == validation_count


class TestConcurrentUtils:
    """Test concurrent utils operations"""

    @pytest.mark.asyncio
    async def test_concurrent_sanitization(self, benchmark):
        """Test concurrent sanitization operations"""
        import asyncio
        
        async def concurrent_sanitization():
            # Create concurrent sanitization tasks
            tasks = []
            
            test_strings = [
                f"Concurrent test {i} with content <script>alert({i})</script>"
                for i in range(50)
            ]
            
            async def sanitize_string(text):
                # Simulate async sanitization
                await asyncio.sleep(0.001)  # Small delay to simulate processing
                sanitized = sanitize_user_input(text)
                logged = sanitize_for_logging(sanitized)
                return (sanitized, logged)
            
            for text in test_strings:
                tasks.append(sanitize_string(text))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)
            return results
        
        results = await benchmark(concurrent_sanitization)
        assert len(results) == 50

    @pytest.mark.asyncio
    async def test_concurrent_validation(self, benchmark):
        """Test concurrent validation operations"""
        import asyncio
        
        validator = InputValidator()
        
        async def concurrent_validation():
            # Create concurrent validation tasks
            tasks = []
            
            async def validate_message(i):
                # Create test message
                message = MagicMock()
                message.text = f"Concurrent validation test {i}"
                message.from_user = MagicMock()
                message.from_user.id = 100000000 + i
                message.from_user.first_name = f"User{i}"
                message.from_user.last_name = "Test"
                message.from_user.username = f"user{i}"
                message.chat = MagicMock()
                message.chat.id = -1001234567890
                message.chat.title = "Test Chat"
                
                # Simulate async validation
                await asyncio.sleep(0.001)  # Small delay
                return validator.validate_message(message)
            
            for i in range(30):
                tasks.append(validate_message(i))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)
            return results
        
        results = await benchmark(concurrent_validation)
        assert len(results) == 30
