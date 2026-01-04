# Changelog

All notable changes to OrcaSync will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Automated test suite
- GUI application
- File watchers for auto-sync
- Selective file sync (include/exclude patterns)
- Standalone executables for all platforms

## [0.1.0] - 2024-01-XX

### Added
- Initial release of OrcaSync CLI
- Multi-platform support (Windows, macOS, Linux, WSL)
- Git-based profile synchronization
- Profile-based configuration system
- Platform-specific path handling
- Automatic OrcaSlicer installation detection
- Rich terminal UI with colors and formatted tables
- Commands:
  - `init` - Interactive configuration wizard
  - `push` - Upload profiles to remote repository
  - `pull` - Download profiles from remote repository
  - `sync` - Bidirectional sync (pull then push)
  - `status` - Show detailed status and configuration
  - `config-path` - Display configuration file location
- Command options:
  - `--config, -c` - Custom configuration file
  - `--profile, -p` - Use specific profile
  - `--message, -m` - Custom commit message (push command)
- Multiple profile support with platform-specific paths
- Flexible branching strategies:
  - Shared branch across all machines
  - Per-machine branches based on hostname
  - Custom branch prefixes/postfixes
- SSH and HTTPS authentication support
- Platform-specific credential handling:
  - macOS: osxkeychain
  - Windows: wincred
  - Linux: system Git configuration
- WSL (Windows Subsystem for Linux) support
- Automatic path discovery for:
  - Standard OrcaSlicer installations
  - Portable installations
  - WSL Windows paths
  - Flatpak installations (Linux)
- Comprehensive error handling and helpful error messages
- YAML-based configuration files
- Auto-commit functionality
- Git rebase/merge for conflict handling

### Documentation
- README.md - User guide with quick start
- PROFILES.md - Detailed profile configuration guide
- main.md - Technical documentation and architecture
- CONTRIBUTING.md - Developer and contributor guide
- TROUBLESHOOTING.md - Common issues and solutions
- CHANGELOG.md - Version history
- pyproject.toml - Package metadata and dependencies

### Dependencies
- GitPython >= 3.1.0 - Git operations
- PyYAML >= 6.0 - Configuration file handling
- Click >= 8.0.0 - CLI framework
- Rich >= 13.0.0 - Terminal UI

### Platform Support
- Python >= 3.8
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu, Fedora, Arch, etc.)
- Windows Subsystem for Linux (WSL)

### Known Issues
- No automated conflict resolution UI
- Large repositories may sync slowly
- First-time authentication on macOS may require manual git push

## Release Notes

### v0.1.0 - Initial Release

OrcaSync is a command-line tool for synchronizing OrcaSlicer profiles across multiple machines using Git as a backend. This initial release provides full CLI functionality with support for multiple platforms and flexible configuration.

**Key Features**:
- Easy setup with interactive `init` command
- Simple `sync` command for bidirectional synchronization
- Multiple profile support for different use cases (home, work, etc.)
- Platform-aware path handling - works seamlessly on Windows, macOS, and Linux
- WSL support for using OrcaSlicer on both Windows and Linux from WSL

**Getting Started**:
```bash
pip install orcasync
orcasync init
orcasync sync
```

See [README.md](README.md) for complete documentation.

---

## Version History

- **0.1.0** (2024-01-XX) - Initial release with full CLI support

[Unreleased]: https://github.com/yourusername/orcasync/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/orcasync/releases/tag/v0.1.0
