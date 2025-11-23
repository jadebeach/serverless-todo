# Serverless Todo Application - Test Suite

This directory contains comprehensive unit and integration tests for the Serverless Todo application.

## Test Coverage Overview

### Backend (Python/Lambda)
- **Helper Modules**: `dynamodb_helper.py`, `auth_helper.py`
- **Lambda Functions**: `create_todo`, `get_todos`, `update_todo`, `delete_todo`
- **Coverage Goal**: 80%+

### Frontend (React)
- **Components**: `App`, `TodoForm`, `TodoList`, `TodoItem`
- **Test Types**: Unit tests, component rendering, user interactions

## Directory Structure

```
tests/
├── unit/
│   ├── functions/
│   │   ├── create_todo/
│   │   │   └── test_app.py
│   │   ├── get_todos/
│   │   │   └── test_app.py
│   │   ├── update_todo/
│   │   │   └── test_app.py
│   │   └── delete_todo/
│   │       └── test_app.py
│   └── layers/
│       ├── test_dynamodb_helper.py
│       └── test_auth_helper.py
└── integration/
    └── (future integration tests)
```

## Running Backend Tests

### Prerequisites

1. Install Python dependencies:
```bash
cd aws/serverless-todo
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=functions --cov=layers --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Test Files

```bash
# Test a specific Lambda function
pytest tests/unit/functions/create_todo/test_app.py

# Test helper modules
pytest tests/unit/layers/test_dynamodb_helper.py

# Run tests matching a pattern
pytest -k "test_create_todo"
```

### Run Tests by Category

```bash
# Run only validation tests
pytest -k "validation"

# Run only success path tests
pytest -k "success"

# Run only error handling tests
pytest -k "error"
```

## Running Frontend Tests

### Prerequisites

1. Install Node.js dependencies:
```bash
cd aws/serverless-todo/frontend
npm install
```

### Run All Tests

```bash
# Run all frontend tests
npm test

# Run tests in watch mode (interactive)
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run tests without watch mode
npm test -- --watchAll=false
```

### Run Specific Test Files

```bash
# Test a specific component
npm test -- TodoForm.test.js

# Test all component tests
npm test -- --testPathPattern=components
```

## Test Categories Explained

### Backend Tests

#### 1. Input Validation Tests
- Test missing required fields
- Test empty values
- Test invalid data types
- Test invalid enum values (priority, status)

#### 2. Success Path Tests
- Test successful operations with valid data
- Test optional fields
- Test all enum values
- Test data persistence

#### 3. Error Handling Tests
- Test DynamoDB errors
- Test JSON parsing errors
- Test network errors
- Test exception handling

#### 4. Edge Cases
- Test unicode characters
- Test very long strings
- Test special characters
- Test concurrent operations

### Frontend Tests

#### 1. Component Rendering Tests
- Test component structure
- Test default props
- Test conditional rendering

#### 2. User Interaction Tests
- Test form submissions
- Test button clicks
- Test input changes
- Test validation

#### 3. State Management Tests
- Test state updates
- Test callback functions
- Test loading states
- Test error states

## Coverage Goals

| Module | Current Coverage | Goal |
|--------|-----------------|------|
| create_todo | 100% | 80% |
| get_todos | 100% | 80% |
| update_todo | 100% | 80% |
| delete_todo | 100% | 80% |
| dynamodb_helper | 100% | 80% |
| auth_helper | 100% | 80% |
| Frontend Components | ~80% | 70% |

## Test Fixtures and Mocks

### Backend Fixtures
- `mock_dynamodb_table`: Creates a mocked DynamoDB table using moto
- `sample_todo`: Inserts sample todo data for testing
- `sample_todos`: Multiple todo items for list operations

### Frontend Mocks
- Amplify authentication mocks
- Fetch API mocks
- User interaction mocks via `@testing-library/user-event`

## Continuous Integration

Tests run automatically on:
- Pull request creation
- Push to main branch
- Scheduled nightly runs

CI Pipeline checks:
- ✅ All tests pass
- ✅ Coverage threshold met (80%)
- ✅ No linting errors
- ✅ Type checking passes

## Best Practices

1. **Write tests first**: Follow TDD when adding new features
2. **Test behavior, not implementation**: Focus on what the code does
3. **Use descriptive test names**: Test names should explain what is being tested
4. **Keep tests independent**: Each test should run in isolation
5. **Mock external dependencies**: Don't rely on actual AWS services in unit tests
6. **Test edge cases**: Don't just test the happy path

## Common Issues and Solutions

### Issue: Tests timing out
**Solution**: Increase pytest timeout or check for infinite loops

### Issue: DynamoDB mock not working
**Solution**: Ensure `@mock_dynamodb` decorator is applied to the test

### Issue: Frontend tests failing
**Solution**: Check that all mocks are properly set up in `beforeEach`

### Issue: Coverage not reaching 80%
**Solution**: Identify uncovered lines with `pytest --cov-report=term-missing`

## Adding New Tests

When adding a new feature:

1. Create test file in appropriate directory
2. Import necessary fixtures and mocks
3. Write test cases covering:
   - Success scenarios
   - Validation errors
   - Error handling
   - Edge cases
4. Run tests and ensure they pass
5. Check coverage and add tests if needed

## Contact

For questions about the test suite, contact the development team or open an issue in the repository.
