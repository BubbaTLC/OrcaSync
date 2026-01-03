"""Git operations for OrcaSync."""

import shutil
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import platform

import git
from git import Repo


class GitSyncError(Exception):
    """Base exception for Git sync operations."""
    pass


class GitManager:
    """Manages Git operations for profile syncing."""
    
    def __init__(self, repo_path: Path, repo_url: str, branch_name: str):
        """Initialize Git manager.
        
        Args:
            repo_path: Local path for the Git repository
            repo_url: Remote repository URL
            branch_name: Branch name to use for this machine
        """
        self.repo_path = repo_path
        self.repo_url = repo_url
        self.branch_name = branch_name
        self.repo: Optional[Repo] = None
    
    def init_repository(self) -> Repo:
        """Initialize or open the Git repository."""
        if self.repo_path.exists():
            try:
                self.repo = Repo(self.repo_path)
                return self.repo
            except git.InvalidGitRepositoryError:
                raise GitSyncError(f"{self.repo_path} exists but is not a valid Git repository")
        
        # Clone repository if URL is provided
        if self.repo_url:
            try:
                self.repo = Repo.clone_from(self.repo_url, self.repo_path)
                return self.repo
            except git.GitCommandError as e:
                raise GitSyncError(f"Failed to clone repository: {e}")
        
        # Initialize new repository
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.repo = Repo.init(self.repo_path)
        
        # Create initial commit if repository is empty
        if not self.repo.heads:
            # Create a README
            readme_path = self.repo_path / "README.md"
            readme_path.write_text("# OrcaSync Profiles\n\nThis repository contains OrcaSlicer profile synchronization data.\n")
            self.repo.index.add(["README.md"])
            self.repo.index.commit("Initial commit")
        
        # Add remote if URL provided
        if self.repo_url:
            try:
                self.repo.create_remote("origin", self.repo_url)
            except git.GitCommandError:
                pass  # Remote already exists
        
        return self.repo
    
    def ensure_branch(self) -> None:
        """Ensure the branch for this machine exists and is checked out."""
        if not self.repo:
            raise GitSyncError("Repository not initialized")
        
        # Create branch if it doesn't exist
        if self.branch_name not in self.repo.heads:
            # Check if branch exists on remote
            try:
                if "origin" in self.repo.remotes:
                    origin = self.repo.remotes.origin
                    origin.fetch()
                    
                    remote_branch = f"origin/{self.branch_name}"
                    if remote_branch in [ref.name for ref in origin.refs]:
                        # Create local branch tracking remote
                        self.repo.create_head(self.branch_name, remote_branch)
                        self.repo.heads[self.branch_name].set_tracking_branch(origin.refs[self.branch_name])
                    else:
                        # Create new local branch
                        self.repo.create_head(self.branch_name, 'HEAD')
                else:
                    # No remote, create local branch
                    self.repo.create_head(self.branch_name, 'HEAD')
            except git.GitCommandError:
                # Create local branch if fetch fails
                self.repo.create_head(self.branch_name, 'HEAD')
        
        # Checkout the branch
        self.repo.heads[self.branch_name].checkout()
    
    def sync_files(self, source_paths: List[Path], target_subdir: str = "profiles") -> List[Path]:
        """Copy files from source paths to repository.
        
        Args:
            source_paths: List of source directories to sync
            target_subdir: Subdirectory within repo to sync to
            
        Returns:
            List of files that were copied
        """
        if not self.repo:
            raise GitSyncError("Repository not initialized")
        
        target_path = self.repo_path / target_subdir
        target_path.mkdir(parents=True, exist_ok=True)
        
        copied_files = []
        
        for source_path in source_paths:
            if not source_path.exists():
                continue
            
            # Get relative name for this source path
            source_name = source_path.name
            dest_path = target_path / source_name
            
            # Copy entire directory tree
            if dest_path.exists():
                shutil.rmtree(dest_path)
            
            shutil.copytree(source_path, dest_path)
            
            # Track copied files
            for file_path in dest_path.rglob("*"):
                if file_path.is_file():
                    copied_files.append(file_path.relative_to(self.repo_path))
        
        return copied_files
    
    def restore_files(self, target_paths: List[Path], source_subdir: str = "profiles") -> List[Path]:
        """Restore files from repository to target paths.
        
        Args:
            target_paths: List of target directories to restore to
            source_subdir: Subdirectory within repo to restore from
            
        Returns:
            List of files that were restored
        """
        if not self.repo:
            raise GitSyncError("Repository not initialized")
        
        source_path = self.repo_path / source_subdir
        if not source_path.exists():
            return []
        
        restored_files = []
        
        for target_path in target_paths:
            # Get corresponding source directory
            source_name = target_path.name
            src_dir = source_path / source_name
            
            if not src_dir.exists():
                continue
            
            # Ensure target parent exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            if target_path.exists():
                shutil.rmtree(target_path)
            
            shutil.copytree(src_dir, target_path)
            
            # Track restored files
            for file_path in target_path.rglob("*"):
                if file_path.is_file():
                    restored_files.append(file_path)
        
        return restored_files
    
    def commit_changes(self, message: Optional[str] = None) -> bool:
        """Commit changes to the repository.
        
        Args:
            message: Commit message (auto-generated if None)
            
        Returns:
            True if changes were committed, False if nothing to commit
        """
        if not self.repo:
            raise GitSyncError("Repository not initialized")
        
        # Stage all changes
        self.repo.git.add(A=True)
        
        # Check if there are changes to commit
        if not self.repo.is_dirty() and not self.repo.untracked_files:
            return False
        
        # Generate commit message if not provided
        if not message:
            hostname = platform.node()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Sync from {hostname} - {timestamp}"
        
        # Commit
        self.repo.index.commit(message)
        return True
    
    def push(self) -> None:
        """Push changes to remote repository."""
        if not self.repo:
            raise GitSyncError("Repository not initialized")
        
        if "origin" not in self.repo.remotes:
            raise GitSyncError("No remote 'origin' configured")
        
        origin = self.repo.remotes.origin
        
        try:
            # For first push or when tracking not set, use set_upstream
            # This creates the branch on remote if it doesn't exist
            current_branch = self.repo.active_branch
            tracking_branch = current_branch.tracking_branch()
            
            if tracking_branch is None:
                # First push - set upstream
                push_info = origin.push(refspec=f'{self.branch_name}:{self.branch_name}', set_upstream=True)
            else:
                # Regular push
                push_info = origin.push(self.branch_name)
            
            # Check push results for errors
            for info in push_info:
                if info.flags & info.ERROR:
                    raise GitSyncError(f"Push failed: {info.summary}")
                if info.flags & info.REJECTED:
                    raise GitSyncError(f"Push rejected: {info.summary}. Try pulling first or check if remote branch exists.")
                if info.flags & info.REMOTE_REJECTED:
                    raise GitSyncError(f"Remote rejected push: {info.summary}")
                if info.flags & info.REMOTE_FAILURE:
                    raise GitSyncError(f"Remote failure: {info.summary}")
                    
        except git.GitCommandError as e:
            # Provide helpful error messages for common issues
            error_msg = str(e)
            if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                raise GitSyncError(f"Authentication failed. Check your Git credentials for {self.repo_url}")
            elif "Repository not found" in error_msg:
                raise GitSyncError(f"Repository not found: {self.repo_url}. Make sure it exists and you have access.")
            elif "non-fast-forward" in error_msg:
                raise GitSyncError("Push rejected (non-fast-forward). Run 'orcasync pull' first to merge remote changes.")
            else:
                raise GitSyncError(f"Failed to push: {e}")
    
    def pull(self) -> Tuple[bool, List[str]]:
        """Pull changes from remote repository.
        
        Returns:
            Tuple of (has_changes, list of changed files)
        """
        if not self.repo:
            raise GitSyncError("Repository not initialized")
        
        if "origin" not in self.repo.remotes:
            raise GitSyncError("No remote 'origin' configured")
        
        origin = self.repo.remotes.origin
        
        # Get current commit
        old_commit = self.repo.head.commit
        
        try:
            origin.pull(self.branch_name)
        except git.GitCommandError as e:
            raise GitSyncError(f"Failed to pull: {e}")
        
        # Get new commit
        new_commit = self.repo.head.commit
        
        # Check if there were changes
        if old_commit == new_commit:
            return False, []
        
        # Get list of changed files
        changed_files = [
            item.a_path for item in old_commit.diff(new_commit)
        ]
        
        return True, changed_files
    
    def get_status(self) -> dict:
        """Get repository status.
        
        Returns:
            Dictionary with status information
        """
        if not self.repo:
            return {"initialized": False}
        
        return {
            "initialized": True,
            "branch": self.repo.active_branch.name,
            "dirty": self.repo.is_dirty(),
            "untracked_files": len(self.repo.untracked_files),
            "has_remote": "origin" in self.repo.remotes,
        }
