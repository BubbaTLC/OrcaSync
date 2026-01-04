# OrcaSync - Technical Documentation

OrcaSync is a command-line tool designed to sync OrcaSlicer profiles between multiple machines using Git as a backend.

Files are stored within a Git repository, allowing users to push and pull changes to their OrcaSlicer setup easily across Windows, macOS, and Linux systems.

## Architecture Overview

### Core Components

1. **CLI Module** (`cli.py`):
   - Command-line interface using Click framework
   - Rich terminal UI for better user experience
   - Commands: init, push, pull, sync, status, config-path

2. **Configuration Module** (`config.py`):
   - YAML-based configuration management
   - Multi-profile support with platform-specific paths
   - Automatic OrcaSlicer installation detection
   - WSL-aware path discovery

3. **Git Operations Module** (`git_ops.py`):
   - GitPython-based repository management
   - Bidirectional file synchronization
   - Platform-specific credential handling
   - Conflict resolution via Git rebase/merge

### Data Flow

```
OrcaSlicer Profiles  →  Local Git Repo  →  Remote Git Repo
       ↑                                          ↓
       └──────────  Sync Command  ───────────────┘
```

1. **Push**: Copies profiles → commits → pushes to remote
2. **Pull**: Pulls from remote → extracts → copies to OrcaSlicer
3. **Sync**: Pull + Push in one operation

## Profile Storage Locations

| Operating System | Default User Profile Path                                                         | Default System Profile Path                              | Notes                                                                                                                                                                                    |
| ---------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Windows          | `C:\Users\<username>\AppData\Roaming\OrcaSlicer\user\` | `C:\Users\<username>\AppData\Roaming\OrcaSlicer\system\` | AppData is a hidden folder. User profiles are JSON files within subfolders (filament, machine, process).                                                                                 |
| macOS            | `~/Library/Application Support/OrcaSlicer/user/`                                  | `~/Library/Application Support/OrcaSlicer/system/`       | Library is a hidden folder. Bundled system profiles can also be found by right-clicking the Orca app, then Show Contents → Contents → Resources → Profiles.                     |
| Linux            | `~/.config/OrcaSlicer/user/`                                                      | `~/.config/OrcaSlicer/system/`                           | .config is a hidden folder. AppImage versions typically use this path. Some Flatpak installations may use `/home/<user name>/.var/app/io.github.softfever.OrcaSlicer/config/OrcaSlicer`. |
| WSL              | `/mnt/c/Users/<username>/AppData/Roaming/OrcaSlicer/user/`                       | `/mnt/c/Users/<username>/AppData/Roaming/OrcaSlicer/system/` | Can sync Windows paths from WSL environment |
| Portable Version | `(Custom data_dir or --datadir option)`                                           | `(Custom data_dir or --datadir option)`                  | If a data_dir folder exists under the application's path, OrcaSlicer uses it. The --datadir command line option allows specifying any custom location.                                        |

## Installation

### For End Users

**Using pip (requires Python 3.8+):**
```bash
pip install orcasync
```

**From source:**
```bash
git clone https://github.com/yourusername/orcasync.git
cd orcasync
pip install -e .
```

OrcaSync must be installed on all machines that will be syncing OrcaSlicer profiles.

## Configuration

### Configuration File Location

- **Linux/macOS**: `~/.config/orcasync/orcasync-config.yaml`
- **Windows**: `%APPDATA%\orcasync\orcasync-config.yaml`
- **Current directory**: `./orcasync-config.yaml` (checked first)

### Configuration Structure

```yaml
# Global settings
default_profile: default
repository_url: https://github.com/user/orca-profiles
repository_name: orca-profiles
auto_commit: true
commit_message_template: "Sync from {hostname} - {timestamp}"

# Profile definitions
profiles:
  default:
    branch_name: main
    paths:
      Darwin:    # macOS
        user_paths: [...]
        system_paths: []
      Windows:
        user_paths: [...]
        system_paths: []
      Linux:
        user_paths: [...]
        system_paths: []
```

### Configuration Options

| Option | Type | Description | Default |
| ------ | ---- | ----------- | ------- |
| `default_profile` | string | Profile to use when none specified | `default` |
| `repository_url` | string | Git repository URL (HTTPS or SSH) | (empty) |
| `repository_name` | string | Local repository directory name | `orca-profiles` |
| `auto_commit` | boolean | Automatically commit changes | `true` |
| `commit_message_template` | string | Template for commit messages | `Sync from {hostname} - {timestamp}` |

### Profile Options

| Option | Type | Description | Notes |
| ------ | ---- | ----------- | ----- |
| `branch_name` | string | Git branch to use | Overrides branch_prefix/postfix |
| `branch_prefix` | string | Prefix for hostname-based branch | Used if branch_name not set |
| `branch_postfix` | string | Postfix for hostname-based branch | Used if branch_name not set |
| `paths` | object | Platform-specific path configuration | Required |
| `repository_url` | string | Override global repository URL | Optional |
| `repository_name` | string | Override global repository name | Optional |

## Local Repository Location

Profiles are stored locally at:
- **Linux/macOS**: `~/.local/share/orcasync/<repository_name>/`
- **Windows**: `%LOCALAPPDATA%\orcasync\<repository_name>\`

## Security Recommendations

1. **Use private repositories** to protect your profile data
2. **Use SSH authentication** for better security and automation
3. **Keep sensitive data out of profiles** (API keys, passwords, etc.)
4. **Regular backups** - Git provides version history but backup your remote repo

## Implementation Details

### Credential Handling

- **macOS**: Uses `osxkeychain` credential helper
- **Windows**: Uses `wincred` credential helper  
- **Linux**: Uses system Git configuration
- **Non-interactive**: Prevents hanging on credential prompts

### Conflict Resolution

- Uses Git rebase for linear history on per-machine branches
- Falls back to merge if rebase fails
- Provides helpful error messages for common issues

### File Synchronization

1. Copies entire directory trees (user/ and/or system/)
2. Preserves directory structure
3. Handles deletions via Git operations
4. Tracks all file changes through Git