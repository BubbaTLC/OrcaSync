# OrcaSync Troubleshooting Guide

This guide covers common issues and their solutions.

## Installation Issues

### Python Version Error

**Problem**: `ERROR: orcasync requires Python '>=3.8'`

**Solution**: 
```bash
# Check your Python version
python --version

# Use Python 3.8+ 
python3 --version

# Install with specific Python version
python3.10 -m pip install orcasync
```

### Command Not Found

**Problem**: `orcasync: command not found`

**Solution**:
```bash
# Check if pip bin directory is in PATH
python -m pip show orcasync

# Run directly via Python module
python -m orcasync.cli --help

# Or add pip bin directory to PATH
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
```

## Authentication Issues

### macOS: Authentication Failed

**Problem**: 
```
[✗] Failed to push: Authentication failed. Git cannot prompt for credentials
```

**Solution 1 - Use SSH (Recommended)**:
```bash
# 1. Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. Add to GitHub
cat ~/.ssh/id_ed25519.pub  # Copy this

# 3. Go to GitHub → Settings → SSH Keys → Add

# 4. Update config file
nano ~/.config/orcasync/orcasync-config.yaml

# Change:
repository_url: git@github.com:username/repo.git
```

**Solution 2 - Configure Credential Helper**:
```bash
# Configure macOS Keychain
git config --global credential.helper osxkeychain

# Manually authenticate once
cd ~/.local/share/orcasync/orca-profiles
git push  # Enter credentials when prompted
```

**Solution 3 - Use Personal Access Token**:
```bash
# 1. Generate PAT on GitHub: Settings → Developer settings → Personal access tokens
# 2. Use HTTPS URL with token embedded:
repository_url: https://TOKEN@github.com/username/repo.git
```

### Windows: Credential Issues

**Problem**: Authentication errors on Windows

**Solution**:
```bash
# Configure Windows Credential Manager
git config --global credential.helper wincred

# Or use Git Credential Manager
git config --global credential.helper manager-core
```

### Linux: Permission Denied (publickey)

**Problem**: SSH authentication failing

**Solution**:
```bash
# Test SSH connection
ssh -T git@github.com

# If fails, add SSH key to agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Ensure correct permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
```

## Configuration Issues

### No OrcaSlicer Profiles Found

**Problem**: `⚠ No OrcaSlicer profiles found in standard locations`

**Solution**:
```bash
# Find OrcaSlicer installation manually
# Windows:
dir %APPDATA%\OrcaSlicer /s

# macOS:
find ~/Library -name OrcaSlicer 2>/dev/null

# Linux:
find ~/.config -name OrcaSlicer 2>/dev/null
find ~/.local -name OrcaSlicer 2>/dev/null

# Then specify path manually in config:
nano ~/.config/orcasync/orcasync-config.yaml
```

### Config File Location

**Problem**: Can't find config file

**Solution**:
```bash
# Show config path
orcasync config-path

# View config
cat $(orcasync config-path)

# Edit config
nano $(orcasync config-path)
```

### Invalid Configuration

**Problem**: `Failed to load config: ...`

**Solution**:
```bash
# Backup current config
cp ~/.config/orcasync/orcasync-config.yaml ~/.config/orcasync/orcasync-config.yaml.bak

# Reinitialize
orcasync init

# Or validate YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.config/orcasync/orcasync-config.yaml'))"
```

## Sync Issues

### Push Rejected (non-fast-forward)

**Problem**: `Push rejected (non-fast-forward)`

**Solution**:
```bash
# Pull changes first
orcasync pull

# Then push
orcasync push

# Or use sync command (does both)
orcasync sync
```

### Merge Conflicts

**Problem**: Conflicting changes between machines

**Solution**:
```bash
# Go to local repository
cd ~/.local/share/orcasync/orca-profiles

# View status
git status

# Resolve conflicts manually
git mergetool  # or edit files directly

# Or reset to remote version
git fetch origin
git reset --hard origin/main

# Then re-run sync
orcasync sync
```

### No Changes to Commit

**Problem**: `No changes to commit` but files have changed

**Solution**:
```bash
# Check if files are in the right location
orcasync status

# Verify paths in config
cat $(orcasync config-path)

# Check OrcaSlicer is actually saving to those paths
ls -la ~/.config/OrcaSlicer/user/  # Linux example
```

### Repository Not Found (404)

**Problem**: `Repository not found: https://github.com/user/repo.git`

**Solution**:
```bash
# Check repository exists and you have access
# Visit: https://github.com/user/repo

# Verify repository URL in config
cat $(orcasync config-path)

# Update if incorrect
nano $(orcasync config-path)

# Create repository if needed
# Go to GitHub → New Repository
```

## Profile Issues

### Profile Not Found

**Problem**: `Profile 'work' not found in config`

