# OrcaSync - Next Features & Roadmap

## Next Features for OrcaSync

### From the Project Plan (Priority Order)

**Short Term (v0.2.0) - Highest Priority:**
1. **Automated test suite** - Currently no tests exist
2. **Dry-run mode** - Preview changes without executing them
3. **Configuration validation** - Catch errors before running commands
4. **Better error recovery** - More graceful handling of failures
5. **PyPI packaging** - Easier installation for users

**Medium Term (v0.3.0):**
1. **Background daemon mode** - Run as a service for continuous sync
2. **File watchers for auto-sync** - Automatic sync when OrcaSlicer saves changes
3. **CRON job support** - Scheduled syncs
4. **Selective sync (include/exclude patterns)** - Only sync specific files/folders
5. **Interactive conflict resolution** - Visual merge tool within TUI
6. **Standalone executables** - Already started with PyInstaller 

**Long Term (v1.0.0):**
1. **GUI application** - Desktop app for non-CLI users
2. **Plugin system** - Extensibility for custom workflows
3. **Advanced merge strategies** - Smart conflict resolution
4. **Cloud backup integration** - Beyond Git (S3, Dropbox, etc.)

## Recommended Priority

Based on the maturity of the project, I recommend focusing on:

### 1. Testing Infrastructure (Critical)
- Unit tests for config, git_ops, and CLI
- Integration tests for TUI workflows
- CI/CD pipeline for automated testing
- **Why**: Foundation for reliable software, catches regressions
- **Effort**: Medium-High
- **Impact**: High (enables confident iteration)

### 2. Dry-Run Mode (High Value, Low Effort)
- Add `--dry-run` flag to all commands
- Show what would change without executing
- Preview file operations before they happen
- **Why**: Helps users gain confidence, prevents mistakes
- **Effort**: Low-Medium
- **Impact**: High (user trust)

### 3. Configuration Validation (Prevents User Errors)
- Validate YAML structure on load
- Check that paths exist before operations
- Verify Git URLs are reachable
- Provide helpful error messages with suggestions
- **Why**: Better UX, fewer support issues
- **Effort**: Low-Medium
- **Impact**: Medium-High

### 4. Background Daemon & Auto-Sync (Most Requested Feature)
- **Background daemon mode** - Run OrcaSync as a service
- **File watchers** - Monitor OrcaSlicer directories for changes
- **CRON support** - Scheduled automatic syncs
- Auto-sync on file save with configurable debouncing
- TUI indicator for daemon/watcher status
- **Why**: Core user workflow improvement, "set it and forget it"
- **Effort**: Medium-High
- **Impact**: Very High (game-changer for daily use)

### 5. Selective Sync Patterns (Flexibility)
- Add `include`/`exclude` patterns to config
- Skip cache files, logs, temp files
- Per-profile pattern customization
- Common presets (e.g., "no-cache", "essentials-only")
- **Why**: Reduces sync overhead, more control
- **Effort**: Medium
- **Impact**: Medium-High

## Current State

**What's Working:**
- ✅ Full CLI functionality
- ✅ Interactive TUI with real-time logs
- ✅ Cross-platform support (Windows, macOS, Linux, WSL)
- ✅ Multi-profile configuration
- ✅ Git-based sync (push, pull, bidirectional)
- ✅ Platform-specific path detection
- ✅ Comprehensive documentation

**Known Gaps:**
- ❌ No automated tests
- ❌ No preview/dry-run capability
- ❌ No automatic sync on file changes
- ❌ No selective file sync
- ❌ Manual conflict resolution required
- ❌ Not yet on PyPI

## Implementation Suggestions

### Testing (v0.2.0)
```python
# tests/test_config.py
def test_config_loads_default_profile()
def test_platform_specific_paths()
def test_multi_profile_support()

# tests/test_git_ops.py
def test_sync_files()
def test_pull_changes()
def test_conflict_detection()

# tests/test_tui.py
def test_status_panel_renders()
def test_button_handlers()
```

### Dry-Run Mode (v0.2.0)
```yaml
# Add to config
dry_run: false

# CLI usage
orcasync push --dry-run
orcasync sync --dry-run

# Output
[DRY RUN] Would copy: profiles/user/machine/Ender-3.json
[DRY RUN] Would commit: 15 files changed
[DRY RUN] Would push to: origin/main
```

### Config Validation (v0.2.0)
```python
def validate_config(config: Dict) -> List[ValidationError]:
    errors = []
    
    # Check required fields
    if not config.get('repository_url'):
        errors.append(ValidationError("repository_url is required"))
    
    # Validate paths exist
    for path in config.get('paths', {}).get(platform.system(), {}).get('user_paths', []):
        if not Path(path).exists():
            errors.append(ValidationError(f"Path does not exist: {path}"))
    
    return errors
```

