"""Benchmark tests for sync operations performance."""

import pytest
from pathlib import Path
import tempfile
import shutil
from git import Repo

from orcasync.git_ops import GitManager


@pytest.fixture
def benchmark_git_manager(tmp_path):
    """Create a GitManager for benchmarking."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    # Initialize a bare repo as remote
    remote_path = tmp_path / "remote"
    remote_path.mkdir()
    Repo.init(remote_path, bare=True)
    
    # Create GitManager instance
    manager = GitManager(
        repo_path=repo_path,
        repo_url=str(remote_path),
        branch_name="benchmark-branch"
    )
    
    # Initialize repo
    manager.init_repository()
    
    return manager, tmp_path


def create_test_files(base_path: Path, num_files: int, nested: bool = True):
    """Create test files for benchmarking.
    
    Args:
        base_path: Base directory to create files in
        num_files: Number of files to create
        nested: Whether to create nested directory structure
    """
    base_path.mkdir(parents=True, exist_ok=True)
    
    if nested:
        # Create nested structure mimicking OrcaSlicer profiles
        subdirs = ["filament", "machine", "process"]
        files_per_dir = num_files // len(subdirs)
        
        for subdir in subdirs:
            subdir_path = base_path / subdir
            subdir_path.mkdir(exist_ok=True)
            
            for i in range(files_per_dir):
                # Create .json file
                json_file = subdir_path / f"profile_{i}.json"
                json_file.write_text('{"version": "1.0", "data": "test content"}')
                
                # Create .info file
                info_file = subdir_path / f"profile_{i}.info"
                info_file.write_text("Profile info content")
    else:
        # Create flat structure
        for i in range(num_files):
            file_path = base_path / f"file_{i}.txt"
            file_path.write_text(f"Test content {i}")


class TestSyncPerformance:
    """Benchmark tests for sync_files operations."""
    
    def test_sync_small_profile(self, benchmark, benchmark_git_manager):
        """Benchmark sync_files with small profile (100 files)."""
        manager, tmp_path = benchmark_git_manager
        
        # Create source directory with 100 files
        source_path = tmp_path / "small_profile"
        create_test_files(source_path, 100, nested=True)
        
        # Benchmark the sync operation
        result = benchmark(manager.sync_files, [source_path], "profiles")
        
        # Verify files were synced
        assert len(result) > 0
        assert len(result) >= 100  # At least 100 files synced
    
    def test_sync_medium_profile(self, benchmark, benchmark_git_manager):
        """Benchmark sync_files with medium profile (500 files)."""
        manager, tmp_path = benchmark_git_manager
        
        # Create source directory with 500 files
        source_path = tmp_path / "medium_profile"
        create_test_files(source_path, 500, nested=True)
        
        # Benchmark the sync operation
        result = benchmark(manager.sync_files, [source_path], "profiles")
        
        # Verify files were synced
        assert len(result) > 0
        assert len(result) >= 500
    
    def test_sync_large_profile(self, benchmark, benchmark_git_manager):
        """Benchmark sync_files with large profile (2000 files)."""
        manager, tmp_path = benchmark_git_manager
        
        # Create source directory with 2000 files
        source_path = tmp_path / "large_profile"
        create_test_files(source_path, 2000, nested=True)
        
        # Benchmark the sync operation
        result = benchmark(manager.sync_files, [source_path], "profiles")
        
        # Verify files were synced
        assert len(result) > 0
        assert len(result) >= 2000
    
    def test_sync_multiple_paths(self, benchmark, benchmark_git_manager):
        """Benchmark sync_files with multiple source paths (300 files each)."""
        manager, tmp_path = benchmark_git_manager
        
        # Create multiple source directories
        source_paths = []
        for i in range(3):
            source_path = tmp_path / f"source_{i}"
            create_test_files(source_path, 300, nested=True)
            source_paths.append(source_path)
        
        # Benchmark the sync operation
        result = benchmark(manager.sync_files, source_paths, "profiles")
        
        # Verify files were synced
        assert len(result) > 0
        assert len(result) >= 900  # 3 * 300 files


class TestCommitPerformance:
    """Benchmark tests for commit operations."""
    
    def test_commit_small_changes(self, benchmark, benchmark_git_manager):
        """Benchmark commit with small number of changes (100 files)."""
        manager, tmp_path = benchmark_git_manager
        
        # Create and sync files
        source_path = tmp_path / "small_profile"
        create_test_files(source_path, 100, nested=True)
        manager.sync_files([source_path], "profiles")
        
        # Benchmark the commit operation
        result = benchmark(
            manager.commit_changes,
            "Benchmark commit - small changes"
        )
        
        # Verify commit was created (should have files)
        assert result is not None
    
    def test_commit_medium_changes(self, benchmark, benchmark_git_manager):
        """Benchmark commit with medium number of changes (500 files)."""
        manager, tmp_path = benchmark_git_manager
        
        # Create and sync files
        source_path = tmp_path / "medium_profile"
        create_test_files(source_path, 500, nested=True)
        manager.sync_files([source_path], "profiles")
        
        # Benchmark the commit operation
        result = benchmark(
            manager.commit_changes,
            "Benchmark commit - medium changes"
        )
        
        # Verify commit was created
        assert result is not None
    
    def test_commit_large_changes(self, benchmark, benchmark_git_manager):
        """Benchmark commit with large number of changes (2000 files)."""
        manager, tmp_path = benchmark_git_manager
        
        # Create and sync files
        source_path = tmp_path / "large_profile"
        create_test_files(source_path, 2000, nested=True)
        manager.sync_files([source_path], "profiles")
        
        # Benchmark the commit operation
        result = benchmark(
            manager.commit_changes,
            "Benchmark commit - large changes"
        )
        
        # Verify commit was created
        assert result is not None


class TestRestorePerformance:
    """Benchmark tests for restore_files operations."""
    
    def test_restore_medium_profile(self, benchmark, benchmark_git_manager):
        """Benchmark restore_files with medium profile (500 files)."""
        manager, tmp_path = benchmark_git_manager
        
        # Create, sync, and commit files
        source_path = tmp_path / "medium_profile"
        create_test_files(source_path, 500, nested=True)
        manager.sync_files([source_path], "profiles")
        manager.commit_changes("Setup for restore benchmark")
        
        # Create target directory with same name structure
        target_base = tmp_path / "restored"
        target_base.mkdir()
        target_path = target_base / "medium_profile"  # Must match source name
        
        # Benchmark the restore operation
        result = benchmark(manager.restore_files, [target_path], "profiles")
        
        # Verify files were restored
        assert len(result) > 0
        assert len(result) >= 500
