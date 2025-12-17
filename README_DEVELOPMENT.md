# Development Environment Setup

## Python Version Requirements

**Important**: This project uses **Python 3.11** for all services.

### Local Development

For local development, you have two options:

1. **Use Python 3.11** (Recommended)
   - Install Python 3.11 and create a virtual environment:
     ```bash
     python3.11 -m venv venv
     source venv/bin/activate
     ```

2. **Use Python 3.13 with workarounds**
   - If you must use Python 3.13, upgrade pydantic first:
     ```bash
     pip install --upgrade "pydantic>=2.10.0" "pydantic-core>=2.20.0"
     ```
   - Note: Some services pin older pydantic versions that may not build on Python 3.13

### Docker Development

All Docker services use Python 3.11, so Docker builds will work regardless of your local Python version.

## Installing Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install service dependencies (may require Python 3.11)
find services -name "requirements.txt" -exec pip install -r {} \;
```

## Troubleshooting

### pydantic-core build errors on Python 3.13

If you see errors like:
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
```

This is a Python 3.13 compatibility issue. Solutions:
1. Use Python 3.11 for local development
2. Upgrade pydantic: `pip install --upgrade "pydantic>=2.10.0"`
3. Use Docker for development instead

