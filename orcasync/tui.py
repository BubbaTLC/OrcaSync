"""Textual TUI for OrcaSync."""

import sys
from pathlib import Path
from typing import Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, Input, Label, Rule, Select
from textual.worker import Worker, WorkerState

from .config import Config
from .git_ops import GitManager, GitSyncError


class StatusPanel(Static):
    """Display current configuration and repository status."""
    
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
    
    def compose(self) -> ComposeResult:
        yield Static(self.render_status(), id="status-content")
    
    def render_status(self) -> str:
        """Render the status information."""
        cfg = self.config
        
        # Build status text
        lines = ["[bold cyan]═══ OrcaSync Status ═══[/bold cyan]\n"]
        
        # Configuration
        active_profile = cfg.profile_name or cfg.data.get("default_profile", "default")
        lines.append(f"[yellow]Profile:[/yellow] {active_profile}")
        lines.append(f"[yellow]Config:[/yellow] {cfg.config_path}")
        lines.append(f"[yellow]Repository:[/yellow] {cfg.repository_url or '[dim]Not configured[/dim]'}")
        lines.append(f"[yellow]Branch:[/yellow] {cfg.branch_name}")
        
        # OrcaSlicer paths
        lines.append("\n[bold cyan]Profile Paths[/bold cyan]")
        if cfg.user_paths:
            for user_path in cfg.user_paths:
                exists = user_path.exists()
                status = "[green]✓[/green]" if exists else "[red]✗[/red]"
                lines.append(f"  {status} {user_path}")
        else:
            lines.append("  [dim]No paths configured[/dim]")
        
        # Repository status
        lines.append("\n[bold cyan]Repository[/bold cyan]")
        repo_path = Path.home() / ".local" / "share" / "orcasync" / cfg.repository_name
        
        if repo_path.exists():
            try:
                git_mgr = GitManager(repo_path, cfg.repository_url, cfg.branch_name)
                git_mgr.init_repository()
                git_status = git_mgr.get_status()
                
                lines.append(f"  [yellow]Branch:[/yellow] {git_status.get('branch', 'N/A')}")
                dirty = git_status.get('dirty', False)
                lines.append(f"  [yellow]Status:[/yellow] {'[yellow]Uncommitted changes[/yellow]' if dirty else '[green]Clean[/green]'}")
                
                # Count synced files
                synced_files = sum(
                    1 for f in repo_path.rglob("*") 
                    if f.is_file() 
                    and ".git" not in f.parts 
                    and not any(part.startswith(".") for part in f.parts[len(repo_path.parts):])
                    and f.name != "README.md"
                )
                lines.append(f"  [yellow]Files:[/yellow] {synced_files}")
                
            except GitSyncError:
                lines.append("  [yellow]⚠ Unable to read repository status[/yellow]")
        else:
            lines.append("  [yellow]⚠ Not initialized - Run Init first[/yellow]")
        
        return "\n".join(lines)
    
    def refresh_status(self) -> None:
        """Refresh the status display."""
        content = self.query_one("#status-content", Static)
        content.update(self.render_status())


