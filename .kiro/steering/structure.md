# Project Structure

## Directory Layout

```
owls-archive-q4/
├── src/q4/                 # Main package source code
│   ├── __init__.py         # Package exports
│   ├── cli.py              # Command-line interface
│   └── operator.py         # Core mathematical operations
├── tests/                  # Test suite
│   └── test_operator.py    # Unit tests for operators
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # Basic project documentation
├── TASKS.md                # Development tasks and roadmap
└── LICENSE                 # Project license
```

## Module Organization

### `q4.operator`

Core mathematical functions for four-quadrant analysis:

- `learn_projectors_linear()`: Learns projection matrices from data
- `four_quadrants()`: Applies quadrant decomposition
- `energy_split()`: Computes energy distribution metrics

### `q4.cli`

Command-line interface providing:

- File I/O handling (CSV/Parquet)
- Batch processing workflow
- Structured output generation (JSON manifests, CSV results)

## Output Structure

The CLI generates standardized outputs:

- `Q_keep.csv`: Signal data (kept quadrants)
- `Q_discard.csv`: Noise data (discarded quadrants)
- `Q_study.json`: Analysis metadata and statistics
- `er.json`: Energy split metrics and row counts
- `MANIFEST.json`: Input/output file mapping

## Naming Conventions

- Package name: `q4` (short, memorable)
- Functions: snake_case with descriptive names
- Variables: Mathematical notation preserved (e.g., `Ps`, `Pv` for projectors)
- Output files: Uppercase for important results (`Q_keep`, `MANIFEST`)
