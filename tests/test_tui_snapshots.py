"""
Snapshot tests for OrcaSync TUI components.

Tests use pytest-textual-snapshot plugin for capturing SVG screenshots
and ensuring UI consistency across changes.

Run tests:
    uv run pytest tests/test_tui_snapshots.py              # Run tests
    uv run pytest --snapshot-update                         # Update snapshots after changes

Snapshots are stored in tests/__snapshots__/ directory.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from orcasync.config import Config
from orcasync.tui import (
    OrcaSyncApp,
    StatusPanel,
    CompactLogView,
    InitDialog,
)


# =============================================================================
# CompactLogView Tests
# =============================================================================

class TestCompactLogViewSnapshots:
    """Snapshot tests for CompactLogView widget."""
    
    def test_log_view_empty(self, snap_compare):
        """Test empty log view."""
        from textual.app import App, ComposeResult
        from textual.widgets import Header
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield Header()
                yield CompactLogView()
        
        assert snap_compare(TestApp())
    
    def test_log_view_single_message(self, snap_compare):
        """Test log view with single message."""
        from textual.app import App, ComposeResult
        from textual.widgets import Header
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield Header()
                yield CompactLogView()
            
            def on_mount(self) -> None:
                log = self.query_one(CompactLogView)
                log.add_log("[green]OrcaSync TUI started[/green]")
        
        assert snap_compare(TestApp())
    
    def test_log_view_multiple_messages(self, snap_compare):
        """Test log view with multiple messages."""
        from textual.app import App, ComposeResult
        from textual.widgets import Header
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield Header()
                yield CompactLogView()
            
            def on_mount(self) -> None:
                log = self.query_one(CompactLogView)
                log.add_log("[green]OrcaSync TUI started[/green]")
                log.add_log("[blue]Initializing repository...[/blue]")
                log.add_log("[green]✓ Repository initialized[/green]")
                log.add_log("[yellow]⚠ Warning: No remote configured[/yellow]")
                log.add_log("[red]✗ Error: Connection failed[/red]")
        
        assert snap_compare(TestApp())
    
    def test_log_view_100_plus_messages(self, snap_compare):
        """Test log view with 100+ messages (should truncate to last 100)."""
        from textual.app import App, ComposeResult
        from textual.widgets import Header
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield Header()
                yield CompactLogView()
            
            def on_mount(self) -> None:
                log = self.query_one(CompactLogView)
                # Add 120 messages, should keep only last 100
                for i in range(120):
                    log.add_log(f"[dim]Log message {i}[/dim]")
        
        assert snap_compare(TestApp(), terminal_size=(100, 50))
    
    def test_log_view_after_clear(self, snap_compare):
        """Test log view after clearing messages."""
        from textual.app import App, ComposeResult
        from textual.widgets import Header
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield Header()
                yield CompactLogView()
            
            def on_mount(self) -> None:
                log = self.query_one(CompactLogView)
                log.add_log("[green]Message 1[/green]")
                log.add_log("[blue]Message 2[/blue]")
                log.clear_logs()
        
        assert snap_compare(TestApp())
    
    def test_log_view_rich_formatting(self, snap_compare):
        """Test log view with various rich formatting."""
        from textual.app import App, ComposeResult
        from textual.widgets import Header
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield Header()
                yield CompactLogView()
            
            def on_mount(self) -> None:
                log = self.query_one(CompactLogView)
                log.add_log("[bold cyan]═══ Status Report ═══[/bold cyan]")
                log.add_log("[green]✓[/green] Operation successful")
                log.add_log("[yellow]⚠[/yellow] [italic]Warning message[/italic]")
                log.add_log("[red]✗[/red] [bold]Error occurred[/bold]")
                log.add_log("[dim]Debug: Additional info[/dim]")
        
        assert snap_compare(TestApp())


# =============================================================================
# InitDialog Tests
# =============================================================================

class TestInitDialogSnapshots:
    """Snapshot tests for InitDialog screen."""
    
    def test_init_dialog_auto_detected_paths(self, mocker, snap_compare):
        """Test InitDialog with auto-detected OrcaSlicer paths."""
        # Mock discover_orcaslicer_paths
        mocker.patch.object(
            Config,
            'discover_orcaslicer_paths',
            return_value={
                'user': [Path('/home/user/.config/OrcaSlicer/user')],
                'system': []
            }
        )
        
        from textual.app import App, ComposeResult
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                config = MagicMock()
                config.repository_name = "orcaslicer-profiles"
                config.branch_name = "main"
                config.config_path = Path("/tmp/config.yaml")
                app_instance = MagicMock()
                yield InitDialog(config, app_instance)
        
        assert snap_compare(TestApp(), terminal_size=(100, 30))
    
    def test_init_dialog_manual_path_entry(self, mocker, snap_compare):
        """Test InitDialog when OrcaSlicer path not auto-detected."""
        # Mock no auto-detection
        mocker.patch.object(
            Config,
            'discover_orcaslicer_paths',
            return_value={'user': [], 'system': []}
        )
        
        from textual.app import App, ComposeResult
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                config = MagicMock()
                config.repository_name = "my-profiles"
                config.branch_name = "develop"
                config.config_path = Path("/tmp/config.yaml")
                app_instance = MagicMock()
                yield InitDialog(config, app_instance)
        
        assert snap_compare(TestApp(), terminal_size=(100, 35))
    
    def test_init_dialog_filled_form(self, mocker, snap_compare):
        """Test InitDialog with filled form fields."""
        mocker.patch.object(
            Config,
            'discover_orcaslicer_paths',
            return_value={'user': [], 'system': []}
        )
        
        from textual.app import App, ComposeResult
        
        class TestApp(App):
            def compose(self) -> ComposeResult:
                config = MagicMock()
                config.repository_name = "custom-repo"
                config.branch_name = "main"
                config.config_path = Path("/tmp/config.yaml")
                app_instance = MagicMock()
                yield InitDialog(config, app_instance)
        
        async def fill_form(pilot):
            await pilot.pause()
            # Fill in the form
            repo_url = pilot.app.query_one("#repo-url")
            repo_url.value = "https://github.com/user/custom-repo"
            
            custom_path_inputs = pilot.app.query("#custom-path")
            if custom_path_inputs:
                custom_path_inputs[0].value = "/custom/orcaslicer/path"
            
            await pilot.pause()
        
        assert snap_compare(TestApp(), terminal_size=(100, 35), run_before=fill_form)


# =============================================================================
# Main OrcaSyncApp Tests
# =============================================================================

class TestOrcaSyncAppSnapshots:
    """Snapshot tests for main OrcaSyncApp."""
    
    def test_app_initial_state(self, mocker, snap_compare, tmp_path):
        """Test main app screen initial rendering."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        # Create minimal config
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        
        config_path.write_text("""repository_url: ""
repository_name: "orcaslicer-profiles"
branch_name: "main"
user_paths: []
""")
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 40)
        )
    
    def test_app_with_configured_repo(self, mocker, snap_compare, tmp_path):
        """Test app screen with configured repository."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        # Create config and OrcaSlicer dir
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        
        user_path = tmp_path / "OrcaSlicer" / "user"
        user_path.mkdir(parents=True)
        
        config_path.write_text(f"""repository_url: "https://github.com/user/profiles"
