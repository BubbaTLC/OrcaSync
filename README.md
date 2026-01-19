# OrcaSync

Sync OrcaSlicer profiles between multiple machines using Git. Configure once per profile with platform-specific paths, and OrcaSync automatically uses the right paths for Windows, macOS, or Linux.

## Features

- **Interactive TUI**: Beautiful terminal user interface for easy operation
- **Cross-platform**: Windows, macOS, Linux, WSL
- **Profile-based configuration** with platform detection
- **Git-based sync** (HTTPS or SSH)
- **Flexible branching**: shared branch or per-machine
- **Automatic OrcaSlicer path detection**
- **CLI commands** available for scripting and automation

## Installation

### Option 1: Standalone Executable (No Python Required)

Download the latest executable for your platform from the [Releases page](https://github.com/BubbaTLC/OrcaSync/releases):

- **Linux (AMD64)**: `orcasync-linux-amd64`
- **Windows (AMD64)**: `orcasync-windows-amd64.exe`
- **macOS Intel (x86_64)**: `orcasync-macos-x86_64`
- **macOS Apple Silicon (ARM64)**: `orcasync-macos-arm64`

#### Linux Installation
```bash
chmod +x orcasync-linux-amd64
sudo mv orcasync-linux-amd64 /usr/local/bin/orcasync
```

#### macOS Installation
```bash
# Download the appropriate version for your Mac
chmod +x orcasync-macos-*
sudo mv orcasync-macos-* /usr/local/bin/orcasync

# First time running: macOS will block unsigned apps
# Right-click the app and select "Open", or run:
sudo xattr -rd com.apple.quarantine /usr/local/bin/orcasync
```

**Note for macOS users**: The first time you run the executable, macOS Gatekeeper may block it because it's not signed with an Apple Developer certificate. To allow it:

1. **Method 1** (Recommended): Remove the quarantine attribute:
   ```bash
   sudo xattr -rd com.apple.quarantine /usr/local/bin/orcasync
   ```

2. **Method 2**: Go to System Settings → Privacy & Security, scroll down and click "Open Anyway" next to the blocked app message.

#### Windows Installation
```powershell
# Move to a permanent location
move orcasync-windows-amd64.exe C:\Windows\System32\orcasync.exe
# Or add the directory containing the executable to your PATH
```

### Option 2: Install with UV (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast Python package installer. Install UV first:

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install orcasync:

```bash
uv tool install orcasync
```

### Option 3: Install with pip

```bash
pip install orcasync
```

## Quick Start

### Using the Interactive TUI (Recommended)

Simply run `orcasync` to launch the interactive terminal interface:

```bash
orcasync
```

The TUI provides:
- **Status Dashboard** - View your current configuration and sync status at a glance
- **Interactive Menu** - Navigate with arrow keys or use keyboard shortcuts
- **Real-time Logs** - See exactly what's happening during sync operations
- **Guided Setup** - Walk through initialization step-by-step

**Keyboard Shortcuts:**
- `i` - Initialize configuration
- `p` - Push profiles to remote
- `P` - Pull profiles from remote  
- `s` - Sync (pull + push)
- `r` - Refresh status
- `c` - Clear logs
- `q` - Quit

### Using CLI Commands

For automation or scripting, use CLI commands directly:

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

### Interactive TUI

Run without any arguments to launch the interactive interface:

```bash
orcasync
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `orcasync` | Launch interactive TUI (default) |
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

**Important Note:** Starting with v0.2.1, automatic WSL path detection has been removed. WSL users must manually configure their Windows OrcaSlicer paths.

From WSL, you can sync Windows OrcaSlicer profiles by manually specifying the Windows path through the `/mnt/c/` mount point:

```yaml
profiles:
  default:
    paths:
      Linux:  # WSL uses Linux platform detection
        user_paths:
          - /mnt/c/Users/YourWindowsUsername/AppData/Roaming/OrcaSlicer/user
```

**Finding your Windows username in WSL:**
```bash
# List Windows users
ls /mnt/c/Users/

# Verify OrcaSlicer directory exists
ls /mnt/c/Users/YourWindowsUsername/AppData/Roaming/OrcaSlicer/
```

**Alternative:** Use OrcaSlicer's Linux installation in WSL:
```yaml
profiles:
  default:
    paths:
      Linux:
        user_paths:
          - /home/yourlinuxusername/.config/OrcaSlicer/user
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

# Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/orcasync/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/orcasync/discussions)

## License

MIT License - See LICENSE file