class CompactLogView(Static):
    """Compact log display showing recent messages above footer."""
    
    DEFAULT_CSS = """
    CompactLogView {
        height: auto;
        padding: 0 1;
    }
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.recent_logs: list[str] = []
    
    def add_log(self, message: str) -> None:
        """Add a log message to the compact view."""
        self.recent_logs.append(message)
        # Keep only last 100 logs
        if len(self.recent_logs) > 100:
            self.recent_logs = self.recent_logs[-100:]
        self.update("\n".join(self.recent_logs))
    
    def clear_logs(self) -> None:
        """Clear the compact log view."""
        self.recent_logs.clear()
        self.update("")


class InitDialog(Screen):
    """Dialog for initializing OrcaSync configuration."""
    
    DEFAULT_CSS = """
    InitDialog {
        align: center middle;
    }
    
    InitDialog > Container {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    
    InitDialog Label {
        margin: 1 0;
    }
    
    InitDialog Input {
        margin: 0 0 1 0;
    }
    
    InitDialog Button {
        margin: 1 1 0 0;
    }
    """
    
    def __init__(self, config: Config, app_instance: 'OrcaSyncApp') -> None:
        super().__init__()
        self.config = config
        self.app_instance = app_instance
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Static("[bold cyan]Initialize OrcaSync Configuration[/bold cyan]\n")
            
            yield Label("Git Repository URL (leave empty for local-only):")
            yield Input(placeholder="https://github.com/user/repo", id="repo-url")
            
            yield Label("Repository Name:")
            yield Input(value=self.config.repository_name, id="repo-name")
            
            yield Label("Branch Name:")
            yield Input(value=self.config.branch_name, id="branch-name")
            
            # Check for discovered paths
            discovered = Config.discover_orcaslicer_paths()
            if discovered["user"]:
                yield Label(f"[green]✓[/green] Found OrcaSlicer at: {discovered['user'][0]}")
            else:
                yield Label("[yellow]⚠[/yellow] OrcaSlicer path not auto-detected")
                yield Label("Custom OrcaSlicer Profile Path:")
                yield Input(placeholder="/path/to/OrcaSlicer/user", id="custom-path")
            
            with Horizontal():
                yield Button("Save & Initialize", variant="primary", id="save-init")
                yield Button("Cancel", variant="default", id="cancel-init")
    
    @on(Button.Pressed, "#save-init")
    def handle_save(self) -> None:
        """Handle save button press."""
        repo_url_input = self.query_one("#repo-url", Input)
        repo_name_input = self.query_one("#repo-name", Input)
        branch_name_input = self.query_one("#branch-name", Input)
        
        repo_url = repo_url_input.value.strip()
        repo_name = repo_name_input.value.strip()
        branch_name = branch_name_input.value.strip()
        
        # Check for custom path
        custom_path_inputs = self.query("#custom-path")
        custom_path = None
        if custom_path_inputs:
            custom_path = custom_path_inputs[0].value.strip()
        
        self.config.set("repository_url", repo_url if repo_url else "")
        self.config.set("repository_name", repo_name)
        self.config.set("branch_name", branch_name)
        
        # Set paths
        discovered = Config.discover_orcaslicer_paths()
        if discovered["user"]:
            self.config.set("user_paths", [str(p) for p in discovered["user"]])
            if discovered["system"]:
                self.config.set("system_paths", [str(p) for p in discovered["system"]])
        elif custom_path:
            self.config.set("user_paths", [custom_path])
        
        self.config.save()
        self.app_instance.get_compact_view().add_log(f"[green]✓ Configuration saved to {self.config.config_path}[/green]")
        
        # Initialize repository
        self.app_instance.initialize_repository()
        
        self.app.pop_screen()
    
    @on(Button.Pressed, "#cancel-init")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.app.pop_screen()


class OrcaSyncApp(App[None]):
    """A Textual TUI for OrcaSync."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #status-panel {
        width: 100%;
        height: 3fr;
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
        overflow-y: auto;
    }
    
    #menu-container {
        width: 100%;
        height: auto;
        align: center middle;
    }
    
    #log-container {
        width: 100%;
        height: 7fr;
        border: solid $primary-darken-1;
        background: $surface-darken-1;
        margin-top: 1;
    }
    
    #menu-grid {
        width: auto;
        height: auto;
        padding: 1;
    }
    
    #menu-grid > Horizontal {
        width: auto;
        height: auto;
        margin-bottom: 1;
    }
    
    #menu-grid Button {
        min-width: 20;
        margin: 0 1 1 1;
    }
    
    Button {
        width: auto;
    }
    
    Button:focus {
        text-style: bold;
        border: heavy $accent;
        background: $accent-darken-2;
    }
    
    #log-panel {
        width: 100%;
        margin-top: 1;
    }
    
    .dialog-container {
        align: center middle;
        width: 100%;
        height: 100%;
    }
    """
    
    BINDINGS = [
        Binding("i", "init", "Init", priority=True),
        Binding("p", "push", "Push", priority=True),
        Binding("P", "pull", "Pull", priority=True),
        Binding("s", "sync", "Sync", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("c", "clear_logs", "Clear Logs", priority=True),
        Binding("q", "quit", "Quit", priority=True),
        Binding("down,right", "focus_next", "Next", show=False),
        Binding("up,left", "focus_previous", "Previous", show=False),
    ]
    
    def __init__(self, config_path: Optional[Path] = None, profile: Optional[str] = None):
        super().__init__()
        self.title = "OrcaSync"
        self.sub_title = "Git-based OrcaSlicer Profile Sync"
        self.config = Config(config_path, profile)
        self.repo_path = Path.home() / ".local" / "share" / "orcasync" / self.config.repository_name
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        with Container(id="main-container"):
            # Status panel at top
            with Container(id="status-panel"):
                yield StatusPanel(self.config)
            
            # Menu buttons
            with Container(id="menu-container"):
                with Vertical(id="menu-grid"):
                    yield Static("[bold]Main Menu[/bold] (Use arrow keys or hotkeys)", id="menu-title")
                    with Horizontal():
                        yield Button("Init", id="btn-init", variant="default")
                        yield Button("Push", id="btn-push", variant="default")
                        yield Button("Pull", id="btn-pull", variant="default")
                    with Horizontal():
                        yield Button("Sync", id="btn-sync", variant="default")
                        yield Button("Refresh", id="btn-refresh", variant="default")
                        yield Button("Clear Logs", id="btn-clear", variant="default")
        
        # Scrollable log view above footer
        with VerticalScroll(id="log-container"):
            yield CompactLogView()
        yield Footer()
    
    def on_mount(self) -> None:
        """Handle app mount."""
        compact_view = self.get_compact_view()
        compact_view.add_log("[green]OrcaSync TUI started[/green]")
        compact_view.add_log("Use buttons or keyboard shortcuts to interact")
        # Set focus to first button
        self.query_one("#btn-init", Button).focus()
    
    def get_status_panel(self) -> StatusPanel:
        """Get the status panel widget."""
        return self.query_one(StatusPanel)
    
    def get_compact_view(self) -> CompactLogView:
        """Get the compact log view widget."""
        return self.query_one(CompactLogView)
    
    def action_refresh(self) -> None:
        """Refresh the status display."""
        self.get_status_panel().refresh_status()
        self.get_compact_view().add_log("[blue]Status refreshed[/blue]")
    
    def action_clear_logs(self) -> None:
        """Clear the log panel."""
        self.get_compact_view().clear_logs()
    
    def action_init(self) -> None:
        """Show init dialog."""
        self.show_init_dialog()
    
    def action_push(self) -> None:
        """Push profiles to repository."""
        self.push_profiles()
    
    def action_pull(self) -> None:
        """Pull profiles from repository."""
        self.pull_profiles()
    
    def action_sync(self) -> None:
        """Sync profiles (pull + push)."""
        self.sync_profiles()
    
    @on(Button.Pressed, "#btn-init")
    def handle_init_button(self) -> None:
        """Handle init button press."""
        self.show_init_dialog()
    
    @on(Button.Pressed, "#btn-push")
    def handle_push_button(self) -> None:
        """Handle push button press."""
        self.push_profiles()
    
    @on(Button.Pressed, "#btn-pull")
    def handle_pull_button(self) -> None:
        """Handle pull button press."""
        self.pull_profiles()
    
    @on(Button.Pressed, "#btn-sync")
    def handle_sync_button(self) -> None:
        """Handle sync button press."""
        self.sync_profiles()
    
    @on(Button.Pressed, "#btn-refresh")
    def handle_refresh_button(self) -> None:
        """Handle refresh button press."""
        self.action_refresh()
    
    @on(Button.Pressed, "#btn-clear")
    def handle_clear_button(self) -> None:
        """Handle clear logs button press."""
        self.action_clear_logs()
    
    def show_init_dialog(self) -> None:
        """Show the initialization dialog."""
        dialog = InitDialog(self.config, self)
        self.push_screen(dialog)
    
    @work(exclusive=True, thread=True)
    def initialize_repository(self) -> None:
        """Initialize the git repository."""
        log = self.get_compact_view()
        
        try:
            log.add_log("[blue]Initializing repository...[/blue]")
            git_mgr = GitManager(self.repo_path, self.config.repository_url, self.config.branch_name)
            git_mgr.init_repository()
            git_mgr.ensure_branch()
            
            log.add_log(f"[green]✓ Repository initialized at {self.repo_path}[/green]")
            log.add_log(f"[green]✓ Branch: {self.config.branch_name}[/green]")
            log.add_log("[bold green]Initialization complete![/bold green]")
            
            # Refresh status
            self.call_from_thread(self.get_status_panel().refresh_status)
            
        except GitSyncError as e:
            log.add_log(f"[red]✗ Failed to initialize repository: {e}[/red]")
        except Exception as e:
            log.add_log(f"[red]✗ Unexpected error: {e}[/red]")
    
    @work(exclusive=True, thread=True)
    def push_profiles(self) -> None:
        """Push profiles to the repository."""
        log = self.get_compact_view()
        
        if not self.config.repository_url:
            log.add_log("[yellow]⚠ No repository URL configured. Will commit locally only.[/yellow]")
        
        try:
            log.add_log("[blue]Pushing profiles...[/blue]")
            git_mgr = GitManager(self.repo_path, self.config.repository_url, self.config.branch_name)
            git_mgr.init_repository()
            git_mgr.ensure_branch()
            
            # Sync files
            copied = git_mgr.sync_files(self.config.sync_paths)
            log.add_log(f"[green]✓ Copied {len(copied)} files to repository[/green]")
            
            # Commit
            has_changes = git_mgr.commit_changes()
            if has_changes:
                log.add_log("[green]✓ Changes committed[/green]")
            else:
                log.add_log("[yellow]No changes to commit[/yellow]")
            
            # Push to remote if configured
            if self.config.repository_url and has_changes:
                try:
                    git_mgr.push()
                    log.add_log("[green]✓ Pushed to remote repository[/green]")
                except GitSyncError as e:
                    log.add_log(f"[yellow]⚠ Push to remote failed: {e}[/yellow]")
                    log.add_log("[dim]Changes committed locally but not pushed to remote[/dim]")
            
            log.add_log("[bold green]Push complete![/bold green]")
            
            # Refresh status
            self.call_from_thread(self.get_status_panel().refresh_status)
            
        except GitSyncError as e:
            log.add_log(f"[red]✗ Push failed: {e}[/red]")
        except Exception as e:
            log.add_log(f"[red]✗ Unexpected error: {e}[/red]")
    
    @work(exclusive=True, thread=True)
    def pull_profiles(self) -> None:
        """Pull profiles from the repository."""
        log = self.get_compact_view()
        
        if not self.config.repository_url:
            log.add_log("[red]✗ No repository URL configured. Run Init first.[/red]")
            return
        
        try:
            log.add_log("[blue]Pulling profiles...[/blue]")
            git_mgr = GitManager(self.repo_path, self.config.repository_url, self.config.branch_name)
            git_mgr.init_repository()
            git_mgr.ensure_branch()
            
            # Pull changes
            has_changes, changed_files = git_mgr.pull()
            
            if has_changes:
                log.add_log(f"[green]✓ Pulled {len(changed_files)} changed files[/green]")
                
                # Restore files
                restored = git_mgr.restore_files(self.config.sync_paths)
                log.add_log(f"[green]✓ Restored {len(restored)} files to OrcaSlicer[/green]")
            else:
                log.add_log("[yellow]No changes to pull[/yellow]")
            
            log.add_log("[bold green]Pull complete![/bold green]")
            
            # Refresh status
            self.call_from_thread(self.get_status_panel().refresh_status)
            
        except GitSyncError as e:
            log.add_log(f"[red]✗ Pull failed: {e}[/red]")
        except Exception as e:
            log.add_log(f"[red]✗ Unexpected error: {e}[/red]")
    
    @work(exclusive=True, thread=True)
    def sync_profiles(self) -> None:
        """Sync profiles (pull then push)."""
        log = self.get_compact_view()
        
        if not self.config.repository_url:
            log.add_log("[red]✗ No repository URL configured. Run Init first.[/red]")
            return
        
        try:
            git_mgr = GitManager(self.repo_path, self.config.repository_url, self.config.branch_name)
            git_mgr.init_repository()
            git_mgr.ensure_branch()
            
            # Step 1: Fetch
            log.add_log("[bold blue]Step 1/3: Fetching from remote...[/bold blue]")
            if "origin" in git_mgr.repo.remotes:
                origin = git_mgr.repo.remotes.origin
                fetch_info = origin.fetch()
                log.add_log("[green]✓ Fetched latest changes from remote[/green]")
            else:
                log.add_log("[yellow]⚠ No remote configured, skipping fetch[/yellow]")
            
            # Step 2: Pull
            log.add_log("[bold blue]Step 2/3: Pulling changes...[/bold blue]")
            
            # Commit local changes before pulling
            if git_mgr.repo.is_dirty() or git_mgr.repo.untracked_files:
                git_mgr.repo.git.add(A=True)
                git_mgr.commit_changes("Pre-sync commit")
                log.add_log("[blue]ℹ Committed local repository changes before pull[/blue]")
            
            has_changes, changed_files = git_mgr.pull()
            
            if has_changes:
                log.add_log(f"[green]✓ Pulled {len(changed_files)} changed files[/green]")
                restored = git_mgr.restore_files(self.config.sync_paths)
                log.add_log(f"[green]✓ Restored {len(restored)} files to OrcaSlicer[/green]")
            else:
                log.add_log("[blue]ℹ No remote changes to pull[/blue]")
            
            # Step 3: Push
            log.add_log("[bold blue]Step 3/3: Pushing local changes...[/bold blue]")
            
            # Sync files
            copied = git_mgr.sync_files(self.config.sync_paths)
            log.add_log(f"[green]✓ Copied {len(copied)} files to repository[/green]")
            
            # Commit
            has_local_changes = git_mgr.commit_changes()
            if has_local_changes:
                log.add_log("[green]✓ Local changes committed[/green]")
            
            # Push
            try:
                if git_mgr.repo.active_branch.tracking_branch():
                    commits_ahead = list(git_mgr.repo.iter_commits(
                        f'{git_mgr.repo.active_branch.tracking_branch().name}..{git_mgr.repo.active_branch.name}'
                    ))
                    if commits_ahead:
                        git_mgr.push()
                        log.add_log(f"[green]✓ Pushed {len(commits_ahead)} commit(s) to remote[/green]")
                    elif has_local_changes:
                        git_mgr.push()
                        log.add_log("[green]✓ Pushed to remote repository[/green]")
                    else:
                        log.add_log("[blue]ℹ No commits to push[/blue]")
                else:
                    if has_local_changes:
                        git_mgr.push()
                        log.add_log("[green]✓ Pushed to remote repository[/green]")
            except Exception as e:
                log.add_log(f"[yellow]⚠ Could not push: {e}[/yellow]")
            
            log.add_log("[bold green]✓ Sync complete![/bold green]")
            
            # Refresh status
            self.call_from_thread(self.get_status_panel().refresh_status)
            
        except GitSyncError as e:
            log.add_log(f"[red]✗ Sync failed: {e}[/red]")
        except Exception as e:
            log.add_log(f"[red]✗ Unexpected error: {e}[/red]")


def run_tui(config_path: Optional[Path] = None, profile: Optional[str] = None) -> None:
    """Run the Textual TUI application."""
    app = OrcaSyncApp(config_path, profile)
    app.run()
