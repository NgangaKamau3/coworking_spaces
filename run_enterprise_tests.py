#!/usr/bin/env python
"""Enterprise global test runner with Docker support"""

import os
import sys
import subprocess
from pathlib import Path

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def run_docker_tests():
    """Run tests in Docker environment"""
    print("[DOCKER] Running enterprise tests with full dependencies...")
    
    # Build and run comprehensive test suite
    cmd = [
        'docker-compose', '-f', 'docker-compose.test.yml', 
        'up', '--build', '--abort-on-container-exit'
    ]
    
    result = subprocess.run(cmd)
    
    # Extract coverage report
    print("[DOCKER] Extracting coverage report...")
    extract_cmd = [
        'docker-compose', '-f', 'docker-compose.test.yml',
        'run', 'test-runner',
        'cp', '/app/htmlcov', '/app/coverage_output'
    ]
    
    subprocess.run(extract_cmd, capture_output=True)
    
    # Cleanup
    cleanup_cmd = [
        'docker-compose', '-f', 'docker-compose.test.yml',
        'down', '-v'
    ]
    subprocess.run(cleanup_cmd)
    
    return result.returncode

def run_categorized_tests():
    """Run categorized test suites"""
    print("[CATEGORIES] Running categorized test suites...")
    
    categories = [
        ('unit', 'Unit Tests'),
        ('integration', 'Integration Tests'), 
        ('security', 'Security Tests'),
        ('performance', 'Performance Tests')
    ]
    
    for category, description in categories:
        print(f"[{category.upper()}] Running {description}...")
        
        cmd = [
            'docker-compose', '-f', 'docker-compose.test.yml',
            'run', 'test-runner',
            'pytest', '-m', category, '-v', '--tb=short',
            '--cov=apps', '--cov-report=term'
        ]
        
        subprocess.run(cmd)

def main():
    """Main test execution"""
    print("[ENTERPRISE] Global Test Suite with Full Dependencies")
    
    if not check_docker():
        print("[ERROR] Docker not available. Install Docker Desktop to run global tests.")
        return 1
    
    try:
        # Run comprehensive test suite
        result = run_docker_tests()
        
        # Run categorized tests
        run_categorized_tests()
        
        if result == 0:
            print("[SUCCESS] Enterprise global test suite completed successfully!")
            print("[COVERAGE] Coverage report available in Docker volume")
        else:
            print("[FAILED] Some tests failed. Check output above.")
            
        return result
        
    except KeyboardInterrupt:
        print("[INTERRUPTED] Test execution interrupted")
        return 1
    except Exception as e:
        print(f"[ERROR] Test execution failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())