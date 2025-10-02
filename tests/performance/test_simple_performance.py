"""
Simple performance tests that work correctly with pytest-benchmark
"""

import pytest
from unittest.mock import MagicMock

from app.utils.security import sanitize_for_logging, sanitize_user_input, safe_format_message
from app.utils.validation import InputValidator


class TestSimplePerformance:
    """Simple performance benchmarks"""

    def test_sanitize_for_logging_benchmark(self, benchmark):
        """Benchmark sanitize_for_logging function"""
        
        test_strings = [
            "Normal user message",
            "Message with sensitive data: password123",
            "Long message " * 50,
            "Message with special chars: @#$%^&*()",
            "Message with numbers: 123456789",
            "Mixed content: user@example.com, phone: +1234567890",
            "HTML content: <script>alert('xss')</script>",
            "SQL injection: '; DROP TABLE users; --",
            "Unicode content: 🚀 Привет мир! 你好世界",
            "Empty string: ",
        ]
        
        def sanitize_strings():
            results = []
            for test_string in test_strings:
                result = sanitize_for_logging(test_string)
                results.append(result)
            return results
        
        results = benchmark(sanitize_strings)
        assert len(results) == 10

    def test_sanitize_user_input_benchmark(self, benchmark):
        """Benchmark sanitize_user_input function"""
        
        test_inputs = [
            "Regular user input",
            "<script>alert('malicious')</script>",
            "Very long input " * 100,
            "Input with\nnewlines\nand\ttabs",
            "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "Unicode: 🎉🚀💻🔥⭐",
            "Mixed: Hello 世界 🌍",
            "",  # Empty input
            " " * 50,  # Whitespace only
            "A" * 1000,  # Long input
        ]
        
        def sanitize_inputs():
            results = []
            for test_input in test_inputs:
                result = sanitize_user_input(test_input)
                results.append(result)
            return results
        
        results = benchmark(sanitize_inputs)
        assert len(results) == 10

    def test_safe_format_message_benchmark(self, benchmark):
        """Benchmark safe_format_message function"""
        
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
        
        def format_messages():
            results = []
            for template in templates:
                for data in test_data:
                    try:
                        result = safe_format_message(template, **data)
                        results.append(result)
                    except:
                        results.append(template)  # Fallback
            return results
        
        results = benchmark(format_messages)
        assert len(results) == 25  # 5 templates * 5 data sets

    def test_input_validator_benchmark(self, benchmark):
        """Benchmark InputValidator performance"""
        
        validator = InputValidator()
        
        def validate_messages():
            results = []
            for i in range(50):
                # Create test message
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
                
                result = validator.validate_message(message)
                results.append(result)
            
            return results
        
        results = benchmark(validate_messages)
        assert len(results) == 50


class TestScalabilityBenchmarks:
    """Scalability benchmarks with different input sizes"""

    @pytest.mark.parametrize("input_size", [10, 50, 100, 200])
    def test_sanitization_scalability(self, benchmark, input_size):
        """Test sanitization performance with increasing input sizes"""
        
        def sanitize_multiple():
            test_input = "Test content with special chars: <script>alert('xss')</script> "
            results = []
            
            for i in range(input_size):
                sanitized = sanitize_user_input(test_input + str(i))
                logged = sanitize_for_logging(sanitized)
                results.append((sanitized, logged))
            
            return results
        
        results = benchmark(sanitize_multiple)
        assert len(results) == input_size

    @pytest.mark.parametrize("validation_count", [10, 25, 50, 100])
    def test_validation_scalability(self, benchmark, validation_count):
        """Test validation performance with increasing validation counts"""
        
        validator = InputValidator()
        
        def validate_multiple():
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
        
        results = benchmark(validate_multiple)
        assert len(results) == validation_count


class TestComplexOperations:
    """Complex operations benchmarks"""

    def test_complex_validation_benchmark(self, benchmark):
        """Benchmark complex validation scenarios"""
        
        validator = InputValidator()
        
        test_cases = [
            "Normal message",
            "Message with email: user@example.com",
            "Message with phone: +1234567890",
            "Message with URL: https://example.com",
            "Message with @username mention",
            "Long message " * 20,
            "Message with special chars: !@#$%^&*()",
            "Message with unicode: 🚀 Привет мир!",
            "HTML content: <script>alert('test')</script>",
            "Mixed content with multiple patterns",
        ]
        
        def validate_complex():
            results = []
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
        
        results = benchmark(validate_complex)
        assert len(results) == 10

    def test_combined_operations_benchmark(self, benchmark):
        """Benchmark combined security and validation operations"""
        
        validator = InputValidator()
        
        def combined_operations():
            results = []
            
            for i in range(20):
                # Input text
                text = f"Test message {i} with <script>alert('xss')</script> content"
                
                # 1. Sanitize for logging
                logged = sanitize_for_logging(text)
                
                # 2. Sanitize user input
                sanitized = sanitize_user_input(text)
                
                # 3. Format message safely
                formatted = safe_format_message("User {user_id}: {msg}", user_id=i, msg=sanitized)
                
                # 4. Create and validate message
                message = MagicMock()
                message.text = formatted
                message.from_user = MagicMock()
                message.from_user.id = 100000000 + i
                message.from_user.first_name = f"User{i}"
                message.from_user.last_name = "Test"
                message.from_user.username = f"user{i}"
                message.chat = MagicMock()
                message.chat.id = -1001234567890
                message.chat.title = "Test Chat"
                
                validation_result = validator.validate_message(message)
                
                results.append({
                    'logged': logged,
                    'sanitized': sanitized,
                    'formatted': formatted,
                    'validation': validation_result
                })
            
            return results
        
        results = benchmark(combined_operations)
        assert len(results) == 20
