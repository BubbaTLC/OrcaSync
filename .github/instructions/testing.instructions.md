---
description: "Instructions for testing OrcaSync"
title: "OrcaSync - Testing Guide"
applyTo: "**/tests/**"
---

# OrcaSync - Testing Guide

## Quick Start
```bash
uv sync --dev                     # Install dependencies
uv run pytest                     # Run all tests
uv run pytest --cov=orcasync     # With coverage
uv run pytest tests/test_config.py::TestClass::test_method  # Specific test
```

## Fixtures (from conftest.py)
- `tmp_config_dir` - Temporary config directory with mocked home
- `mock_orcaslicer_dir` - Mock OrcaSlicer directory structure
- `mock_git_repo` - Mock GitPython repository

## Critical Patterns

### Platform Testing
**MUST** mock `Config.DEFAULT_PATHS` when using temp paths:
```python
mocker.patch('platform.system', return_value='Linux')
mock_default_paths = {'Linux': {'user': tmp_path / ".config" / "OrcaSlicer" / "user"}}
mocker.patch.object(Config, 'DEFAULT_PATHS', mock_default_paths)
```

### Mock GitPython
```python
mock_repo_class = mocker.patch('orcasync.git_ops.Repo')
mock_repo = MagicMock()
mock_repo_class.return_value = mock_repo
mock_repo.is_dirty.return_value = False
```

### CLI Testing
```python
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(main, ['status'])
assert result.exit_code == 0
```

### Multi-Platform
```python
@pytest.mark.parametrize("platform_name,expected", [
    ("Windows", "AppData"), ("Darwin", "Library"), ("Linux", ".config")
])
def test_platforms(mocker, platform_name, expected):
    mocker.patch('platform.system', return_value=platform_name)
```

## Project Rules
1. **NEVER** use subprocess for Git - use GitPython mocks
2. **NEVER** hardcode paths - use Config.DEFAULT_PATHS
3. **ALWAYS** test all platforms (Windows/macOS/Linux)
4. **ALWAYS** use tmp_path for file operations
5. **Mock at correct level** - `orcasync.git_ops.Repo`, not `git.Repo`
6. **Test error paths** - every try/except needs tests

## Coverage Targets
- Overall: >80% | Config: 100% | Git ops: >85% | CLI: >75% | TUI: >70%

## Common Issues
- **"fixture 'mocker' not found"** - Ensure pytest-mock in pyproject.toml dev deps
- **Tests fail in CI** - Check platform mocking and `clear=False` in `mocker.patch.dict()`
- **Coverage low** - Run `pytest --cov=orcasync --cov-report=term-missing`
