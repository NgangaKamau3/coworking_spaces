@echo off
echo [ENTERPRISE] Global Test Suite with Full Dependencies

echo [CHECK] Checking Docker availability...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not available. Install Docker Desktop to run global tests.
    pause
    exit /b 1
)

echo [DOCKER] Running comprehensive test suite...
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

echo [UNIT] Running unit tests...
docker-compose -f docker-compose.test.yml run test-runner pytest -m unit -v --tb=short --cov=apps --cov-report=term

echo [INTEGRATION] Running integration tests...
docker-compose -f docker-compose.test.yml run test-runner pytest -m integration -v --tb=short --cov=apps --cov-report=term

echo [SECURITY] Running security tests...
docker-compose -f docker-compose.test.yml run test-runner pytest -m security -v --tb=short --cov=apps --cov-report=term

echo [PERFORMANCE] Running performance tests...
docker-compose -f docker-compose.test.yml run test-runner pytest -m performance -v --tb=short --cov=apps --cov-report=term

echo [CLEANUP] Cleaning up test environment...
docker-compose -f docker-compose.test.yml down -v

echo [SUCCESS] Enterprise global test suite completed!
echo [COVERAGE] Coverage reports generated in Docker containers
pause