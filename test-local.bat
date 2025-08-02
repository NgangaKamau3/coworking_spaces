@echo off
echo 🚀 Starting Enterprise Test Suite (Local)...

echo 📦 Installing test dependencies...
pip install pytest pytest-django pytest-cov pytest-mock factory-boy faker

echo 🧪 Running comprehensive test suite with coverage...
pytest -v --tb=short --cov=apps --cov-report=html --cov-report=term-missing --cov-fail-under=80

echo 📊 Generating detailed coverage report...
if exist htmlcov\index.html (
    echo ✅ Coverage report generated successfully!
    echo 📈 Opening coverage report...
    start htmlcov\index.html
) else (
    echo ❌ Coverage report not found. Check test execution.
)

echo 🔍 Running security tests...
pytest -m security -v

echo 🏃 Running performance tests...
pytest -m performance -v

echo ✅ Enterprise test suite completed!
pause