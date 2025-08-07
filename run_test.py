#!/usr/bin/env python
"""
Test runner script for the transaction system

Usage:
    python run_tests.py           # Run all tests
    python run_tests.py --unit    # Run only unit tests
    python run_tests.py --integration  # Run only integration tests
    python run_tests.py --coverage     # Run with coverage report
    python run_tests.py --fast         # Run fast tests only
"""

import argparse
import subprocess
import sys


def run_command(command):
    """Run a command and return the exit code"""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Run tests for transaction system')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--fast', action='store_true', help='Run fast tests only (exclude slow tests)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Base pytest command
    cmd = ['python', '-m', 'pytest']

    # Add verbosity
    if args.verbose:
        cmd.append('-v')

    # Add markers for test selection
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.fast:
        cmd.extend(['-m', 'not slow'])

    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            '--cov=transactions',
            '--cov=reports',
            '--cov=utils',
            '--cov-report=html',
            '--cov-report=term-missing'
        ])

    # Run the tests
    exit_code = run_command(cmd)

    if exit_code == 0:
        print("\n✅ All tests passed!")

        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(exit_code)


if __name__ == '__main__':
    main()