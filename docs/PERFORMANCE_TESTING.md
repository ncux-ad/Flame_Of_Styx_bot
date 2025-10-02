# 🚀 Performance Testing Guide

Comprehensive guide for performance testing the Flame of Styx bot.

## 📋 Overview

This guide covers performance testing using `pytest-benchmark` to measure and optimize the bot's performance across different components.

## 🛠️ Setup

### Prerequisites

```bash
# Install performance testing dependencies
pip install pytest-benchmark

# Optional: Install additional tools for advanced reporting
pip install pytest-benchmark[histogram]
```

### Configuration

Performance tests are configured in `pytest-benchmark.ini`:

- **Minimum rounds**: 5 (for statistical significance)
- **Maximum time**: 10 seconds per benchmark
- **Timer**: `time.perf_counter` (high precision)
- **Garbage collection**: Disabled during benchmarks
- **Warmup**: 2 iterations before actual measurement

## 📊 Test Categories

### 1. Database Performance (`test_database_performance.py`)

Tests database operations performance:

- **CRUD Operations**: User, Channel, Bot creation/updates
- **Bulk Operations**: Mass insertions and queries
- **Complex Queries**: Joins and aggregations
- **Scalability**: Performance with increasing data sizes

**Key Metrics**:
- Insert rate (operations/second)
- Query response time
- Memory usage during bulk operations

### 2. Services Performance (`test_services_performance.py`)

Tests business logic services:

- **ModerationService**: Ban/unban operations
- **BotService**: Whitelist management
- **ChannelService**: Channel operations
- **ProfileService**: Profile analysis

**Key Metrics**:
- Service method execution time
- Concurrent operation handling
- Resource utilization

### 3. Middleware Performance (`test_middleware_performance.py`)

Tests middleware chain performance:

- **DIMiddleware**: Dependency injection overhead
- **RateLimitMiddleware**: Rate limiting performance
- **ValidationMiddleware**: Input validation speed
- **Chain Processing**: Full middleware stack

**Key Metrics**:
- Request processing time
- Middleware overhead
- Chain latency

### 4. Utils Performance (`test_utils_performance.py`)

Tests utility functions:

- **Security Utils**: Sanitization functions
- **Validation**: Input validation performance
- **Pattern Matching**: Regex operations

**Key Metrics**:
- Function execution time
- Memory allocation
- CPU usage

## 🎯 Running Performance Tests

### Quick Start

```bash
# Run all performance tests
python scripts/run_performance_tests.py all

# Run specific category
python scripts/run_performance_tests.py database
python scripts/run_performance_tests.py services
python scripts/run_performance_tests.py middleware
python scripts/run_performance_tests.py utils
```

### Advanced Usage

```bash
# Run with result saving
python scripts/run_performance_tests.py all --save

# Compare with previous results
python scripts/run_performance_tests.py all --compare

# Generate detailed report
python scripts/run_performance_tests.py report

# Run scalability tests
python scripts/run_performance_tests.py scalability

# Run concurrent tests
python scripts/run_performance_tests.py concurrent
```

### Direct pytest Commands

```bash
# Run all benchmarks
pytest tests/performance/ --benchmark-only

# Run with specific output format
pytest tests/performance/ --benchmark-only --benchmark-json=results.json

# Run with histogram generation
pytest tests/performance/ --benchmark-only --benchmark-histogram

# Compare with baseline
pytest tests/performance/ --benchmark-only --benchmark-compare=0001
```

## 📈 Interpreting Results

### Benchmark Output

```
Name (time in ms)                    Min      Max     Mean   StdDev   Median     IQR   Outliers     OPS   Rounds
test_user_crud_performance        1.234    2.456    1.567    0.123    1.500   0.200      2;0   638.14      100
```

**Key Columns**:
- **Min/Max**: Fastest/slowest execution times
- **Mean**: Average execution time
- **StdDev**: Standard deviation (consistency indicator)
- **Median**: Middle value (less affected by outliers)
- **IQR**: Interquartile range (spread indicator)
- **Outliers**: Number of outlier measurements
- **OPS**: Operations per second
- **Rounds**: Number of test iterations

### Performance Targets

#### Database Operations
- **Simple queries**: < 10ms
- **Complex queries**: < 50ms
- **Bulk inserts**: > 100 ops/sec
- **CRUD operations**: < 5ms

