"""Unit tests for Config module."""

import os
from pathlib import Path
import pytest
import yaml

from orcasync.config import Config


class TestDiscoverOrcaSlicerPaths:
    """Test discover_orcaslicer_paths() static method."""

    def test_discover_windows_standard_paths(self, mocker, tmp_path):
        """Test discovery on Windows with standard APPDATA location."""
        mocker.patch("platform.system", return_value="Windows")

        # Create mock Windows paths
        appdata = tmp_path / "AppData" / "Roaming"
        orca_user = appdata / "OrcaSlicer" / "user"
        orca_system = appdata / "OrcaSlicer" / "system"
        orca_user.mkdir(parents=True)
        orca_system.mkdir(parents=True)

        mocker.patch.dict(os.environ, {"APPDATA": str(appdata)}, clear=False)

        # Mock DEFAULT_PATHS to use temp paths
        mock_default_paths = {
            "Windows": {
                "user": orca_user,
                "system": orca_system,
            },
            "Darwin": Config.DEFAULT_PATHS["Darwin"],
            "Linux": Config.DEFAULT_PATHS["Linux"],
        }
        mocker.patch.object(Config, "DEFAULT_PATHS", mock_default_paths)

        result = Config.discover_orcaslicer_paths()

        assert len(result["user"]) == 1
        assert len(result["system"]) == 1
        assert result["user"][0] == orca_user
        assert result["system"][0] == orca_system

    def test_discover_windows_additional_locations(self, mocker, tmp_path):
        """Test discovery on Windows with additional search locations."""
        mocker.patch("platform.system", return_value="Windows")

        # Create paths in additional locations
        localappdata = tmp_path / "Local"
        orca_user = localappdata / "OrcaSlicer" / "user"
        orca_user.mkdir(parents=True)

        mocker.patch.dict(
            os.environ,
            {"APPDATA": str(tmp_path / "nonexistent"), "LOCALAPPDATA": str(localappdata)},
        )

        result = Config.discover_orcaslicer_paths()

        assert len(result["user"]) >= 1
        assert orca_user in result["user"]

    def test_discover_macos_standard_paths(self, mocker, tmp_path):
        """Test discovery on macOS with standard Library location."""
        mocker.patch("platform.system", return_value="Darwin")

        # Create mock macOS paths
        library = tmp_path / "Library" / "Application Support" / "OrcaSlicer"
        user_path = library / "user"
        system_path = library / "system"
        user_path.mkdir(parents=True)
        system_path.mkdir(parents=True)

        # Mock DEFAULT_PATHS to use temp paths
        mock_default_paths = {
            "Windows": Config.DEFAULT_PATHS["Windows"],
            "Darwin": {
                "user": user_path,
                "system": system_path,
            },
            "Linux": Config.DEFAULT_PATHS["Linux"],
        }
        mocker.patch.object(Config, "DEFAULT_PATHS", mock_default_paths)

        result = Config.discover_orcaslicer_paths()

        assert len(result["user"]) == 1
        assert len(result["system"]) == 1
        assert result["user"][0] == user_path
        assert result["system"][0] == system_path

    def test_discover_macos_additional_locations(self, mocker, tmp_path):
        """Test discovery on macOS with additional search locations."""
        mocker.patch("platform.system", return_value="Darwin")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        # Create path in .config
        config_path = tmp_path / ".config" / "OrcaSlicer" / "user"
        config_path.mkdir(parents=True)

        result = Config.discover_orcaslicer_paths()

        assert config_path in result["user"]

    def test_discover_linux_standard_paths(self, mocker, tmp_path):
        """Test discovery on Linux with standard .config location."""
        mocker.patch("platform.system", return_value="Linux")

        # Create mock Linux paths
        config = tmp_path / ".config" / "OrcaSlicer"
        user_path = config / "user"
        system_path = config / "system"
        user_path.mkdir(parents=True)
        system_path.mkdir(parents=True)

        # Mock DEFAULT_PATHS to use temp paths
        mock_default_paths = {
            "Windows": Config.DEFAULT_PATHS["Windows"],
            "Darwin": Config.DEFAULT_PATHS["Darwin"],
            "Linux": {
                "user": user_path,
                "system": system_path,
            },
        }
        mocker.patch.object(Config, "DEFAULT_PATHS", mock_default_paths)

        result = Config.discover_orcaslicer_paths()

        assert len(result["user"]) == 1
        assert len(result["system"]) == 1
        assert result["user"][0] == user_path
        assert result["system"][0] == system_path

    def test_discover_linux_additional_locations(self, mocker, tmp_path):
        """Test discovery on Linux with additional search locations."""
        mocker.patch("platform.system", return_value="Linux")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        # Create path in .local/share
        local_path = tmp_path / ".local" / "share" / "OrcaSlicer" / "user"
        local_path.mkdir(parents=True)

        result = Config.discover_orcaslicer_paths()

        assert local_path in result["user"]

    def test_discover_no_duplicates(self, mocker, tmp_path):
        """Test that discovered paths contain no duplicates."""
        mocker.patch("platform.system", return_value="Linux")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        # Create overlapping paths
        config_path = tmp_path / ".config" / "OrcaSlicer" / "user"
        config_path.mkdir(parents=True)

        result = Config.discover_orcaslicer_paths()

        # Check no duplicates in user paths
        assert len(result["user"]) == len(set(result["user"]))
        assert len(result["system"]) == len(set(result["system"]))

    def test_discover_nonexistent_paths(self, mocker, tmp_path):
        """Test discovery when no OrcaSlicer paths exist."""
        mocker.patch("platform.system", return_value="Linux")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        result = Config.discover_orcaslicer_paths()

        assert result["user"] == []
        assert result["system"] == []

    def test_discover_unknown_platform(self, mocker, tmp_path):
        """Test discovery falls back to Linux defaults for unknown platforms."""
        mocker.patch("platform.system", return_value="UnknownOS")

        # Create Linux-style paths
        config_path = tmp_path / ".config" / "OrcaSlicer" / "user"
        config_path.mkdir(parents=True)

        # Mock DEFAULT_PATHS - unknown platform should use Linux defaults
        mock_default_paths = {
            "Windows": Config.DEFAULT_PATHS["Windows"],
            "Darwin": Config.DEFAULT_PATHS["Darwin"],
            "Linux": {
                "user": config_path,
                "system": tmp_path / ".config" / "OrcaSlicer" / "system",
            },
        }
        mocker.patch.object(Config, "DEFAULT_PATHS", mock_default_paths)

        result = Config.discover_orcaslicer_paths()

        assert config_path in result["user"]


