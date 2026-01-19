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
    
    @staticmethod
    def discover_orcaslicer_paths() -> Dict[str, List[Path]]:
        """Automatically discover OrcaSlicer installation paths.
        
        Returns:
            Dict with 'user' and 'system' keys containing lists of discovered paths.
        """
        discovered = {"user": [], "system": []}
        system = platform.system()
        
        # Get standard paths for the current platform
        default_paths = Config.DEFAULT_PATHS.get(system, Config.DEFAULT_PATHS["Linux"])
        
        # Check standard locations
        for path_type in ["user", "system"]:
            standard_path = default_paths[path_type]
            if standard_path.exists() and standard_path.is_dir():
                discovered[path_type].append(standard_path)
        
        # Additional search locations based on platform
        search_locations = []
        
        if system == "Windows":
            # Check local appdata, program files, portable installations
            search_locations.extend([
                Path(os.environ.get("LOCALAPPDATA", "")) / "OrcaSlicer",
                Path(os.environ.get("PROGRAMFILES", "")) / "OrcaSlicer",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "OrcaSlicer",
                Path.home() / "OrcaSlicer",
            ])
        elif system == "Darwin":
            # Check additional macOS locations
            search_locations.extend([
                Path.home() / ".config" / "OrcaSlicer",
                Path("/Applications/OrcaSlicer.app/Contents/Resources") / "profiles",
            ])
        elif system == "Linux":
            # Check additional Linux locations
            search_locations.extend([
                Path.home() / ".local" / "share" / "OrcaSlicer",
                Path.home() / "OrcaSlicer",
            ])
        
        # Search additional locations
        for base_path in search_locations:
            if not base_path.exists():
                continue
            
            for path_type in ["user", "system"]:
                candidate = base_path / path_type
                if candidate.exists() and candidate.is_dir():
                    # Avoid duplicates
                    if candidate not in discovered[path_type]:
                        discovered[path_type].append(candidate)
        
        return discovered
    
    def __init__(self, config_path: Optional[Path] = None, profile: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config file. If None, looks in default locations.
            profile: Profile name to use. If None, uses default profile or global settings.
        """
        self.config_path = config_path or self._find_config_file()
        self.profile_name = profile
        self.data = self._load_config()
        self.active_profile = self._load_profile()
    
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
        
        # Try to discover actual paths
        discovered = self.discover_orcaslicer_paths()
        
        # Use discovered paths if available, otherwise fall back to defaults
        # Only sync user paths by default (system paths disabled)
        user_paths = [str(p) for p in discovered["user"]] if discovered["user"] else [str(default_paths["user"])]
        
        # Create platform-specific path configurations
        paths_config = {}
        for platform_name, paths in self.DEFAULT_PATHS.items():
            paths_config[platform_name] = {
                "user_paths": [str(paths["user"])],
                "system_paths": []  # Disabled by default
            }
        
        return {
            "repository_url": "",
            "repository_name": "orca-profiles",
            "auto_commit": True,
            "commit_message_template": "Sync from {hostname} - {timestamp}",
            "default_profile": "default",  # Use 'default' profile by default
            "profiles": {
                "default": {
                    "branch_name": "main",
                    "paths": paths_config
                }
            }
        }
    
    def _load_profile(self) -> Dict:
        """Load and merge profile with base configuration.
        
        Returns:
            Merged configuration dict with profile settings applied.
        """
        # Determine which profile to use
        profile_name = self.profile_name or self.data.get("default_profile")
        
        # Start with base config (excluding profiles)
        base_config = {k: v for k, v in self.data.items() if k not in ["profiles", "default_profile"]}
        
        # If no profile specified, return base config
        if not profile_name:
            return base_config
        
        # Get profile configuration
        profiles = self.data.get("profiles", {})
        if profile_name not in profiles:
            raise ValueError(f"Profile '{profile_name}' not found in config")
        
        profile_config = profiles[profile_name]
        
        # Merge profile with base (profile overrides base)
        merged = base_config.copy()
        
        # Handle platform-specific paths if present
        current_platform = platform.system()
        
        if "paths" in profile_config:
            platform_paths = profile_config["paths"].get(current_platform, {})
            if platform_paths:
                # Use platform-specific paths
                if "user_paths" in platform_paths:
                    merged["user_paths"] = platform_paths["user_paths"]
                if "system_paths" in platform_paths:
                    merged["system_paths"] = platform_paths["system_paths"]
            # Remove the paths key from profile_config before merging other settings
            profile_settings = {k: v for k, v in profile_config.items() if k != "paths"}
        else:
            profile_settings = profile_config
        
        # Merge remaining profile settings
        merged.update(profile_settings)
        
        return merged
    
    def save(self):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)
    
    def get(self, key: str, default=None):
        """Get configuration value from active profile."""
        return self.active_profile.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value."""
        self.data[key] = value
    
    @property
    def repository_url(self) -> str:
        """Get repository URL."""
        return self.active_profile.get("repository_url", "")
    
    @property
    def repository_name(self) -> str:
        """Get repository name."""
        return self.active_profile.get("repository_name", "orca-profiles")
    
    @property
    def branch_name(self) -> str:
        """Get current branch name."""
        # Check if profile has a custom branch_name
        if "branch_name" in self.active_profile:
            return self.active_profile["branch_name"]
        
        # Otherwise construct from prefix/postfix and hostname
        hostname = platform.node()
        prefix = self.active_profile.get("branch_prefix", "")
        postfix = self.active_profile.get("branch_postfix", "")
        return f"{prefix}{hostname}{postfix}"
    
    @property
    def user_paths(self) -> List[Path]:
        """Get user profile paths."""
        paths = self.active_profile.get("user_paths", [])
        return [Path(p) for p in paths]
    
    @property
    def system_paths(self) -> List[Path]:
        """Get system profile paths."""
        paths = self.active_profile.get("system_paths", [])
        return [Path(p) for p in paths]
    
    @property
    def sync_paths(self) -> List[Path]:
        """Get all paths to sync."""
        return self.user_paths + self.system_paths
    
    def list_profiles(self) -> List[str]:
        """List available profile names."""
        return list(self.data.get("profiles", {}).keys())
