#!/usr/bin/env python3
"""
Performance testing script for Flame of Styx bot
"""

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return exit code"""
    print(f"🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_benchmark_tests(
    test_pattern: str = "tests/performance/",
    output_format: str = "table",
    save_results: bool = True,
    compare_results: bool = False,
    verbose: bool = False
) -> int:
    """Run performance tests with pytest-benchmark"""
    
    cmd = [
        sys.executable, "-m", "pytest",
        test_pattern,
        "--benchmark-only",
        f"--benchmark-sort=mean",
        f"--benchmark-columns=min,max,mean,stddev,median,iqr,outliers,ops,rounds",
    ]
    
    if output_format:
        cmd.append(f"--benchmark-output-format={output_format}")
    
    if save_results:
        cmd.extend([
            "--benchmark-save=performance_results",
            "--benchmark-save-data"
        ])
    
    if compare_results:
        cmd.append("--benchmark-compare")
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    return run_command(cmd)


def run_specific_benchmarks(category: str) -> int:
    """Run specific category of benchmarks"""
    
    categories = {
        "database": "tests/performance/test_database_performance.py",
        "services": "tests/performance/test_services_performance.py",
        "middleware": "tests/performance/test_middleware_performance.py",
        "utils": "tests/performance/test_utils_performance.py",
    }
    
    if category not in categories:
        print(f"❌ Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return 1
    
    return run_benchmark_tests(
        test_pattern=categories[category],
        verbose=True
    )


def run_scalability_tests() -> int:
    """Run scalability tests with different parameters"""
    
    print("🔄 Running scalability tests...")
    
    scalability_tests = [
        "tests/performance/test_database_performance.py::TestDatabaseScalability",
        "tests/performance/test_services_performance.py::TestServicesScalability",
        "tests/performance/test_middleware_performance.py::TestMiddlewareChainPerformance::test_middleware_scalability",
        "tests/performance/test_utils_performance.py::TestUtilsScalability",
    ]
    
    for test in scalability_tests:
        print(f"\n📊 Running {test}")
        result = run_benchmark_tests(
            test_pattern=test,
            verbose=True
        )
        if result != 0:
            print(f"❌ Scalability test failed: {test}")
            return result
    
    return 0


def run_concurrent_tests() -> int:
    """Run concurrent performance tests"""
    
    print("🔄 Running concurrent performance tests...")
    
    concurrent_tests = [
        "tests/performance/test_services_performance.py::TestConcurrentOperations",
        "tests/performance/test_middleware_performance.py::TestConcurrentMiddleware",
        "tests/performance/test_utils_performance.py::TestConcurrentUtils",
    ]
    
    for test in concurrent_tests:
        print(f"\n⚡ Running {test}")
        result = run_benchmark_tests(
            test_pattern=test,
            verbose=True
        )
        if result != 0:
            print(f"❌ Concurrent test failed: {test}")
            return result
    
    return 0


def generate_performance_report() -> int:
    """Generate performance report"""
    
    print("📊 Generating performance report...")
    
    # Run all benchmarks and save results
    result = run_benchmark_tests(
        save_results=True,
        output_format="json",
        verbose=False
    )
    
    if result != 0:
        print("❌ Failed to generate performance report")
        return result
    
    # Generate HTML report if available
    try:
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance/",
            "--benchmark-only",
            "--benchmark-histogram",
            "--benchmark-save=performance_report",
        ]
        run_command(cmd)
        print("✅ Performance report generated")
    except Exception as e:
        print(f"⚠️  Could not generate HTML report: {e}")
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Performance testing for Flame of Styx bot"
    )
    
    parser.add_argument(
        "command",
        choices=["all", "database", "services", "middleware", "utils", "scalability", "concurrent", "report"],
        help="Type of performance tests to run"
    )
    
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save benchmark results"
    )
    
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare with previous results"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"🎯 Running {args.command} performance tests...")
    print(f"📁 Working directory: {project_root}")
    
    if args.command == "all":
        result = run_benchmark_tests(
            save_results=args.save,
            compare_results=args.compare,
            verbose=args.verbose,
            output_format=args.format
        )
    elif args.command in ["database", "services", "middleware", "utils"]:
        result = run_specific_benchmarks(args.command)
    elif args.command == "scalability":
        result = run_scalability_tests()
    elif args.command == "concurrent":
        result = run_concurrent_tests()
    elif args.command == "report":
        result = generate_performance_report()
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1
    
    if result == 0:
        print("✅ Performance tests completed successfully!")
    else:
        print("❌ Performance tests failed!")
    
    return result


if __name__ == "__main__":
    sys.exit(main())
