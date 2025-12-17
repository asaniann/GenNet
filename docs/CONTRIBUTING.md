# Contributing to GenNet

Thank you for your interest in contributing to GenNet! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Process

### 1. Create an Issue

Before starting work, create an issue describing:
- What you want to implement
- Why it's needed
- How you plan to implement it

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# Or
git checkout -b fix/your-bug-fix
```

### 3. Make Changes

- Follow coding standards
- Write tests
- Update documentation
- Add type hints

### 4. Commit Changes

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
chore: maintenance tasks
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create a pull request with:
- Clear description
- Related issues
- Test results
- Screenshots (if applicable)

## Coding Standards

### Python

- **Style**: Black (line length 120)
- **Linting**: Flake8
- **Type Checking**: MyPy
- **Format**:
  ```bash
  black services/ shared/
  flake8 services/ shared/
  mypy services/ shared/
  ```

### TypeScript

- **Style**: ESLint + Prettier
- **Format**:
  ```bash
  npm run lint
  npm run format
  ```

## Testing

### Write Tests

- Unit tests for all new functions
- Integration tests for API endpoints
- E2E tests for critical flows

### Run Tests

```bash
# All tests
pytest

# Specific service
pytest services/auth-service/tests/

# With coverage
pytest --cov=services/auth-service --cov-report=html
```

### Test Coverage

- Aim for 80%+ coverage
- Cover edge cases
- Test error conditions

## Documentation

### Code Documentation

- Add docstrings to all public functions
- Document complex algorithms
- Add inline comments for non-obvious code

### API Documentation

- Update API docs for new endpoints
- Add request/response examples
- Document error codes

### User Documentation

- Update user-facing docs
- Add examples
- Update screenshots if UI changes

## Pull Request Process

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Tests passing
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Type hints added
- [ ] Error handling implemented

### Review Process

1. Automated checks must pass
2. At least one approval required
3. Address review comments
4. Maintainer merges PR

## Questions?

- Create an issue
- Ask in team chat
- Check existing documentation

---

**Thank you for contributing!**

