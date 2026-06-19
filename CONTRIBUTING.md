# Contributing to Tripwire

Thanks for your interest in contributing!

## Getting Started

```bash
git clone https://github.com/nousresearch/tripwire.git
cd tripwire
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Development Guidelines

- Write tests for new features
- Keep the core dependency-light; heavy deps go in optional extras
- Run `pytest` before submitting a PR
- Follow existing code style (we use ruff)

## Pull Request Process

1. Fork the repo and create a feature branch
2. Add tests for your changes
3. Ensure all tests pass
4. Submit a PR with a clear description

## Reporting Issues

Open a GitHub issue with:
- What you expected to happen
- What actually happened
- Minimal reproduction steps