**Solution**:
```bash
# List available profiles
orcasync status

# Check config file
cat $(orcasync config-path)

# Use default profile
orcasync push  # Without --profile flag

# Or create the profile
nano $(orcasync config-path)
```

### Wrong Profile Being Used

**Problem**: Using incorrect profile

**Solution**:
```bash
# Check which profile is active
orcasync status

# Change default profile in config
nano $(orcasync config-path)
# Set: default_profile: name

# Or specify profile explicitly
orcasync push --profile home
```

## WSL-Specific Issues

### Can't Access Windows Paths

**Problem**: Windows OrcaSlicer paths not accessible from WSL

**Solution**:
```bash
# Check if Windows drives are mounted
ls /mnt/c/

# Find Windows username
ls /mnt/c/Users/

# Use correct path in config
user_paths:
  - /mnt/c/Users/YourWindowsUsername/AppData/Roaming/OrcaSlicer/user

# Check permissions
ls -la /mnt/c/Users/YourWindowsUsername/AppData/Roaming/OrcaSlicer/
```

### Mixed Line Endings

**Problem**: Git warnings about CRLF/LF line endings

**Solution**:
```bash
# Configure Git line ending handling
git config --global core.autocrlf input  # WSL/Linux
git config --global core.autocrlf true   # Windows

# In repository
cd ~/.local/share/orcasync/orca-profiles
git config core.autocrlf input
```

## Performance Issues

### Slow Sync Operations

**Problem**: Sync takes too long

**Solution**:
```bash
# Check number of files being synced
orcasync status

# Disable system profiles if not needed
nano $(orcasync config-path)
# Set: system_paths: []

# Clean up OrcaSlicer profiles
# Remove unused filament/machine/process profiles in OrcaSlicer

# Use .gitignore for large files (if needed)
echo "*.large_file" >> ~/.local/share/orcasync/orca-profiles/.gitignore
```

### Large Repository Size

**Problem**: Repository growing too large

**Solution**:
```bash
# Check repository size
du -sh ~/.local/share/orcasync/orca-profiles

# Clean Git history (advanced)
cd ~/.local/share/orcasync/orca-profiles
git gc --aggressive --prune=now

# Or start fresh (backup first!)
mv ~/.local/share/orcasync/orca-profiles ~/.local/share/orcasync/orca-profiles.bak
orcasync init
orcasync push
```

## Platform-Specific Issues

### macOS: Library Folder Hidden

**Problem**: Can't find Library folder

**Solution**:
```bash
# Show hidden files in Finder
# Press: Cmd + Shift + . (period)

# Or navigate directly
open ~/Library/Application\ Support/OrcaSlicer/

# In terminal
ls -la ~/Library/Application\ Support/OrcaSlicer/
```

### Windows: AppData Folder Hidden

**Problem**: Can't see AppData folder

**Solution**:
1. Open File Explorer
2. Click View → Options → Change folder and search options
3. View tab → Show hidden files, folders, and drives
4. OK

Or in terminal:
```cmd
explorer %APPDATA%\OrcaSlicer
```

### Linux: Flatpak Installation

**Problem**: OrcaSlicer installed via Flatpak uses different path

**Solution**:
```bash
# Check Flatpak path
ls ~/.var/app/io.github.softfever.OrcaSlicer/config/

# Use in config
user_paths:
  - /home/you/.var/app/io.github.softfever.OrcaSlicer/config/OrcaSlicer/user
```

## Getting More Help

### Enable Verbose Logging

For debugging, you can run commands with Python's verbose mode:

```bash
python -v -m orcasync.cli status
```

### Check Git Operations Manually

```bash
# Navigate to local repository
cd ~/.local/share/orcasync/orca-profiles

# Check status
git status

# View log
git log --oneline -10

# Check remotes
git remote -v

# Test connectivity
git fetch --dry-run
```

### Reset Everything

Last resort - complete reset:

```bash
# Backup current OrcaSlicer profiles
cp -r ~/.config/OrcaSlicer ~/.config/OrcaSlicer.backup  # Linux

# Remove OrcaSync data
rm -rf ~/.config/orcasync
rm -rf ~/.local/share/orcasync

# Reinstall
pip uninstall orcasync
pip install orcasync

# Reinitialize
orcasync init
```

## Reporting Issues

If none of these solutions work:

1. **Gather information**:
   ```bash
   orcasync --version
   python --version
   git --version
   orcasync status
   ```

2. **Check existing issues**: [GitHub Issues](https://github.com/yourusername/orcasync/issues)

3. **Create new issue** with:
   - Operating system and version
   - Python and Git versions
   - Complete error message
   - Steps to reproduce
   - Config file (remove sensitive data)

4. **Get community help**: [GitHub Discussions](https://github.com/yourusername/orcasync/discussions)
