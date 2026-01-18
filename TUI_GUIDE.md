# TUI User Guide

## Overview

OrcaSync now includes an interactive Terminal User Interface (TUI) that makes it easy to sync your OrcaSlicer profiles without memorizing commands.

## Launching the TUI

Simply run `orcasync` with no arguments:

```bash
orcasync
```

Or if using UV:

```bash
uv run orcasync
```

When building from source or running the executable:

```bash
# macOS/Linux
./orcasync

# Windows  
orcasync.exe
```

## Interface Layout

The TUI is divided into three main sections:

### 1. Status Dashboard (Top)
Shows your current configuration:
- Active profile name
- Config file location
- Git repository URL and branch
- OrcaSlicer profile paths and file counts
- Repository status (branch, uncommitted changes, synced files)

### 2. Main Menu (Middle)
Interactive buttons for all operations:
- **Init** - Set up configuration and initialize repository
- **Push** - Upload your local profiles to the remote repository
- **Pull** - Download profiles from the remote repository
- **Sync** - Perform a full bidirectional sync (pull + push)
- **Refresh** - Update the status dashboard
- **Clear Logs** - Clear the log panel

### 3. Logs Panel (Bottom)
Real-time output showing:
- Operation progress
- Success/error messages
- File counts and sync details
- Color-coded messages (green = success, yellow = warning, red = error, blue = info)

## Navigation

### Using Mouse
- Click any button to execute that operation
- Scroll through logs with mouse wheel

### Using Keyboard

#### Hotkeys
- `i` - Initialize configuration
- `p` - Push profiles
- `P` (Shift+p) - Pull profiles
- `s` - Sync profiles
- `r` - Refresh status
- `c` - Clear logs
- `q` - Quit application

#### Arrow Keys
- Navigate between buttons with ↑↓←→
- Press `Enter` to activate selected button
- Press `Tab` to cycle through interactive elements

## Typical Workflows

### First Time Setup

1. Launch TUI: `orcasync`
2. Press `i` or click **Init**
3. Fill in the configuration form:
   - Git repository URL (or leave empty for local-only)
   - Repository name (defaults to "orca-profiles")
   - Branch name (defaults to "main")
   - Custom paths (optional, auto-detected if available)
4. Click **Save & Initialize**
5. Watch the logs as the repository is initialized
6. Press `p` or click **Push** to upload your current profiles

### Daily Sync on Other Machines

1. Launch TUI: `orcasync`
2. Press `s` or click **Sync**
3. Watch the logs to see:
   - Step 1: Fetch from remote
   - Step 2: Pull changes and restore to OrcaSlicer
   - Step 3: Push any local changes back
4. Press `r` to refresh status and see updated file counts

### Pushing Local Changes

1. Launch TUI: `orcasync`
2. Make changes in OrcaSlicer
3. Press `p` or click **Push**
4. Your changes are committed and pushed to the remote

### Getting Remote Changes

1. Launch TUI: `orcasync`
2. Press `P` (Shift+p) or click **Pull**
3. Remote changes are downloaded and applied to your OrcaSlicer

## Tips

- **Auto-refresh**: Press `r` after operations to update the status dashboard
- **Monitor logs**: Keep an eye on the logs panel for detailed operation feedback
- **Clear logs**: Press `c` when logs get too long for easier reading
- **Status at a glance**: The status panel shows if you have uncommitted changes
- **Multiple profiles**: Use `orcasync -p <profile>` to launch TUI with a specific profile

## CLI Still Available

The TUI doesn't replace the CLI - you can still use commands directly:

```bash
# Use CLI commands directly
orcasync push
orcasync pull
orcasync sync
orcasync status

# Or launch TUI
orcasync
```

This is useful for:
- Automation scripts
- Cron jobs / scheduled tasks
- Integration with other tools
- Quick operations without the full interface

## Troubleshooting

**TUI won't launch:**
- Make sure Textual is installed: `uv add textual` or `pip install textual`
- Check terminal compatibility (most modern terminals work)
- Try running with `orcasync status` to verify installation

**Buttons not responding:**
- Use keyboard shortcuts instead
- Check if terminal supports mouse input
- Try resizing the terminal window

**Status not updating:**
- Press `r` to manually refresh
- Operations automatically refresh status when complete

**Init form not showing discovered paths:**
- Paths are auto-detected, but you can still add custom paths
- Check that OrcaSlicer is installed in standard locations
