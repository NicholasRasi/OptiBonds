# Tests

This directory contains comprehensive tests for the project.

## Test Structure

- `test_utils.py` - Tests for utility functions in `bond_calc/utils.py`
- `test_strategies.py` - Tests for ladder building strategies in `bond_calc/strategies.py`
- `test_ladder.py` - Tests for ladder building
- `test_model.py` - Test for the models
- `conftest.py` - Shared pytest fixtures and configuration

## Running Tests

### Install Test Dependencies

First, install the test dependencies using Poetry:

```bash
poetry install --with dev
```

### Run All Tests

```bash
poetry run pytest
```

### Run Tests with Coverage

```bash
poetry run pytest --cov=bond_calc --cov-report=html
```

This will generate an HTML coverage report in the `htmlcov/` directory.

### Run Specific Test Files

```bash
# Run only utils tests
poetry run pytest tests/test_utils.py

# Run only strategies tests
poetry run pytest tests/test_strategies.py
```

### Run Tests in Verbose Mode

```bash
poetry run pytest -v
```

### Run Tests and Show Print Statements

```bash
poetry run pytest -s
```