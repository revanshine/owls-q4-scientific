# Technology Stack

## Build System

- **Package Manager**: Python packaging with `pyproject.toml`
- **Python Version**: Requires Python >=3.10
- **Entry Point**: CLI accessible via `q4` command after installation

## Core Dependencies

- **numpy**: Numerical computing and linear algebra operations
- **pandas**: Data manipulation and I/O (CSV/Parquet support)
- **scipy**: Scientific computing utilities
- **pyarrow**: Parquet file format support

## Common Commands

```bash
# Install the package in development mode
pip install -e .

# Run the CLI tool
q4 --input data.csv --out results/

# Run tests
python -m pytest tests/

# Install dependencies
pip install numpy pandas scipy pyarrow
```

## Code Style Conventions

- Use type hints for function parameters and return values
- Prefer numpy arrays over lists for numerical data
- Use pathlib.Path for file operations
- Follow PEP 8 naming conventions
- Keep functions focused and modular

## Testing Framework

- Uses pytest for testing
- Tests should verify numerical accuracy within tolerance ranges
- Random number generators should use fixed seeds for reproducibility
