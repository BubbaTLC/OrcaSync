"""Shared pytest fixtures for OrcaSync tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def tmp_config_dir(tmp_path: Path, mocker) -> Generator[Path, None, None]:
    """Create a temporary configuration directory.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        mocker: pytest-mock's mocker fixture
        
    Yields:
        Path to temporary config directory
    """
    config_dir = tmp_path / ".config" / "orcasync"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock Path.home() to return our temp directory
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    
    yield config_dir
    

@pytest.fixture
def mock_orcaslicer_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a mock OrcaSlicer directory structure.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Yields:
        Path to mock OrcaSlicer directory
    """
    orca_dir = tmp_path / "OrcaSlicer"
    user_dir = orca_dir / "user"
    system_dir = orca_dir / "system"
    
    # Create directory structure
    user_dir.mkdir(parents=True, exist_ok=True)
    system_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some mock profile directories
    profiles_dir = user_dir / "default"
    profiles_dir.mkdir(exist_ok=True)
    
    (profiles_dir / "filament").mkdir(exist_ok=True)
    (profiles_dir / "machine").mkdir(exist_ok=True)
    (profiles_dir / "process").mkdir(exist_ok=True)
    
    # Create mock profile files
    (profiles_dir / "filament" / "PLA.json").write_text('{"name": "PLA"}')
    (profiles_dir / "machine" / "printer.json").write_text('{"name": "Printer"}')
    (profiles_dir / "process" / "default.json").write_text('{"name": "Default"}')
    
    yield orca_dir


@pytest.fixture
def mock_git_repo(tmp_path: Path, mocker) -> Generator[MagicMock, None, None]:
    """Create a mock GitPython repository.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        mocker: pytest-mock's mocker fixture
        
    Yields:
        MagicMock instance configured as a git repository
    """
    # Create a temporary git directory
    git_dir = tmp_path / "repo"
    git_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock repository
    mock_repo = MagicMock()
    mock_repo.working_dir = str(git_dir)
    mock_repo.bare = False
    mock_repo.is_dirty.return_value = False
    mock_repo.untracked_files = []
    
    # Mock git objects
    mock_repo.heads = []
    mock_repo.remotes = MagicMock()
    mock_repo.remote.return_value = MagicMock()
    
    # Mock git operations
    mock_repo.git.add = MagicMock()
    mock_repo.git.commit = MagicMock()
    mock_repo.git.push = MagicMock()
    mock_repo.git.pull = MagicMock()
    mock_repo.git.fetch = MagicMock()
    
    # Mock index
    mock_index = MagicMock()
    mock_repo.index = mock_index
    mock_index.commit.return_value = MagicMock()
    
    # Patch Repo class
    mock_repo_class = mocker.patch('git.Repo')
    mock_repo_class.return_value = mock_repo
    mock_repo_class.clone_from.return_value = mock_repo
    mock_repo_class.init.return_value = mock_repo
    
    yield mock_repo


@pytest.fixture
def sample_config_data() -> dict:
    """Provide sample configuration data for testing.
    
    Returns:
        Dictionary with sample configuration
    """
    return {
        "repository_url": "https://github.com/user/orca-profiles.git",
        "repository_name": "orca-profiles",
        "auto_commit": True,
        "commit_message_template": "Sync from {hostname} - {timestamp}",
        "default_profile": "default",
        "profiles": {
            "default": {
                "branch_name": "main",
                "paths": {
                    "Windows": {
                        "user_paths": [r"C:\Users\TestUser\AppData\Roaming\OrcaSlicer\user"],
                        "system_paths": []
                    },
                    "Darwin": {
                        "user_paths": ["/Users/testuser/Library/Application Support/OrcaSlicer/user"],
                        "system_paths": []
                    },
                    "Linux": {
                        "user_paths": ["/home/testuser/.config/OrcaSlicer/user"],
                        "system_paths": []
                    }
                }
            },
            "work": {
                "branch_name": "work-machine",
                "paths": {
                    "Windows": {
                        "user_paths": [r"C:\Users\WorkUser\AppData\Roaming\OrcaSlicer\user"],
                        "system_paths": []
                    },
                    "Darwin": {
                        "user_paths": ["/Users/workuser/Library/Application Support/OrcaSlicer/user"],
                        "system_paths": []
                    },
                    "Linux": {
                        "user_paths": ["/home/workuser/.config/OrcaSlicer/user"],
                        "system_paths": []
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_platform(mocker):
    """Fixture to easily mock platform.system() for cross-platform testing.
    
    Args:
        mocker: pytest-mock's mocker fixture
        
    Returns:
        Function that accepts a platform name and mocks platform.system()
    """
    def _set_platform(platform_name: str):
        """Set the platform for testing.
        
        Args:
            platform_name: One of 'Windows', 'Darwin', 'Linux'
        """
        mocker.patch('platform.system', return_value=platform_name)
    
    return _set_platform


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test.
    
    Args:
        monkeypatch: pytest's built-in monkeypatch fixture
    """
    # Clear potentially interfering environment variables
    env_vars_to_clear = ['APPDATA', 'LOCALAPPDATA', 'PROGRAMFILES', 'PROGRAMFILES(X86)']
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)
