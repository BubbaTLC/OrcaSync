# OrcaSync

OrcaSync is a tool designed to sync OrcaSlicer profiles between multiple machines using Git as a backend.

Files are stored within a Git repository, allowing users to push and pull changes to their Orca setup easily.

## Features

- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ Git-based synchronization
- ✅ Automatic profile detection
- ✅ Per-machine branching
- ✅ Simple CLI interface
- ✅ Conflict handling via Git
- 🚧 GUI interface (planned)

## Installation

### For End Users

**Option 1: Using pip (requires Python 3.8+)**
```bash
pip install orcasync
```

**Option 2: Standalone executable (coming soon)**

Download the latest release for your platform from the [releases page](https://github.com/yourusername/orcasync/releases).

### For Developers

```bash
# Clone repository
git clone https://github.com/yourusername/orcasync.git
cd orcasync

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

### 1. Initialize OrcaSync

```bash
orcasync init
```

This will:
- Create a configuration file
- Ask for your Git repository URL (optional)
- Detect your OrcaSlicer profile locations
- Initialize the local Git repository
- Create a branch for your machine

### 2. Push Your Profiles

Upload your current OrcaSlicer profiles to the repository:

```bash
orcasync push
```

### 3. Pull Profiles on Another Machine

On another machine, after running `orcasync init` with the same repository URL:

```bash
orcasync pull
```

## Usage

### Commands

- `orcasync init` - Initialize configuration and repository
- `orcasync push` - Upload local profiles to repository
- `orcasync pull` - Download profiles from repository
- `orcasync status` - Show current sync status
- `orcasync config-path` - Show path to config file

### Configuration

The configuration file is located at:
- Linux/macOS: `~/.config/orcasync/orcasync-config.yaml`
- Windows: `%APPDATA%\orcasync\orcasync-config.yaml`

You can also specify a custom config file with the `--config` flag.

#### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `repository_url` | Git repository URL | (empty) |
| `repository_name` | Local repository name | `orca-profiles` |
| `branch_prefix` | Prefix for branch names | (empty) |
| `branch_postfix` | Postfix for branch names | (empty) |
| `user_paths` | Paths to user profiles | Auto-detected |
| `system_paths` | Paths to system profiles | Auto-detected |
| `auto_commit` | Auto-commit changes | `true` |

## Profile Storage Locations

| Operating System | Default User Profile Path |
|-----------------|---------------------------|
| Windows | `C:\Users\<username>\AppData\Roaming\OrcaSlicer\user\` |
| macOS | `~/Library/Application Support/OrcaSlicer/user/` |
| Linux | `~/.config/OrcaSlicer/user/` |

## How It Works

1. **Per-Machine Branches**: Each machine gets its own Git branch (named after the hostname by default)
2. **Local Repository**: Profiles are copied to a local Git repository
3. **Git Sync**: Changes are committed and pushed/pulled using standard Git operations
4. **Conflict Handling**: Git's merge capabilities handle conflicts when syncing between machines

## Recommended Workflow

1. **Use Private Repository**: Store your profiles in a private Git repository for security
2. **Branch per Machine**: Use the default hostname-based branching to avoid conflicts
3. **Regular Syncs**: Push changes after making profile updates, pull before starting work on another machine

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black orca_sync/
```

### Type Checking

```bash
mypy orca_sync/
```

## Building Standalone Executables

Coming soon: Instructions for building platform-specific executables using PyInstaller.

## Roadmap

- [x] CLI implementation
- [x] Basic push/pull functionality
- [x] Auto-detection of profile paths
- [ ] Conflict resolution UI
- [ ] GUI application
- [ ] Auto-sync on profile changes
- [ ] Multiple profile sets support
- [ ] Selective file syncing

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/yourusername/orcasync/issues)
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/yourusername/orcasync/discussions)
# Test update
