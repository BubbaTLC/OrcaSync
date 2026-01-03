"""Configuration management for OrcaSync."""

import os
import platform
from pathlib import Path
from typing import Dict, List, Optional
import yaml


class Config:
    """Manages OrcaSync configuration."""
    
    DEFAULT_CONFIG_NAME = "orcasync-config.yaml"
    
    # Default Orca Slicer profile paths by platform
    DEFAULT_PATHS = {
        "Windows": {
            "user": Path(os.environ.get("APPDATA", "")) / "OrcaSlicer" / "user",
            "system": Path(os.environ.get("APPDATA", "")) / "OrcaSlicer" / "system",
        },
        "Darwin": {  # macOS
            "user": Path.home() / "Library" / "Application Support" / "OrcaSlicer" / "user",
            "system": Path.home() / "Library" / "Application Support" / "OrcaSlicer" / "system",
        },
        "Linux": {
            "user": Path.home() / ".config" / "OrcaSlicer" / "user",
            "system": Path.home() / ".config" / "OrcaSlicer" / "system",
        },
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config file. If None, looks in default locations.
        """
        self.config_path = config_path or self._find_config_file()
        self.data = self._load_config()
    
    def _find_config_file(self) -> Path:
        """Find configuration file in default locations."""
        # Check current directory
        current_dir = Path.cwd() / self.DEFAULT_CONFIG_NAME
        if current_dir.exists():
            return current_dir
        
        # Check user config directory
        config_dir = Path.home() / ".config" / "orcasync"
        config_file = config_dir / self.DEFAULT_CONFIG_NAME
        
        return config_file
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to load config from {self.config_path}: {e}")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        system = platform.system()
        default_paths = self.DEFAULT_PATHS.get(system, self.DEFAULT_PATHS["Linux"])
        
        return {
            "repository_url": "",
            "repository_name": "orca-profiles",
            "branch_prefix": "",
            "branch_postfix": "",
            "user_paths": [str(default_paths["user"])],
            "system_paths": [str(default_paths["system"])],
            "sync_interval": 0,  # 0 = manual only
            "auto_commit": True,
            "commit_message_template": "Sync from {hostname} - {timestamp}",
        }
    
    def save(self):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.data.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value."""
        self.data[key] = value
    
    @property
    def repository_url(self) -> str:
        """Get repository URL."""
        return self.data.get("repository_url", "")
    
    @property
    def repository_name(self) -> str:
        """Get repository name."""
        return self.data.get("repository_name", "orca-profiles")
    
    @property
    def branch_name(self) -> str:
        """Get current branch name."""
        hostname = platform.node()
        prefix = self.data.get("branch_prefix", "")
        postfix = self.data.get("branch_postfix", "")
        return f"{prefix}{hostname}{postfix}"
    
    @property
    def user_paths(self) -> List[Path]:
        """Get user profile paths."""
        paths = self.data.get("user_paths", [])
        return [Path(p) for p in paths]
    
    @property
    def system_paths(self) -> List[Path]:
        """Get system profile paths."""
        paths = self.data.get("system_paths", [])
        return [Path(p) for p in paths]
    
    @property
    def sync_paths(self) -> List[Path]:
        """Get all paths to sync."""
        return self.user_paths + self.system_paths
