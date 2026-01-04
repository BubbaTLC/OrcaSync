# OrcaSync

Sync OrcaSlicer profiles between multiple machines using Git. Configure once per profile with platform-specific paths, and OrcaSync automatically uses the right paths for Windows, macOS, or Linux.

## Features

- Cross-platform: Windows, macOS, Linux, WSL
- Profile-based configuration with platform detection
- Git-based sync (HTTPS or SSH)
- Flexible branching: shared branch or per-machine
- Automatic OrcaSlicer path detection

## Installation

```bash
pip install orcasync
```

## Quick Start

**First Machine:**
```bash
orcasync init    # Configure with your Git repo URL
orcasync push    # Upload profiles
```

**Additional Machines:**
```bash
orcasync init    # Same repo URL
orcasync pull    # Download profiles
```

**Daily Usage:**
```bash
orcasync sync    # Bidirectional sync (recommended)
```

## Commands

| Command | Description |
|---------|-------------|
| `orcasync init` | Initialize configuration and repository |
| `orcasync push` | Upload profiles to remote (add `-m "message"` for custom commit) |
| `orcasync pull` | Download profiles from remote |
| `orcasync sync` | Pull then push (recommended) |
| `orcasync status` | Show configuration and sync status |
| `orcasync config-path` | Show config file location |

**Options:** Use `--profile, -p NAME` to specify a profile, or `--config, -c PATH` for custom config file.

## Profile Configuration

OrcaSync uses profiles to manage platform-specific paths. Define paths once, and OrcaSync automatically selects the right ones for your OS.

### Basic Configuration

**Config location:** `~/.config/orcasync/orcasync-config.yaml` (Linux/macOS) or `%APPDATA%\orcasync\orcasync-config.yaml` (Windows)

```yaml
default_profile: default

profiles:
  default:
    repository_url: https://github.com/you/orca-profiles
    branch_name: main  # All machines sync to same branch
    
    paths:
      Darwin:  # macOS
        user_paths:
          - /Users/you/Library/Application Support/OrcaSlicer/user
      Windows:
        user_paths:
          - C:/Users/you/AppData/Roaming/OrcaSlicer/user
      Linux:  # Also WSL
        user_paths:
          - /home/you/.config/OrcaSlicer/user
```

### Multiple Profiles Example

```yaml
default_profile: home

profiles:
  home:
    repository_url: https://github.com/you/home-profiles
    branch_name: home
    paths:
      Darwin:
        user_paths: [/Users/you/Library/Application Support/OrcaSlicer/user]
      Windows:
        user_paths: [C:/Users/you/AppData/Roaming/OrcaSlicer/user]
      Linux:
        user_paths: [/home/you/.config/OrcaSlicer/user]
  
  work:
    repository_url: https://github.com/company/work-profiles
    branch_name: work
    paths:
      # Same structure as home profile
```

**Usage:**
```bash
orcasync sync              # Uses 'home' (default_profile)
orcasync sync --profile work   # Uses 'work' profile
```

### Branching Strategies

**Shared Branch (Recommended):** All machines sync to same branch
```yaml
profiles:
  default:
    branch_name: main
```

**Per-Machine Branches:** Each machine gets its own branch based on hostname
```yaml
profiles:
  default:
    # Omit branch_name to use hostname
    branch_prefix: "machine-"  # Optional prefix
```

### WSL Support

From WSL, you can sync Windows OrcaSlicer:
```yaml
profiles:
  default:
    paths:
      Linux:  # WSL uses Linux platform
        user_paths:
          - /mnt/c/Users/yourname/AppData/Roaming/OrcaSlicer/user
```

## Authentication Setup

**SSH (Recommended):**
```bash
# Generate key
ssh-keygen -t ed25519 -C "your@email.com"

# Add to GitHub: Settings → SSH Keys
cat ~/.ssh/id_ed25519.pub

# Use SSH URL in config
repository_url: git@github.com:username/repo.git
```

**HTTPS with Personal Access Token:**
```yaml
repository_url: https://TOKEN@github.com/username/repo.git
```

**macOS Keychain:**
```bash
git config --global credential.helper osxkeychain
```

**Windows Credential Manager:**
```bash
git config --global credential.helper wincred
```

## Default Profile Paths

| OS | Default Path |
|----|-------------|
| Windows | `C:\Users\<user>\AppData\Roaming\OrcaSlicer\user\` |
| macOS | `~/Library/Application Support/OrcaSlicer/user/` |
| Linux | `~/.config/OrcaSlicer/user/` |
| WSL | `/mnt/c/Users/<user>/AppData/Roaming/OrcaSlicer/user/` |

## Documentation

- **[EXAMPLES.md](EXAMPLES.md)** - Real-world configuration examples
- **[PROFILES.md](PROFILES.md)** - Detailed profile configuration
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues & solutions
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Developer guide
- **[main.md](main.md)** - Technical documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

## Troubleshooting

**Authentication errors:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#authentication-issues) for platform-specific solutions.

**Profile not found:** Check paths with `orcasync status` or edit config at `orcasync config-path`.

**Merge conflicts:** Resolve in `~/.local/share/orcasync/<repo_name>/` using standard Git tools.

## Development

```bash
git clone https://github.com/yourusername/orcasync.git
cd orcasync
pip install -e ".[dev]"
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/orcasync/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/orcasync/discussions)

## License

MIT License - See LICENSE file