repository_name: "profiles"
branch_name: "main"
user_paths:
  - "{user_path}"
""")
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 40)
        )
    
    def test_app_with_logs(self, mocker, snap_compare, tmp_path):
        """Test app screen after adding log messages."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_name: "profiles"\nbranch_name: "main"')
        
        async def add_logs(pilot):
            await pilot.pause()
            log_view = pilot.app.get_compact_view()
            log_view.add_log("[blue]Testing log messages...[/blue]")
            log_view.add_log("[green]✓ Operation successful[/green]")
            log_view.add_log("[yellow]⚠ Warning encountered[/yellow]")
            await pilot.pause()
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 40),
            run_before=add_logs
        )
    
    def test_app_navigation(self, mocker, snap_compare, tmp_path):
        """Test app keyboard navigation between buttons."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_name: "profiles"\nbranch_name: "main"')
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 40),
            press=["right", "right"]
        )
    
    def test_app_refresh_action(self, mocker, snap_compare, tmp_path):
        """Test app after refresh action."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_url: "https://github.com/user/profiles"\nbranch_name: "main"')
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 40),
            press=["r"]
        )
    
    def test_app_clear_logs_action(self, mocker, snap_compare, tmp_path):
        """Test app after clearing logs."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_name: "profiles"\nbranch_name: "main"')
        
        async def add_then_clear(pilot):
            await pilot.pause()
            log = pilot.app.get_compact_view()
            log.add_log("[green]Test message 1[/green]")
            log.add_log("[blue]Test message 2[/blue]")
            await pilot.pause()
        
        # Add logs first, then press 'c' to clear
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 40),
            run_before=add_then_clear,
            press=["c"]
        )
    
    def test_app_init_dialog_shown(self, mocker, snap_compare, tmp_path):
        """Test app when init dialog is shown."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        mocker.patch.object(
            Config,
            'discover_orcaslicer_paths',
            return_value={'user': [], 'system': []}
        )
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_name: "profiles"\nbranch_name: "main"')
        
        # Press 'i' to show init dialog
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 45),
            press=["i"]
        )


