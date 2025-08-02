#!/usr/bin/env python
"""Enterprise-grade test runner without Docker dependencies"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def install_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")
    deps = [
        'pytest==7.4.3',
        'pytest-django==4.7.0', 
        'pytest-cov==4.1.0',
        'pytest-mock==3.12.0',
        'factory-boy==3.3.0',
        'faker==20.1.0'
    ]
    
    for dep in deps:
        subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)

def run_tests():
    """Run comprehensive test suite"""
    print("🧪 Running enterprise test suite...")
    
    # Set environment variables
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    os.environ['PYTHONPATH'] = str(Path.cwd())
    
    # Run tests with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        '-v',
        '--tb=short',
        '--cov=apps',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-fail-under=70',
        'tests/'
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def run_security_tests():
    """Run security-focused tests"""
    print("🔒 Running security tests...")
    cmd = [
        sys.executable, '-m', 'pytest',
        '-v', '-m', 'security',
        'tests/'
    ]
    subprocess.run(cmd)

def run_performance_tests():
    """Run performance tests"""
    print("🏃 Running performance tests...")
    cmd = [
        sys.executable, '-m', 'pytest',
        '-v', '-m', 'performance',
        'tests/'
    ]
    subprocess.run(cmd)

def open_coverage_report():
    """Open coverage report in browser"""
    coverage_file = Path('htmlcov/index.html')
    if coverage_file.exists():
        print("📊 Opening coverage report...")
        webbrowser.open(f'file://{coverage_file.absolute()}')
        return True
    return False

def main():
    """Main test execution"""
    print("🚀 Starting Enterprise Test Suite...")
    
    try:
        # Install dependencies
        install_dependencies()
        
        # Run main test suite
        success = run_tests()
        
        # Run specialized test categories
        run_security_tests()
        run_performance_tests()
        
        # Open coverage report
        if open_coverage_report():
            print("✅ Test suite completed successfully!")
            print("📈 Coverage report opened in browser")
        else:
            print("❌ Coverage report not generated")
            
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())