class TestConfigInitialization:
    """Test Config initialization and file loading."""

    def test_init_with_explicit_path(self, tmp_path):
        """Test initialization with explicit config path."""
        config_path = tmp_path / "custom-config.yaml"
        config_path.write_text(
            yaml.dump(
                {"repository_url": "https://github.com/user/repo", "repository_name": "test-repo"}
            )
        )

        config = Config(config_path=config_path)

        assert config.config_path == config_path
        assert config.data["repository_url"] == "https://github.com/user/repo"

    def test_init_finds_config_in_current_dir(self, tmp_path, mocker):
        """Test initialization finds config in current directory."""
        config_path = tmp_path / Config.DEFAULT_CONFIG_NAME
        config_path.write_text(yaml.dump({"repository_url": "http://example.com"}))

        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        config = Config()

        assert config.config_path == config_path
        assert config.data["repository_url"] == "http://example.com"

    def test_init_finds_config_in_user_config_dir(self, tmp_path, mocker):
        """Test initialization finds config in ~/.config/orcasync/."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path / "elsewhere")

        config_dir = tmp_path / ".config" / "orcasync"
        config_dir.mkdir(parents=True)
        config_path = config_dir / Config.DEFAULT_CONFIG_NAME
        config_path.write_text(yaml.dump({"repository_name": "found-config"}))

        config = Config()

        assert config.config_path == config_path

    def test_init_with_profile_name(self, tmp_path):
        """Test initialization with specific profile name."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "default_profile": "default",
                    "profiles": {
                        "default": {"branch_name": "main"},
                        "custom": {"branch_name": "custom-branch"},
                    },
                }
            )
        )

        config = Config(config_path=config_path, profile="custom")

        assert config.profile_name == "custom"
        assert config.active_profile["branch_name"] == "custom-branch"

    def test_init_uses_default_profile(self, tmp_path):
        """Test initialization uses default_profile when profile not specified."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "default_profile": "myprofile",
                    "repository_url": "https://example.com",
                    "profiles": {"myprofile": {"branch_name": "my-branch"}},
                }
            )
        )

        config = Config(config_path=config_path)

        assert config.active_profile["branch_name"] == "my-branch"


class TestConfigFileLoading:
    """Test YAML config file loading."""

    def test_load_valid_yaml(self, tmp_path):
        """Test loading valid YAML configuration."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "repository_url": "https://github.com/user/repo",
            "repository_name": "orca-profiles",
            "auto_commit": True,
            "commit_message_template": "Sync - {timestamp}",
        }
        config_path.write_text(yaml.dump(config_data))

        config = Config(config_path=config_path)

        assert config.data["repository_url"] == config_data["repository_url"]
        assert config.data["auto_commit"] is True

    def test_load_empty_yaml(self, tmp_path):
        """Test loading empty YAML file returns empty dict."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("")

        config = Config(config_path=config_path)

        assert config.data == {}

    def test_load_invalid_yaml_raises_error(self, tmp_path):
        """Test loading invalid YAML raises ValueError."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(ValueError, match="Failed to load config"):
            Config(config_path=config_path)

    def test_load_nonexistent_file_returns_defaults(self, tmp_path, mocker):
        """Test loading nonexistent file returns default configuration."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        config_path = tmp_path / "nonexistent.yaml"

        config = Config(config_path=config_path)

        assert "repository_url" in config.data
        assert "repository_name" in config.data
        assert "profiles" in config.data

    def test_load_yaml_with_comments(self, tmp_path):
        """Test loading YAML with comments."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
