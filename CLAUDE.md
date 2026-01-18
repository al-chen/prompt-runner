# Claude Code Guidelines

## Project Overview

Scheduled prompt runner that sends LLM responses via email. Uses GitHub Actions for orchestration.

## Architecture

- **Pluggable providers**: Use abstract base classes (`llm/base.py`, `delivery/base.py`)
- **Public code + private data**: Framework is public, user configs/data are in a separate private repo

## Development

```bash
# Run tests (pip install has issues with hatch, use PYTHONPATH)
PYTHONPATH=src pytest

# Lint
ruff check src/
```

## Code Style

- Python 3.10+ with type hints
- Use dataclasses for data structures
- Keep implementations simple - avoid over-engineering

## Commits

- When completing a task from SPEC.md, mark it as done (`[x]`) in the same commit
- Follow existing commit message style (see `git log`)

## Key Files

- `SPEC.md` - Project specification and task tracking
- `src/prompt_runner/` - Main package
- `examples/` - Example configs (non-personal)