#### Services
- **Moderation operations**: < 20ms
- **Profile analysis**: < 100ms
- **Channel operations**: < 15ms
- **Bot management**: < 10ms

#### Middleware
- **DI overhead**: < 1ms
- **Rate limiting**: < 2ms
- **Validation**: < 5ms
- **Full chain**: < 10ms

#### Utils
- **Sanitization**: < 1ms
- **Pattern matching**: < 5ms
- **Validation**: < 3ms

## 🔍 Scalability Testing

### Database Scalability

Tests performance with increasing data sizes:

```python
@pytest.mark.parametrize("user_count", [100, 500, 1000, 2000])
async def test_user_scalability(self, benchmark, user_count):
    # Test scales with user count
```

### Service Scalability

Tests service performance under load:

```python
@pytest.mark.parametrize("operation_count", [10, 50, 100, 200])
async def test_moderation_service_scalability(self, benchmark, operation_count):
    # Test scales with operation count
```

### Expected Scaling

- **Linear scaling**: Performance degrades proportionally
- **Sub-linear scaling**: Performance degrades less than proportionally (good)
- **Super-linear scaling**: Performance degrades more than proportionally (bad)

## ⚡ Concurrent Testing

### Concurrent Operations

Tests performance under concurrent load:

```python
async def test_concurrent_user_operations(self, benchmark):
    # Multiple operations running simultaneously
    tasks = [operation() for _ in range(20)]
    results = await asyncio.gather(*tasks)
```

### Concurrency Metrics

- **Throughput**: Total operations per second
- **Latency**: Individual operation time
- **Resource contention**: Database locks, memory usage
- **Error rate**: Failed operations under load

## 📊 Performance Monitoring

### Continuous Monitoring

1. **Baseline establishment**: Run initial benchmarks
2. **Regular testing**: Weekly performance runs
3. **Regression detection**: Compare with baselines
4. **Performance alerts**: Automated notifications

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Performance Tests
  run: |
    python scripts/run_performance_tests.py all --save
    python scripts/run_performance_tests.py all --compare
```

### Performance Regression

Detect performance regressions:

```bash
# Fail if performance degrades by more than 10%
pytest tests/performance/ --benchmark-only --benchmark-compare-fail=mean:10%
```

## 🛠️ Optimization Strategies

### Database Optimization

1. **Indexing**: Add indexes for frequently queried columns
2. **Query optimization**: Use efficient queries
3. **Connection pooling**: Reuse database connections
4. **Batch operations**: Group multiple operations

### Service Optimization

1. **Caching**: Cache frequently accessed data
2. **Async operations**: Use async/await properly
3. **Resource pooling**: Reuse expensive resources
4. **Algorithm optimization**: Use efficient algorithms

### Middleware Optimization

1. **Early returns**: Exit middleware chain early when possible
2. **Lazy loading**: Load resources only when needed
3. **Caching**: Cache validation results
4. **Parallel processing**: Process independent operations concurrently

## 📝 Best Practices

### Writing Performance Tests

1. **Isolated tests**: Each test should be independent
2. **Realistic data**: Use representative test data
3. **Proper setup/teardown**: Clean state between tests
4. **Statistical significance**: Run enough iterations
5. **Consistent environment**: Control external factors

### Test Data Management

1. **Deterministic data**: Use consistent test data
2. **Appropriate scale**: Test with realistic data sizes
3. **Data cleanup**: Clean up test data after tests
4. **Memory management**: Avoid memory leaks in tests

### Result Analysis

1. **Trend analysis**: Look for performance trends over time
2. **Outlier investigation**: Investigate unusual results
3. **Correlation analysis**: Correlate performance with code changes
4. **Bottleneck identification**: Find performance bottlenecks

## 🚨 Troubleshooting

### Common Issues

1. **Inconsistent results**: Check for external factors
2. **Memory leaks**: Monitor memory usage during tests
3. **Database locks**: Ensure proper transaction handling
4. **Resource contention**: Check for resource conflicts

### Debugging Performance Issues

1. **Profiling**: Use Python profilers (cProfile, py-spy)
2. **Logging**: Add performance logging
3. **Monitoring**: Use system monitoring tools
4. **Isolation**: Test components in isolation

## 📚 Additional Resources

- [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html)
- [Async Python Performance](https://docs.python.org/3/library/asyncio-dev.html#asyncio-dev)

---

*Last updated: January 2025*