# This is a comment
repository_url: https://github.com/user/repo
# Another comment
repository_name: test-repo
"""
        )

        config = Config(config_path=config_path)

        assert config.data["repository_url"] == "https://github.com/user/repo"
        assert config.data["repository_name"] == "test-repo"

    def test_load_yaml_with_nested_structures(self, tmp_path):
        """Test loading YAML with nested dictionaries and lists."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "profiles": {
                "default": {
                    "branch_name": "main",
                    "paths": {"Linux": {"user_paths": ["/path/1", "/path/2"], "system_paths": []}},
                }
            }
        }
        config_path.write_text(yaml.dump(config_data))

        config = Config(config_path=config_path)

        assert config.data["profiles"]["default"]["paths"]["Linux"]["user_paths"] == [
            "/path/1",
            "/path/2",
        ]


class TestDefaultConfiguration:
    """Test default configuration generation."""

    def test_default_config_structure(self, tmp_path, mocker):
        """Test default config contains all required keys."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        config_path = tmp_path / "new-config.yaml"
        config = Config(config_path=config_path)

        assert "repository_url" in config.data
        assert "repository_name" in config.data
        assert "auto_commit" in config.data
        assert "commit_message_template" in config.data
        assert "default_profile" in config.data
        assert "profiles" in config.data

    def test_default_config_platform_paths(self, tmp_path, mocker):
        """Test default config contains paths for all platforms."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        config_path = tmp_path / "new-config.yaml"
        config = Config(config_path=config_path)

        platforms = config.data["profiles"]["default"]["paths"]
        assert "Windows" in platforms
        assert "Darwin" in platforms
        assert "Linux" in platforms

    def test_default_config_uses_discovered_paths(self, tmp_path, mocker):
        """Test default config uses discovered paths when available."""
        mocker.patch("platform.system", return_value="Linux")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        # Create discoverable path
        orca_user = tmp_path / ".config" / "OrcaSlicer" / "user"
        orca_user.mkdir(parents=True)

        # Mock DEFAULT_PATHS to use temp paths
        mock_default_paths = {
            "Windows": Config.DEFAULT_PATHS["Windows"],
            "Darwin": Config.DEFAULT_PATHS["Darwin"],
            "Linux": {
                "user": orca_user,
                "system": tmp_path / ".config" / "OrcaSlicer" / "system",
            },
        }
        mocker.patch.object(Config, "DEFAULT_PATHS", mock_default_paths)

        config_path = tmp_path / "new-config.yaml"
        config = Config(config_path=config_path)

        # Check that discovered path is in default config
        assert any(
            str(orca_user) in str(p)
            for p in config.data["profiles"]["default"]["paths"]["Linux"]["user_paths"]
        )

    def test_default_config_disables_system_paths(self, tmp_path, mocker):
        """Test default config disables system paths."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        config_path = tmp_path / "new-config.yaml"
        config = Config(config_path=config_path)

        # Check all platforms have empty system_paths
        for platform_paths in config.data["profiles"]["default"]["paths"].values():
            assert platform_paths["system_paths"] == []


class TestProfileMerging:
    """Test profile loading and merging with base configuration."""

    def test_profile_overrides_base_config(self, tmp_path):
        """Test profile settings override base configuration."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "repository_url": "https://base.com",
                    "auto_commit": True,
                    "profiles": {
                        "test": {
                            "repository_url": "https://profile.com",
                            "branch_name": "test-branch",
                        }
                    },
                }
            )
        )

        config = Config(config_path=config_path, profile="test")

        assert config.active_profile["repository_url"] == "https://profile.com"
        assert config.active_profile["auto_commit"] is True
        assert config.active_profile["branch_name"] == "test-branch"

    def test_profile_merges_platform_paths(self, tmp_path, mocker):
        """Test profile merges platform-specific paths correctly."""
        mocker.patch("platform.system", return_value="Linux")

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "repository_url": "https://example.com",
                    "profiles": {
                        "test": {
                            "paths": {"Linux": {"user_paths": ["/custom/path"], "system_paths": []}}
                        }
                    },
                }
            )
        )

        config = Config(config_path=config_path, profile="test")

        assert config.active_profile["user_paths"] == ["/custom/path"]
        assert config.active_profile["system_paths"] == []

    def test_profile_nonexistent_raises_error(self, tmp_path):
        """Test loading nonexistent profile raises ValueError."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"profiles": {"default": {"branch_name": "main"}}}))

        with pytest.raises(ValueError, match="Profile 'missing' not found"):
            Config(config_path=config_path, profile="missing")

    def test_profile_no_paths_for_platform(self, tmp_path, mocker):
        """Test profile with no paths for current platform."""
        mocker.patch("platform.system", return_value="Linux")

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "profiles": {
                        "test": {
                            "branch_name": "test",
                            "paths": {"Windows": {"user_paths": ["/windows/path"]}},
                        }
                    }
                }
            )
        )

        config = Config(config_path=config_path, profile="test")

        # Should not have user_paths or system_paths for Linux
        assert (
            "user_paths" not in config.active_profile or config.active_profile["user_paths"] is None
        )

    def test_profile_without_paths_section(self, tmp_path):
        """Test profile without paths section."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "profiles": {
                        "simple": {
                            "branch_name": "simple-branch",
                            "repository_url": "https://simple.com",
                        }
                    }
                }
            )
        )

        config = Config(config_path=config_path, profile="simple")

        assert config.active_profile["branch_name"] == "simple-branch"
        assert config.active_profile["repository_url"] == "https://simple.com"

    def test_no_profile_returns_base_config(self, tmp_path):
        """Test no profile specified returns base config only."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump({"repository_url": "https://base.com", "auto_commit": False})
        )

        config = Config(config_path=config_path)

        assert config.active_profile["repository_url"] == "https://base.com"
        assert config.active_profile["auto_commit"] is False


class TestConfigSaving:
    """Test configuration saving to file."""

    def test_save_creates_parent_directories(self, tmp_path):
        """Test save creates parent directories if they don't exist."""
        config_path = tmp_path / "nested" / "dir" / "config.yaml"

        config = Config(config_path=config_path)
        config.save()

        assert config_path.exists()
        assert config_path.parent.exists()

    def test_save_writes_yaml(self, tmp_path):
        """Test save writes valid YAML to file."""
        config_path = tmp_path / "config.yaml"

        config = Config(config_path=config_path)
        config.data["repository_url"] = "https://saved.com"
        config.save()

        # Reload and verify
        with open(config_path, "r") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["repository_url"] == "https://saved.com"

    def test_save_preserves_structure(self, tmp_path):
        """Test save preserves nested structure."""
        config_path = tmp_path / "config.yaml"

        config = Config(config_path=config_path)
        config.data["profiles"] = {
            "test": {
                "branch_name": "test-branch",
                "paths": {"Linux": {"user_paths": ["/path/1", "/path/2"]}},
            }
        }
        config.save()

        # Reload and verify
        with open(config_path, "r") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["profiles"]["test"]["paths"]["Linux"]["user_paths"] == [
            "/path/1",
            "/path/2",
        ]


