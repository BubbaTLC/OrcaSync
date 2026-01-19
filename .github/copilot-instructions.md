# OrcaSync - Copilot Instructions

## Project Overview

OrcaSync is a cross-platform CLI/TUI tool for synchronizing OrcaSlicer 3D printing profiles via Git. It features dual interfaces: a **Click-based CLI** for automation and a **Textual-based TUI** for interactive use. Default command (`orcasync` alone) launches TUI; subcommands use CLI.

**Key Technologies:** Python 3.10+, GitPython, Click, Rich, Textual, PyInstaller

## Architecture

### Module Structure
- **[orcasync/cli.py](orcasync/cli.py)** - Click commands (`init`, `push`, `pull`, `sync`, `status`). Main entrypoint that dispatches to TUI when no subcommand given.
- **[orcasync/tui.py](orcasync/tui.py)** - Textual app with Screen-based dialogs. Uses `@work` decorator for async Git operations to prevent UI blocking.
- **[orcasync/config.py](orcasync/config.py)** - Profile-based config with platform-specific path resolution. Uses `discover_orcaslicer_paths()` for cross-platform auto-detection.
- **[orcasync/git_ops.py](orcasync/git_ops.py)** - GitManager class handles repo init, branch management, sync operations. Platform-specific credential helpers configured in `_configure_credentials()`.

### Profile System Pattern
Config supports per-machine branches AND multi-profile workflows. Active profile determines:
- Which branch to use (`branch_name` from profile config)
- Platform-specific paths (Windows/Darwin/Linux keys in profile's paths config)
- Each profile in `profiles:` dict contains `branch_name`, `paths` with platform sub-keys

Example from [config.py#L170-180](orcasync/config.py#L170-L180):
```python
paths_config[platform_name] = {
    "user_paths": [str(paths["user"])],
    "system_paths": []  # Disabled by default
}
```

### Cross-Platform Path Handling
**Critical Pattern:** Never hardcode paths. Always use `Config.DEFAULT_PATHS` dict indexed by `platform.system()` return values (`"Windows"`, `"Darwin"`, `"Linux"`). See [config.py#L15-29](orcasync/config.py#L15-L29).

macOS uses `~/Library/Application Support/OrcaSlicer/`, Linux uses `~/.config/OrcaSlicer/`, Windows uses `%APPDATA%\OrcaSlicer\`.

## Development Workflows

### Running Locally
```bash
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
orcasync  # Launches TUI
orcasync push  # Uses CLI
```

### Building Executables
Uses PyInstaller with [orcasync.spec](orcasync.spec):
```bash
uv pip install pyinstaller
pyinstaller --clean orcasync.spec
dist/orcasync --version
```

**Platform-specific notes:**
- macOS requires ad-hoc code signing: `codesign -s - --force --deep dist/orcasync`
- Spec file includes `hiddenimports` for GitPython deps (gitdb, smmap) and all Textual modules
- GitHub Actions builds all platforms on tag push (see [.github/workflows/build.yml](.github/workflows/build.yml))

### Testing
No automated tests yet (see [project_plan.md#L95](project_plan.md#L95) - planned for v0.2.0). Quick TUI verification via [test_tui.py](test_tui.py):
```bash
python test_tui.py
```

## Code Conventions

### Error Handling
- Git operations raise `GitSyncError` (see [git_ops.py#L13](git_ops.py#L13))
- CLI catches and prints with Rich console: `console.print(f"[red]✗[/red] {error}")`
- TUI uses Workers with `.is_success` checks, logs errors to CompactLogView

### Rich Output Styling
**Pattern:** Use semantic colors consistently:
- `[green]✓[/green]` - Success
- `[red]✗[/red]` - Error  
- `[yellow]⚠[/yellow]` - Warning
- `[blue]...[/blue]` - Info/status
- `[dim]...[/dim]` - Muted text

See [cli.py#L95-110](orcasync/cli.py#L95-L110) for status display example.

### Textual Screen Pattern
Dialogs are Screen subclasses with CSS in `DEFAULT_CSS` class variable. Use `@on(Button.Pressed)` decorator for event handlers. Call `self.app.pop_screen()` to close, optionally passing result. See [tui.py#L142-200](orcasync/tui.py#L142-L200) for InitDialog pattern.

### Async Git Operations in TUI
**Critical:** Never block TUI event loop with Git ops. Use `@work` decorator:
```python
@work(exclusive=True, thread=True)
async def _perform_push(self) -> dict:
    # Long-running git operation
    git_mgr.push()
    return {"status": "success"}
```
Check worker state in callback: `if worker.state == WorkerState.SUCCESS:`

## Git Integration Details

### Credential Helpers
Platform-specific helpers configured in `_configure_credentials()`:
- macOS: `osxkeychain`
- Windows: `wincred`
- Linux: System default (not overridden)

**Important:** Pull strategy set to `rebase` to avoid divergent branch errors on per-machine branches.

### Branch Strategy
Two patterns supported:
1. **Per-machine:** Each machine has own branch (`hostname-main` by default)
2. **Shared:** Multiple machines use same branch (manual config)

See [git_ops.py#L117-145](orcasync/git_ops.py#L117-L145) for `ensure_branch()` logic.

## Common Tasks

### Adding a New CLI Command
1. Add Click command decorated function in [cli.py](orcasync/cli.py)
2. Load config: `cfg = Config(config_path, profile)`
3. Initialize GitManager: `GitManager(repo_path, cfg.repository_url, cfg.branch_name)`
4. Use Rich console for output
5. Raise SystemExit on errors

### Adding a TUI Feature
1. Create Screen class with compose() method
2. Define bindings in App.BINDINGS
3. Use `@on` decorators for event handlers
4. Long operations use `@work` with Workers
5. Update CompactLogView for user feedback

### Supporting New OrcaSlicer Paths
Update `Config.DEFAULT_PATHS` dict in [config.py](orcasync/config.py). Add platform key if needed. Extend `discover_orcaslicer_paths()` search locations.

## External Dependencies

- **GitPython:** All Git operations. Use `Repo` class, not subprocess.
- **Click:** CLI framework. Use `@click.group()` for main, `@click.command()` for subcommands.
- **Rich:** Terminal output formatting. Use Console() for printing.
- **Textual:** TUI framework. App/Screen/Widget architecture.
- **PyYAML:** Config file I/O. Use `yaml.safe_load()`/`yaml.safe_dump()`.

## Files You'll Edit Often

- [orcasync/cli.py](orcasync/cli.py) - Adding CLI commands
- [orcasync/tui.py](orcasync/tui.py) - TUI features/screens
- [orcasync/config.py](orcasync/config.py) - Config schema changes
- [orcasync/git_ops.py](orcasync/git_ops.py) - Git operation changes
- [pyproject.toml](pyproject.toml) - Dependencies, version, metadata
- [orcasync.spec](orcasync.spec) - Build configuration
