# Testing Guide

## Enterprise Testing

### Global Test Suite
Run comprehensive tests with full dependencies:

```bash
# Windows
run_enterprise_tests.bat

# Linux/Mac  
python run_enterprise_tests.py
```

### Test Categories
- **Unit**: `pytest -m unit`
- **Integration**: `pytest -m integration` 
- **Security**: `pytest -m security`
- **Performance**: `pytest -m performance`

### Requirements
- Docker Desktop
- PostgreSQL with PostGIS
- Redis
- 60% minimum coverage

### Files
- `tests/test_enterprise_global.py` - Comprehensive test suite
- `docker-compose.test.yml` - Test environment
- `run_enterprise_tests.*` - Test runners

## Local Development
Create `test_local_*.py` files for rapid development testing with SQLite.