class TestConfigGettersSetters:
    """Test Config get/set methods."""

    def test_get_existing_key(self, tmp_path):
        """Test get method returns value for existing key."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"repository_url": "https://example.com"}))

        config = Config(config_path=config_path)

        assert config.get("repository_url") == "https://example.com"

    def test_get_nonexistent_key_returns_default(self, tmp_path):
        """Test get method returns default for nonexistent key."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        config = Config(config_path=config_path)

        assert config.get("missing_key") is None
        assert config.get("missing_key", "default_value") == "default_value"

    def test_set_updates_data(self, tmp_path):
        """Test set method updates configuration data."""
        config_path = tmp_path / "config.yaml"

        config = Config(config_path=config_path)
        config.set("new_key", "new_value")

        assert config.data["new_key"] == "new_value"

    def test_set_overwrites_existing(self, tmp_path):
        """Test set method overwrites existing values."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"existing_key": "old_value"}))

        config = Config(config_path=config_path)
        config.set("existing_key", "new_value")

        assert config.data["existing_key"] == "new_value"


class TestConfigProperties:
    """Test Config property getters."""

    @pytest.mark.parametrize(
        "config_data,property_name,expected",
        [
            (
                {"repository_url": "https://github.com/user/repo"},
                "repository_url",
                "https://github.com/user/repo",
            ),
            ({}, "repository_url", ""),
            ({"repository_name": "my-repo"}, "repository_name", "my-repo"),
            ({}, "repository_name", "orca-profiles"),
        ],
    )
    def test_repository_properties(self, tmp_path, config_data, property_name, expected):
        """Test repository_url and repository_name properties."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config_data))

        config = Config(config_path=config_path)

        assert getattr(config, property_name) == expected

    def test_branch_name_property_explicit(self, tmp_path):
        """Test branch_name property with explicit branch_name."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"branch_name": "my-branch"}))

        config = Config(config_path=config_path)

        assert config.branch_name == "my-branch"

    def test_branch_name_property_from_hostname(self, tmp_path, mocker):
        """Test branch_name property constructed from hostname."""
        mocker.patch("platform.node", return_value="testhost")

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"branch_prefix": "dev-", "branch_postfix": "-work"}))

        config = Config(config_path=config_path)

        assert config.branch_name == "dev-testhost-work"

    def test_branch_name_property_hostname_only(self, tmp_path, mocker):
        """Test branch_name property with only hostname."""
        mocker.patch("platform.node", return_value="mycomputer")

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        config = Config(config_path=config_path)

        assert config.branch_name == "mycomputer"

    @pytest.mark.parametrize(
        "config_data,property_name,expected_paths",
        [
            (
                {"user_paths": ["/path/1", "/path/2"]},
                "user_paths",
                [Path("/path/1"), Path("/path/2")],
            ),
            ({}, "user_paths", []),
            (
                {"system_paths": ["/sys/1", "/sys/2", "/sys/3"]},
                "system_paths",
                [Path("/sys/1"), Path("/sys/2"), Path("/sys/3")],
            ),
            ({}, "system_paths", []),
        ],
    )
    def test_path_list_properties(self, tmp_path, config_data, property_name, expected_paths):
        """Test user_paths and system_paths properties."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config_data))

        config = Config(config_path=config_path)
        paths = getattr(config, property_name)

        assert paths == expected_paths
        if paths:
            assert all(isinstance(p, Path) for p in paths)

    def test_sync_paths_property_combines_both(self, tmp_path):
        """Test sync_paths property combines user and system paths."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump({"user_paths": ["/user/1", "/user/2"], "system_paths": ["/sys/1"]})
        )

        config = Config(config_path=config_path)

        assert len(config.sync_paths) == 3
        assert Path("/user/1") in config.sync_paths
        assert Path("/sys/1") in config.sync_paths

    def test_sync_paths_property_empty(self, tmp_path):
        """Test sync_paths property returns empty list when no paths set."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        config = Config(config_path=config_path)

        assert config.sync_paths == []


