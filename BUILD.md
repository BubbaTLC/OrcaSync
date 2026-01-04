# Building Executables

## Quick Reference

```bash
# Install PyInstaller (first time only)
pip install pyinstaller

# Build executable
pyinstaller --clean orcasync.spec

# Test executable
dist/orcasync --version
dist/orcasync --help
```

## Automated Builds (GitHub Actions)

Executables are automatically built for Linux, Windows, and macOS on:
- Pushes to `main` or `develop` branches
- Pull requests
- Version tags (e.g., `v0.1.0`)

### Creating a Release

1. **Update version in `pyproject.toml`**
2. **Create and push a tag:**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. **GitHub Actions will:**
   - Build executables for all platforms
   - Create a GitHub release
   - Attach binaries to the release

### Workflow Files

- **Build**: `.github/workflows/build.yml` - Creates executables
- **Test**: `.github/workflows/test.yml` - Runs tests on multiple Python versions

## Manual Build Process

### PyInstaller Spec File

The `orcasync.spec` file controls the build:
- Hidden imports for dependencies
- Single-file executable
- Console application
- UPX compression enabled

### Platform-Specific Builds

**Linux:**
```bash
pyinstaller orcasync.spec
# Output: dist/orcasync
```

**Windows:**
```bash
pyinstaller orcasync.spec
# Output: dist/orcasync.exe
```

**macOS:**
```bash
pyinstaller orcasync.spec
# Output: dist/orcasync
```

### Testing Executables

```bash
# Version check
dist/orcasync --version

# Help
dist/orcasync --help

# Dry run
dist/orcasync status
```

## Troubleshooting

### Missing Modules
Add to `hiddenimports` in `orcasync.spec`:
```python
hiddenimports=[
    'click',
    'rich',
    'yaml',
    'git',
    # Add more as needed
],
```

### Large File Size
- Enable UPX compression (already enabled)
- Exclude unnecessary modules in spec file
- Consider using `--exclude-module` for unused dependencies

### Runtime Errors
Check that all data files and dependencies are included:
```bash
pyinstaller --log-level DEBUG orcasync.spec
```
