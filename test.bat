@echo off
echo 🚀 Starting Enterprise Test Suite...

echo 📦 Building test environment...
docker-compose -f docker-compose.test.yml build

echo 🧪 Running comprehensive test suite...
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

echo 📊 Extracting test coverage...
docker-compose -f docker-compose.test.yml run test-runner pytest --cov=apps --cov-report=term --cov-report=html

echo 🧹 Cleaning up test environment...
docker-compose -f docker-compose.test.yml down -v

echo ✅ Test suite completed!
echo 📈 Coverage report available in htmlcov/index.html
pause