class TestListProfiles:
    """Test list_profiles method."""

    def test_list_profiles_multiple(self, tmp_path):
        """Test listing multiple profiles."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "profiles": {
                        "default": {"branch_name": "main"},
                        "work": {"branch_name": "work"},
                        "home": {"branch_name": "home"},
                    }
                }
            )
        )

        config = Config(config_path=config_path)
        profiles = config.list_profiles()

        assert len(profiles) == 3
        assert "default" in profiles
        assert "work" in profiles
        assert "home" in profiles

    def test_list_profiles_single(self, tmp_path):
        """Test listing single profile."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"profiles": {"only": {"branch_name": "only-branch"}}}))

        config = Config(config_path=config_path)
        profiles = config.list_profiles()

        assert len(profiles) == 1
        assert "only" in profiles

    def test_list_profiles_empty(self, tmp_path):
        """Test listing profiles when none exist."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        config = Config(config_path=config_path)
        profiles = config.list_profiles()

        assert profiles == []


class TestPlatformDetection:
    """Test platform-specific behavior."""

    def test_windows_default_paths(self):
        """Test Windows uses correct default paths."""
        # DEFAULT_PATHS is set at module import time, so we just verify structure
        assert "Windows" in Config.DEFAULT_PATHS
        assert "user" in Config.DEFAULT_PATHS["Windows"]
        assert "system" in Config.DEFAULT_PATHS["Windows"]
        assert "OrcaSlicer" in str(Config.DEFAULT_PATHS["Windows"]["user"])

    def test_macos_default_paths(self):
        """Test macOS uses correct default paths."""
        # DEFAULT_PATHS is set at module import time, so we just verify structure
        assert "Darwin" in Config.DEFAULT_PATHS
        assert "user" in Config.DEFAULT_PATHS["Darwin"]
        assert "system" in Config.DEFAULT_PATHS["Darwin"]
        assert "Library" in str(Config.DEFAULT_PATHS["Darwin"]["user"])
        assert "Application Support" in str(Config.DEFAULT_PATHS["Darwin"]["user"])

    def test_linux_default_paths(self):
        """Test Linux uses correct default paths."""
        # DEFAULT_PATHS is set at module import time, so we just verify structure
        assert "Linux" in Config.DEFAULT_PATHS
        assert "user" in Config.DEFAULT_PATHS["Linux"]
        assert "system" in Config.DEFAULT_PATHS["Linux"]
        assert ".config" in str(Config.DEFAULT_PATHS["Linux"]["user"])
        assert "OrcaSlicer" in str(Config.DEFAULT_PATHS["Linux"]["user"])


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.parametrize(
        "platform_name,path_keys,expected_patterns",
        [
            ("Windows", ["user", "system"], ["AppData", "OrcaSlicer"]),
            ("Darwin", ["user", "system"], ["Library", "Application Support"]),
            ("Linux", ["user", "system"], [".config", "OrcaSlicer"]),
        ],
    )
    def test_platform_default_paths(self, platform_name, path_keys, expected_patterns):
        """Test all platforms use correct default paths."""
        assert platform_name in Config.DEFAULT_PATHS
        for key in path_keys:
            assert key in Config.DEFAULT_PATHS[platform_name]

        user_path_str = str(Config.DEFAULT_PATHS[platform_name]["user"])
        assert any(pattern in user_path_str for pattern in expected_patterns)

    def test_config_with_null_values(self, tmp_path):
        """Test config handles null values correctly."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"repository_url": None, "repository_name": None}))

        config = Config(config_path=config_path)

        # Should handle None gracefully
        assert config.data["repository_url"] is None

    def test_config_with_unicode_characters(self, tmp_path):
        """Test config handles unicode characters in values."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"repository_name": "プロファイル-配置文件-профиль"}))

        config = Config(config_path=config_path)

        assert "プロファイル" in config.data["repository_name"]

    def test_config_with_special_path_characters(self, tmp_path):
        """Test config handles paths with spaces and special characters."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump({"user_paths": ["/path/with spaces/and-dashes", "/path/with_underscores"]})
        )

        config = Config(config_path=config_path)

        assert len(config.user_paths) == 2
        assert any("spaces" in str(p) for p in config.user_paths)

    def test_config_with_very_long_values(self, tmp_path):
        """Test config handles very long string values."""
        config_path = tmp_path / "config.yaml"
        long_value = "x" * 10000
        config_path.write_text(yaml.dump({"commit_message_template": long_value}))

        config = Config(config_path=config_path)

        assert len(config.data["commit_message_template"]) == 10000

    def test_discover_with_symlinks(self, tmp_path, mocker):
        """Test discovery handles symlinks correctly."""
        mocker.patch("platform.system", return_value="Linux")

        # Create real directory
        real_dir = tmp_path / "real" / "OrcaSlicer" / "user"
        real_dir.mkdir(parents=True)

        # Create symlink
        link_dir = tmp_path / ".config" / "OrcaSlicer"
        link_dir.parent.mkdir(parents=True)
        link_dir.symlink_to(tmp_path / "real" / "OrcaSlicer")

        # Mock DEFAULT_PATHS to point to symlinked location
        user_via_symlink = link_dir / "user"
        mock_default_paths = {
            "Windows": Config.DEFAULT_PATHS["Windows"],
            "Darwin": Config.DEFAULT_PATHS["Darwin"],
            "Linux": {
                "user": user_via_symlink,
                "system": link_dir / "system",
            },
        }
        mocker.patch.object(Config, "DEFAULT_PATHS", mock_default_paths)

        result = Config.discover_orcaslicer_paths()

        # Should find the path (through symlink)
        assert len(result["user"]) > 0