# =============================================================================
# Responsive Layout Tests
# =============================================================================

class TestResponsiveLayout:
    """Test app rendering at different terminal sizes."""
    
    def test_small_terminal(self, mocker, snap_compare, tmp_path):
        """Test app in small terminal (80x24)."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_name: "profiles"\nbranch_name: "main"')
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(80, 24)
        )
    
    def test_medium_terminal(self, mocker, snap_compare, tmp_path):
        """Test app in medium terminal (100x30)."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_name: "profiles"\nbranch_name: "main"')
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(100, 30)
        )
    
    def test_large_terminal(self, mocker, snap_compare, tmp_path):
        """Test app in large terminal (150x50)."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_name: "profiles"\nbranch_name: "main"')
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(150, 50)
        )
    
    def test_wide_terminal(self, mocker, snap_compare, tmp_path):
        """Test app in wide terminal (200x30)."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        config_path.write_text('repository_name: "profiles"\nbranch_name: "main"')
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(200, 30)
        )


# =============================================================================
# Edge Cases and Error States
# =============================================================================

class TestAppEdgeCases:
    """Test edge cases and error states in the app."""
    
    def test_app_long_repo_url(self, mocker, snap_compare, tmp_path):
        """Test app with very long repository URL."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        
        long_url = "https://github.com/very-long-organization-name/extremely-long-repository-name-that-exceeds-normal-limits"
        config_path.write_text(f"""repository_url: "{long_url}"
repository_name: "extremely-long-repository-name-that-exceeds-normal-limits"
branch_name: "feature/very-long-branch-name-for-testing"
""")
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 40)
        )
    
    def test_app_unicode_in_paths(self, mocker, snap_compare, tmp_path):
        """Test app with unicode characters in paths."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        
        unicode_path = tmp_path / "OrcaSlicer" / "用户" / "配置"
        unicode_path.mkdir(parents=True)
        
        config_path.write_text(f"""repository_url: "https://github.com/用户/配置文件"
repository_name: "配置文件"
branch_name: "主分支"
user_paths:
  - "{unicode_path}"
""")
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 40)
        )
    
    def test_app_many_paths(self, mocker, snap_compare, tmp_path):
        """Test app with many configured paths."""
        mocker.patch('pathlib.Path.home', return_value=tmp_path)
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_path = config_dir / "orcasync.yaml"
        
        # Create multiple paths
        paths = []
        for i in range(10):
            path = tmp_path / f"OrcaSlicer/user{i}"
            path.mkdir(parents=True)
            paths.append(str(path))
        
        paths_yaml = "\n".join(f'  - "{p}"' for p in paths)
        config_path.write_text(f"""repository_url: "https://github.com/user/profiles"
repository_name: "profiles"
branch_name: "main"
user_paths:
{paths_yaml}
""")
        
        assert snap_compare(
            OrcaSyncApp(config_path=config_path),
            terminal_size=(120, 50)
        )
