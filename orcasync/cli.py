"""Command-line interface for OrcaSync."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .config import Config
from .git_ops import GitManager, GitSyncError


console = Console()


@click.group()
@click.version_option()
def main():
    """OrcaSync - Sync OrcaSlicer profiles using Git."""
    pass


@main.command()
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
@click.option("--profile", "-p", help="Profile name to use")
def init(config: Optional[str], profile: Optional[str]):
    """Initialize OrcaSync configuration and repository."""
    config_path = Path(config) if config else None
    cfg = Config(config_path, profile)
    
    # Check if already configured
    if cfg.config_path.exists():
        if not click.confirm(f"Config file already exists at {cfg.config_path}. Overwrite?"):
            console.print("[yellow]Initialization cancelled.[/yellow]")
            return
    
    # Interactive configuration
    console.print("[bold]OrcaSync Initialization[/bold]\n")
    
    # Discover OrcaSlicer paths
    console.print("[blue]Discovering OrcaSlicer installation...[/blue]")
    discovered = Config.discover_orcaslicer_paths()
    
    if discovered["user"] or discovered["system"]:
        console.print("[green]✓[/green] Found OrcaSlicer profiles:")
        if discovered["user"]:
            for path in discovered["user"]:
                console.print(f"  User:   {path}")
        if discovered["system"]:
            for path in discovered["system"]:
                console.print(f"  System: {path}")
        console.print()
    else:
        console.print("[yellow]⚠[/yellow] No OrcaSlicer profiles found in standard locations")
        console.print("  You can specify custom paths manually\n")
    
    repo_url = click.prompt("Git repository URL (leave empty for local-only)", default="", show_default=False)
    cfg.set("repository_url", repo_url)
    
    repo_name = click.prompt("Repository name", default=cfg.repository_name)
    cfg.set("repository_name", repo_name)
    
    # Ask about custom paths
    if click.confirm("Use custom OrcaSlicer profile paths?", default=False):
        user_path = click.prompt("User profile path", default=str(cfg.user_paths[0]) if cfg.user_paths else "")
        cfg.set("user_paths", [user_path])
    elif discovered["user"]:
        # Use discovered paths
        cfg.set("user_paths", [str(p) for p in discovered["user"]])
        if discovered["system"]:
            cfg.set("system_paths", [str(p) for p in discovered["system"]])
    
    # Save configuration
    cfg.save()
    console.print(f"[green]✓[/green] Configuration saved to {cfg.config_path}")
    
    # Initialize repository
    repo_path = Path.home() / ".local" / "share" / "orcasync" / cfg.repository_name
    
    try:
        git_mgr = GitManager(repo_path, repo_url, cfg.branch_name)
        git_mgr.init_repository()
        git_mgr.ensure_branch()
        
        console.print(f"[green]✓[/green] Repository initialized at {repo_path}")
        console.print(f"[green]✓[/green] Branch: {cfg.branch_name}")
        
    except GitSyncError as e:
        console.print(f"[red]✗[/red] Failed to initialize repository: {e}")
        sys.exit(1)
    
    console.print("\n[bold green]Initialization complete![/bold green]")
    console.print("Run 'orcasync push' to upload your profiles or 'orcasync pull' to download.")


@main.command()
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
@click.option("--profile", "-p", help="Profile name to use")
@click.option("--message", "-m", help="Commit message")
def push(config: Optional[str], profile: Optional[str], message: Optional[str]):
    """Push local OrcaSlicer profiles to the repository."""
    config_path = Path(config) if config else None
    cfg = Config(config_path, profile)
    
    if not cfg.repository_url and not click.confirm("No repository URL configured. Continue with local commit only?"):
        return
    
    repo_path = Path.home() / ".local" / "share" / "orcasync" / cfg.repository_name
    
    try:
        with console.status("[bold blue]Syncing profiles..."):
            git_mgr = GitManager(repo_path, cfg.repository_url, cfg.branch_name)
            git_mgr.init_repository()
            git_mgr.ensure_branch()
            
            # Sync files
            copied = git_mgr.sync_files(cfg.sync_paths)
            console.print(f"[green]✓[/green] Copied {len(copied)} files to repository")
            
            # Commit
            has_changes = git_mgr.commit_changes(message)
            if has_changes:
                console.print("[green]✓[/green] Changes committed")
            else:
                console.print("[yellow]No changes to commit[/yellow]")
                return
            
            # Push if remote configured
            if cfg.repository_url:
                git_mgr.push()
                console.print("[green]✓[/green] Pushed to remote repository")
        
        console.print("\n[bold green]Push complete![/bold green]")
        
    except GitSyncError as e:
        console.print(f"[red]✗[/red] Sync failed: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@main.command()
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
@click.option("--profile", "-p", help="Profile name to use")
def pull(config: Optional[str], profile: Optional[str]):
    """Pull OrcaSlicer profiles from the repository."""
    config_path = Path(config) if config else None
    cfg = Config(config_path, profile)
    
    if not cfg.repository_url:
        console.print("[red]✗[/red] No repository URL configured. Run 'orcasync init' first.")
        sys.exit(1)
    
    repo_path = Path.home() / ".local" / "share" / "orcasync" / cfg.repository_name
    
    try:
        with console.status("[bold blue]Pulling profiles..."):
            git_mgr = GitManager(repo_path, cfg.repository_url, cfg.branch_name)
            git_mgr.init_repository()
            git_mgr.ensure_branch()
            
            # Pull changes
            has_changes, changed_files = git_mgr.pull()
            
            if has_changes:
                console.print(f"[green]✓[/green] Pulled {len(changed_files)} changed files")
                
                # Restore files
                restored = git_mgr.restore_files(cfg.sync_paths)
                console.print(f"[green]✓[/green] Restored {len(restored)} files to OrcaSlicer")
            else:
                console.print("[yellow]No changes to pull[/yellow]")
        
        console.print("\n[bold green]Pull complete![/bold green]")
        
    except GitSyncError as e:
        console.print(f"[red]✗[/red] Sync failed: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


@main.command()
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
@click.option("--profile", "-p", help="Profile name to use")
def status(config: Optional[str], profile: Optional[str]):
    """Show OrcaSync status."""
    config_path = Path(config) if config else None
    cfg = Config(config_path, profile)
    
    # Configuration status
    table = Table(title="OrcaSync Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Config File", str(cfg.config_path))
    table.add_row("Active Profile", cfg.profile_name or cfg.data.get("default_profile") or "[dim]None (using global settings)[/dim]")
    table.add_row("Available Profiles", ", ".join(cfg.list_profiles()) or "[dim]None[/dim]")
    table.add_row("Repository URL", cfg.repository_url or "[dim]Not configured[/dim]")
    table.add_row("Branch Name", cfg.branch_name)
    table.add_row("User Paths", "\n".join(str(p) for p in cfg.user_paths))
    
    console.print(table)
    
    # Repository status
    repo_path = Path.home() / ".local" / "share" / "orcasync" / cfg.repository_name
    
    if repo_path.exists():
        try:
            git_mgr = GitManager(repo_path, cfg.repository_url, cfg.branch_name)
            git_mgr.init_repository()
            
            git_status = git_mgr.get_status()
            
            repo_table = Table(title="Repository Status")
            repo_table.add_column("Property", style="cyan")
            repo_table.add_column("Value")
            
            repo_table.add_row("Repository Path", str(repo_path))
            repo_table.add_row("Current Branch", git_status.get("branch", "N/A"))
            repo_table.add_row("Has Changes", "Yes" if git_status.get("dirty") else "No")
            repo_table.add_row("Untracked Files", str(git_status.get("untracked_files", 0)))
            repo_table.add_row("Remote Configured", "Yes" if git_status.get("has_remote") else "No")
            
            console.print(repo_table)
            
        except GitSyncError as e:
            console.print(f"[yellow]Repository status unavailable: {e}[/yellow]")
    else:
        console.print("\n[yellow]Repository not initialized. Run 'orcasync init'.[/yellow]")


@main.command()
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
@click.option("--profile", "-p", help="Profile name to use")
def config_path(config: Optional[str], profile: Optional[str]):
    """Show the path to the configuration file."""
    config_path_obj = Path(config) if config else None
    cfg = Config(config_path_obj, profile)
    console.print(str(cfg.config_path))


if __name__ == "__main__":
    main()
