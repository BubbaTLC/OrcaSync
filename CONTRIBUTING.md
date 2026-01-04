# Contributing to OrcaSync

Thank you for your interest in contributing to OrcaSync! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- [UV](https://github.com/astral-sh/uv) - Fast Python package installer (recommended)

### Local Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/orcasync.git
   cd orcasync
   ```

2. **Install UV (if not already installed):**
   ```bash
   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Create a virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```

4. **Verify installation:**
   ```bash
   orcasync --version
   ```

## Code Structure

```
orcasync/
├── orcasync/
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # Command-line interface (Click)
│   ├── config.py         # Configuration management
│   └── git_ops.py        # Git operations (GitPython)
├── tests/                # Test suite (future)
├── pyproject.toml        # Project metadata and dependencies
├── README.md             # User documentation
├── PROFILES.md           # Profile configuration guide
├── main.md               # Technical documentation
└── CONTRIBUTING.md       # This file
```

## Development Guidelines

### Code Style

- **Python Style**: Follow PEP 8
- **Formatting**: Use `black` for code formatting
- **Type Hints**: Add type hints to function signatures
- **Docstrings**: Use Google-style docstrings

Example:
```python
def sync_files(self, source_paths: List[Path], target_subdir: str = "profiles") -> List[Path]:
    """Copy files from source paths to repository.
    
    Args:
        source_paths: List of source directories to sync
        target_subdir: Subdirectory within repo to sync to
        
    Returns:
        List of files that were copied
    """
```

### Running Code Quality Tools

```bash
# Format code
black orcasync/

# Check style
flake8 orcasync/

# Type checking
mypy orcasync/
```

### Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=orcasync
```

## Building Executables

### Local Build with PyInstaller

Build a standalone executable for your platform:

```bash
# Install PyInstaller using UV
uv pip install pyinstaller

# Build using spec file (recommended)
pyinstaller orcasync.spec

# Or build directly
pyinstaller --onefile --name orcasync orcasync/cli.py

# Executable will be in dist/
./dist/orcasync --version
```

### Multi-Platform Builds with GitHub Actions

The project uses GitHub Actions to automatically build executables for Linux, Windows, and macOS:

- **Workflow**: `.github/workflows/build.yml`
- **Triggers**: Push to main/develop, pull requests, tags (v*)
- **Outputs**: Artifacts uploaded for each platform

**To create a release:**

1. Create and push a version tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. GitHub Actions will automatically:
   - Build executables for all platforms
   - Run tests
   - Create a GitHub release with binaries attached

**Manual workflow trigger:**
You can also trigger builds manually from the Actions tab in GitHub.

## Making Changes

### Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
   ```bash
   # Test CLI commands manually
   orcasync init
   orcasync push
   orcasync status
   
   # Run automated tests
   pytest
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add feature: description of feature"
   ```

5. **Push and create pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests when relevant

Examples:
```
Add support for custom commit messages
Fix credential handling on macOS
Update documentation for profile configuration
```

## Areas for Contribution

### High Priority

- [ ] **Test Suite**: Unit and integration tests
- [ ] **Conflict Resolution UI**: Better handling of merge conflicts
- [ ] **GUI Application**: Desktop application for non-CLI users
- [ ] **Documentation**: Improve and expand documentation
- [ ] **Platform Testing**: Test on various OS configurations

### Feature Ideas

- [ ] File watchers for auto-sync
- [ ] Selective sync (include/exclude patterns)
- [ ] Profile import/export
- [ ] Configuration validation
- [ ] Dry-run mode for commands
- [ ] Backup/restore functionality
- [ ] Interactive configuration wizard
- [ ] Profile diff viewer

### Bug Fixes

Check the [Issues](https://github.com/yourusername/orcasync/issues) page for reported bugs.

## Documentation Contributions

Documentation is just as important as code! Areas that need documentation:

1. **User Guides**: Step-by-step tutorials for common workflows
2. **API Documentation**: Detailed module/function documentation
3. **Troubleshooting**: Common issues and solutions
4. **Examples**: Real-world configuration examples
5. **Video Tutorials**: Screen recordings of OrcaSync in action

## Code Review Process

1. All submissions require code review
2. Maintainers will review your pull request
3. Address any feedback or requested changes
4. Once approved, maintainers will merge your PR

## Questions or Problems?

- **Questions**: Open a [Discussion](https://github.com/yourusername/orcasync/discussions)
- **Bug Reports**: Open an [Issue](https://github.com/yourusername/orcasync/issues)
- **Feature Requests**: Open an [Issue](https://github.com/yourusername/orcasync/issues) with "enhancement" label

## License

By contributing to OrcaSync, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in the project README and release notes. Thank you for helping make OrcaSync better!
