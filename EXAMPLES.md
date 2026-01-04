# OrcaSync Configuration Examples

This document provides real-world configuration examples for various use cases.

## Table of Contents

- [Single User, Multiple Machines (Shared Branch)](#single-user-multiple-machines-shared-branch)
- [Multiple Profiles for Different Purposes](#multiple-profiles-for-different-purposes)
- [Per-Machine Branches](#per-machine-branches)
- [WSL Configuration](#wsl-configuration)
- [Work and Home Separation](#work-and-home-separation)
- [Testing and Production Profiles](#testing-and-production-profiles)
- [Minimal Configuration](#minimal-configuration)

---

## Single User, Multiple Machines (Shared Branch)

**Use Case**: You have multiple machines (laptop, desktop, etc.) and want them all to have identical OrcaSlicer profiles.

**Configuration** (`~/.config/orcasync/orcasync-config.yaml`):

```yaml
default_profile: default
repository_url: https://github.com/yourusername/orca-profiles
repository_name: orca-profiles
auto_commit: true

profiles:
  default:
    branch_name: main  # All machines sync to the same branch
    
    paths:
      Darwin:  # macOS
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
        system_paths: []
      
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
        system_paths: []
      
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
        system_paths: []
```

**Workflow**:
```bash
# On laptop
orcasync sync  # Syncs with desktop

# On desktop  
orcasync sync  # Syncs with laptop
```

---

## Multiple Profiles for Different Purposes

**Use Case**: You have different profile sets for home and work machines, stored in separate repositories.

**Configuration**:

```yaml
default_profile: home  # Use 'home' by default
auto_commit: true

profiles:
  home:
    repository_url: git@github.com:yourusername/home-orca-profiles.git
    repository_name: home-profiles
    branch_name: main
    
    paths:
      Darwin:
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
        system_paths: []
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
        system_paths: []
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
        system_paths: []
  
  work:
    repository_url: git@github.com:yourcompany/work-orca-profiles.git
    repository_name: work-profiles
    branch_name: main
    
    paths:
      Darwin:
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
        system_paths: []
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
        system_paths: []
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
        system_paths: []
```

**Workflow**:
```bash
# At home
orcasync sync  # Uses 'home' profile by default

# At work
orcasync sync --profile work  # Explicitly use work profile
```

---

## Per-Machine Branches

**Use Case**: Each machine has unique configurations that you want to track separately but in the same repository.

**Configuration**:

```yaml
default_profile: default
repository_url: https://github.com/yourusername/orca-profiles
repository_name: orca-profiles
auto_commit: true

profiles:
  default:
    # No branch_name specified = uses hostname
    # Creates branches like: laptop, desktop, mini
    branch_prefix: ""
    branch_postfix: ""
    
    paths:
      Darwin:
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
        system_paths: []
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
        system_paths: []
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
        system_paths: []
```

**Result**: 
- Machine named "laptop" → branch `laptop`
- Machine named "desktop" → branch `desktop`
- Machine named "mini" → branch `mini`

**Workflow**:
```bash
# Each machine pushes to its own branch
orcasync push

# To get settings from another machine:
cd ~/.local/share/orcasync/orca-profiles
git checkout desktop  # Switch to desktop's branch
cd -
orcasync pull  # Pull desktop's settings
```

---

## WSL Configuration

**Use Case**: You use Windows Subsystem for Linux and want to sync Windows OrcaSlicer profiles.

**Configuration** (in WSL):

```yaml
default_profile: default
repository_url: git@github.com:yourusername/orca-profiles.git
repository_name: orca-profiles
auto_commit: true

profiles:
  default:
    branch_name: main
    
    paths:
      # WSL uses 'Linux' platform configuration
      Linux:
        user_paths:
          # Access Windows OrcaSlicer via /mnt/c
          - /mnt/c/Users/YourWindowsUsername/AppData/Roaming/OrcaSlicer/user
        system_paths: []
```

**Alternative** (sync both WSL and Windows installations):

```yaml
default_profile: default
repository_url: git@github.com:yourusername/orca-profiles.git

profiles:
  wsl-native:
    branch_name: wsl
    paths:
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
  
  windows:
    branch_name: windows
    paths:
      Linux:
        user_paths:
          - /mnt/c/Users/YourWindowsUsername/AppData/Roaming/OrcaSlicer/user
```

**Workflow**:
```bash
# Sync WSL native installation
orcasync sync --profile wsl-native

# Sync Windows installation from WSL
orcasync sync --profile windows
```

---

## Work and Home Separation

**Use Case**: Completely separate work and personal profiles with different repositories and custom commit messages.

**Configuration**:

```yaml
default_profile: home
commit_message_template: "Sync from {hostname} - {timestamp}"

profiles:
  home:
    repository_url: git@github.com:yourusername/personal-orca.git
    repository_name: home-profiles
    branch_name: main
    auto_commit: true
    commit_message_template: "Home sync from {hostname} - {timestamp}"
    
    paths:
      Darwin:
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
        system_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/system
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
        system_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/system
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
        system_paths:
          - /home/yourname/.config/OrcaSlicer/system
  
  work:
    repository_url: git@github.com:yourcompany/orca-profiles.git
    repository_name: work-profiles
    branch_name: production
    auto_commit: true
    commit_message_template: "Work sync from {hostname} - {timestamp}"
    
    paths:
      Darwin:
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
        system_paths: []
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
        system_paths: []
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
        system_paths: []
```

---

## Testing and Production Profiles

**Use Case**: You want to test configuration changes before deploying to all machines.

**Configuration**:

```yaml
default_profile: production
repository_url: https://github.com/yourusername/orca-profiles
auto_commit: true

profiles:
  production:
    branch_name: main
    paths:
      Darwin:
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
  
  testing:
    branch_name: testing
    paths:
      Darwin:
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
```

**Workflow**:
```bash
# Test changes on one machine
orcasync push --profile testing

# On another test machine
orcasync pull --profile testing

# After testing, merge testing → main manually via Git
cd ~/.local/share/orcasync/orca-profiles
git checkout main
git merge testing
git push

# Deploy to production machines
orcasync pull  # Uses production profile
```

---

## Minimal Configuration

**Use Case**: Simplest possible setup for single user.

**Configuration**:

```yaml
default_profile: default

profiles:
  default:
    repository_url: https://github.com/yourusername/orca-profiles
    branch_name: main
    paths:
      Darwin:
        user_paths:
          - /Users/yourname/Library/Application Support/OrcaSlicer/user
      Windows:
        user_paths:
          - C:/Users/yourname/AppData/Roaming/OrcaSlicer/user
      Linux:
        user_paths:
          - /home/yourname/.config/OrcaSlicer/user
```

---

## Custom Paths for Portable Installation

**Use Case**: OrcaSlicer installed in a custom location.

**Configuration**:

```yaml
default_profile: default

profiles:
  default:
    repository_url: https://github.com/yourusername/orca-profiles
    branch_name: main
    paths:
      Windows:
        user_paths:
          - D:/PortableApps/OrcaSlicer/data/user
        system_paths:
          - D:/PortableApps/OrcaSlicer/data/system
```

---

## SSH Authentication Setup

**For better automation, use SSH instead of HTTPS:**

```bash
# 1. Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. Add to GitHub
cat ~/.ssh/id_ed25519.pub
# Copy output and add at: https://github.com/settings/keys

# 3. Test connection
ssh -T git@github.com

# 4. Use SSH URL in config
repository_url: git@github.com:yourusername/orca-profiles.git
```

---

## Syncing Only Specific Subdirectories

**Note**: Current version syncs entire `user/` and `system/` directories. For selective syncing, you can manually modify the repository:

```bash
cd ~/.local/share/orcasync/orca-profiles/profiles/user

# Create .gitignore to exclude certain folders
echo "cache/" >> .gitignore
echo "*.log" >> .gitignore

git add .gitignore
git commit -m "Exclude cache and logs"
orcasync push
```

---

## Environment-Specific Configuration

You can use different config files for different environments:

```bash
# Development config
orcasync sync --config ~/configs/orcasync-dev.yaml

# Production config
orcasync sync --config ~/configs/orcasync-prod.yaml
```

---

## Tips and Best Practices

1. **Start Simple**: Use the default profile with shared branch
2. **Use SSH**: More reliable for automation than HTTPS
3. **Private Repos**: Keep your profiles private for security
4. **Test First**: Test on one machine before deploying everywhere
5. **Backup First**: Make a backup before major changes
6. **Commit Messages**: Use descriptive commit messages with `--message`
7. **Regular Syncs**: Run `orcasync sync` regularly to stay in sync

---

For more information, see:
- [README.md](README.md) - Main documentation
- [PROFILES.md](PROFILES.md) - Profile configuration guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
