# OrcaSync Profiles

## Overview

Profiles allow you to use the same OrcaSync configuration across multiple machines (Mac, Windows, Linux) by automatically selecting the correct local paths for each platform while syncing to the same repository.

## How It Works

1. **Single Profile, Multiple Machines**: Define a profile once (e.g., "home") with platform-specific paths
2. **Platform Detection**: OrcaSync automatically uses the right paths based on your current OS
3. **Unified Sync**: All machines sync to the same repository/branch
4. **Bidirectional Changes**: Changes on any machine sync to all others

## Example Workflow

### On Mac:
```bash
# Add a new filament profile in OrcaSlicer
orcasync push                    # Pushes to 'home' branch (default profile)
```

### On Windows:
```bash
orcasync pull                    # Pulls from 'home' branch
# See the new filament in OrcaSlicer

# Delete a printer profile in OrcaSlicer  
orcasync push                    # Pushes deletion to 'home' branch
```

### Back on Mac:
```bash
orcasync pull                    # Pulls changes
# Printer profile is deleted
```

## Configuration Example

```yaml
# Set which profile to use by default
default_profile: home

profiles:
  home:
    # Shared settings (same for all machines)
    repository_url: https://github.com/you/orca-profiles
    repository_name: home-profiles
    branch_name: home              # All machines sync to same branch
    auto_commit: true
    
    # Platform-specific paths
    paths:
      Darwin:  # macOS
        user_paths:
          - /Users/you/Library/Application Support/OrcaSlicer/user
        system_paths:
          - /Users/you/Library/Application Support/OrcaSlicer/system
      
      Windows:
        user_paths:
          - C:/Users/you/AppData/Roaming/OrcaSlicer/user
        system_paths:
          - C:/Users/you/AppData/Roaming/OrcaSlicer/system
      
      Linux:  # Also used for WSL
        user_paths:
          - /home/you/.config/OrcaSlicer/user
        system_paths:
          - /home/you/.config/OrcaSlicer/system
  
  work:
    # Separate profile for work machines
    repository_url: https://github.com/you/work-profiles
    branch_name: work
    paths:
      Darwin:
        user_paths:
          - /Users/you/Library/Application Support/OrcaSlicer/user
      Windows:
        user_paths:
          - C:/Users/you/AppData/Roaming/OrcaSlicer/user
```

## Usage

### Using the Default Profile
```bash
orcasync push           # Uses 'home' (from default_profile)
orcasync pull
orcasync status
```

### Using a Specific Profile
```bash
orcasync push --profile work
orcasync pull --profile work
orcasync status --profile work
```

### Without Profiles (Legacy)
If you don't define profiles, OrcaSync uses the global settings at the root of the config file.

## Profile Settings

### Shared Settings (Same Across All Machines)
- `repository_url`: GitHub repo URL
- `repository_name`: Local repo name
- `branch_name`: Git branch (or use branch_prefix/postfix with hostname)
- `auto_commit`: Auto-commit changes
- `commit_message_template`: Commit message format

### Platform-Specific Settings
- `paths.Darwin`: macOS paths
- `paths.Windows`: Windows paths
- `paths.Linux`: Linux/WSL paths

Each platform can specify:
- `user_paths`: List of user profile directories
- `system_paths`: List of system profile directories

## Merging Behavior

Profile settings **override** global settings:
1. Start with global settings (at config root)
2. Platform-specific paths are selected based on current OS
3. Other profile settings override global settings
4. Result: Merged configuration specific to current machine and profile

## Multiple Profiles

You can have multiple profiles for different purposes:
- **home**: Personal machines syncing home profiles
- **work**: Work machines syncing work profiles
- **testing**: Testing new configurations

Each profile can sync to:
- Different repositories
- Different branches in the same repository
- Different local paths