### Background Daemon Mode (v0.3.0)
```python
# orcasync/daemon.py
import daemon
import daemon.pidfile
from pathlib import Path
import logging
import time

class OrcaSyncDaemon:
    """Background daemon for continuous syncing."""
    
    def __init__(self, config_path: Path, profile: str = None):
        self.config = Config(config_path, profile)
        self.running = True
        self.sync_interval = self.config.data.get('daemon_sync_interval', 300)  # 5 min default
    
    def run(self):
        """Main daemon loop."""
        logger = logging.getLogger('orcasync.daemon')
        logger.info("OrcaSync daemon started")
        
        while self.running:
            try:
                # Perform sync
                self.sync()
                logger.info(f"Synced successfully, sleeping {self.sync_interval}s")
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Sync error: {e}")
                time.sleep(60)  # Wait 1 min on error
    
    def sync(self):
        """Execute sync operation."""
        git_mgr = GitManager(
            self.config.repository_path,
            self.config.repository_url,
            self.config.branch_name
        )
        git_mgr.init_repository()
        git_mgr.ensure_branch()
        
        # Pull then push
        git_mgr.pull()
        git_mgr.restore_files(self.config.sync_paths)
        copied = git_mgr.sync_files(self.config.sync_paths)
        if git_mgr.commit_changes():
            git_mgr.push()

# CLI commands
@main.command()
@click.option("--config", "-c", type=click.Path())
@click.option("--profile", "-p")
def start_daemon(config: str, profile: str):
    """Start OrcaSync daemon."""
    config_path = Path(config) if config else None
    pidfile_path = Path.home() / ".local" / "share" / "orcasync" / "daemon.pid"
    
    with daemon.DaemonContext(
        pidfile=daemon.pidfile.PIDLockFile(str(pidfile_path)),
        working_directory=str(Path.home()),
    ):
        daemon = OrcaSyncDaemon(config_path, profile)
        daemon.run()

@main.command()
def stop_daemon():
    """Stop OrcaSync daemon."""
    pidfile_path = Path.home() / ".local" / "share" / "orcasync" / "daemon.pid"
    if pidfile_path.exists():
        pid = int(pidfile_path.read_text())
        os.kill(pid, signal.SIGTERM)
        console.print("[green]✓ Daemon stopped[/green]")
    else:
        console.print("[yellow]No daemon running[/yellow]")
```

### CRON Job Support (v0.3.0)
```bash
# orcasync/cron_helper.py
def install_cron_job(interval: str = "hourly"):
    """Install cron job for automatic syncing."""
    # Generate crontab entry
    intervals = {
        "hourly": "0 * * * *",
        "daily": "0 0 * * *",
        "every-5-min": "*/5 * * * *",
        "every-15-min": "*/15 * * * *",
    }
    
    cron_schedule = intervals.get(interval, intervals["hourly"])
    cron_command = f"{cron_schedule} orcasync sync --quiet >> ~/.local/share/orcasync/cron.log 2>&1"
    
    # Add to crontab
    from crontab import CronTab
    cron = CronTab(user=True)
    job = cron.new(command='orcasync sync --quiet')
    job.setall(cron_schedule)
    job.set_comment('OrcaSync automatic sync')
    cron.write()
    
    return cron_command

# CLI command
@main.command()
@click.option("--interval", type=click.Choice(["hourly", "daily", "every-5-min", "every-15-min"]), default="hourly")
def install_cron(interval: str):
    """Install cron job for automatic syncing."""
    entry = install_cron_job(interval)
    console.print(f"[green]✓ Cron job installed: {interval}[/green]")
    console.print(f"  {entry}")

@main.command()
def uninstall_cron():
    """Remove OrcaSync cron job."""
    from crontab import CronTab
    cron = CronTab(user=True)
    cron.remove_all(comment='OrcaSync automatic sync')
    cron.write()
    console.print("[green]✓ Cron job removed[/green]")
```

### File Watchers (v0.3.0)
```python
# Using watchdog library
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ProfileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(('.json', '.info')):
            schedule_sync(delay=5)  # Debounce
```

### Selective Sync (v0.3.0)
```yaml
# Config additions
profiles:
  default:
    sync_patterns:
      include:
        - "**/*.json"
        - "**/*.info"
      exclude:
        - "**/cache/**"
        - "**/*.log"
        - "**/temp/**"
```

### Daemon & Automation Config (v0.3.0)
```yaml
profiles:
  default:
    repository_url: https://github.com/user/orca-profiles
    branch_name: main
    
    # Daemon settings
    daemon:
      enabled: false
      sync_interval: 300  # seconds (5 minutes)
      log_file: ~/.local/share/orcasync/daemon.log
      pid_file: ~/.local/share/orcasync/daemon.pid
    
    # Auto-sync with file watching
    auto_sync:
      enabled: false
      debounce_seconds: 5
      watch_on_tui_start: true
    
    # CRON scheduling
    cron:
      enabled: false
      schedule: "hourly"  # hourly, daily, every-5-min, every-15-min, custom
      custom_schedule: "*/30 * * * *"  # if schedule is "custom"
      quiet_mode: true
    
    paths:
      Darwin:
        user_paths:
          - /Users/you/Library/Application Support/OrcaSlicer/user
```

## Next Steps

### v0.2.0 Release (Weeks 1-4)
1. **Week 1-2**: Set up testing framework (pytest, fixtures, CI)
2. **Week 3**: Implement dry-run mode across all commands
3. **Week 4**: Add configuration validation & error recovery
4. **Week 4**: PyPI packaging and v0.2.0 release

### v0.3.0 Release (Weeks 5-10)
1. **Week 5-6**: Background daemon mode implementation
2. **Week 7**: CRON job support and scheduling
3. **Week 8**: File watchers and auto-sync
4. **Week 9**: Selective sync patterns
5. **Week 10**: Interactive conflict resolution in TUI
6. **Week 10**: v0.3.0 release with all automation features

## Success Metrics

### v0.2.0
- **Testing**: 80%+ code coverage
- **Dry-Run**: Zero breaking changes when enabled
- **Validation**: 50% reduction in user config errors
- **PyPI**: Successfully published and installable via `pip install orcasync`

### v0.3.0
- **Daemon Mode**: Runs reliably for 24+ hours without crashes
- **CRON Support**: Cross-platform cron installation (Linux/macOS/Windows Task Scheduler)
- **Auto-Sync**: < 10s latency from save to sync
- **Selective Sync**: Support for complex gitignore-style patterns
- **Resource Usage**: < 50MB memory, < 1% CPU when idle
