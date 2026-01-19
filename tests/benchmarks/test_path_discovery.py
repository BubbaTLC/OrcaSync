"""Benchmark tests for path discovery and config operations."""

import pytest
from pathlib import Path
import tempfile
import time

from orcasync.config import Config


@pytest.fixture
def benchmark_config_dir(tmp_path):
    """Create a temporary config directory for benchmarking."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def benchmark_config_file(benchmark_config_dir):
    """Create a config file with typical content."""
    config_path = benchmark_config_dir / "orcasync-config.yaml"
    config_content = """
repository_url: https://github.com/user/orcasync-profiles.git
branch_name: my-machine
profiles:
  - user
  - system
user_paths:
  - /path/to/orcaslicer/user
system_paths:
  - /path/to/orcaslicer/system
"""
    config_path.write_text(config_content)
    return config_path


class TestConfigLoadingPerformance:
    """Benchmark tests for config loading operations."""
    
    def test_config_creation_with_defaults(self, benchmark, benchmark_config_dir):
        """Benchmark Config creation with default values."""
        config_file = benchmark_config_dir / "orcasync-config.yaml"
        
        def create_config():
            return Config(config_path=config_file)
        
        result = benchmark(create_config)
        
        # Verify config was created
        assert result is not None
        assert isinstance(result, Config)
    
    def test_config_loading_from_file(self, benchmark, benchmark_config_file):
        """Benchmark Config loading from existing file."""
        
        def load_config():
            return Config(config_path=benchmark_config_file)
        
        result = benchmark(load_config)
        
        # Verify config was loaded
        assert result is not None
        assert result.repository_url == "https://github.com/user/orcasync-profiles.git"
    
    def test_config_loading_with_validation(self, benchmark, benchmark_config_file):
        """Benchmark config loading with property access (validation)."""
        
        def load_and_validate():
            config = Config(config_path=benchmark_config_file)
            # Access all properties to trigger validation
            _ = config.repository_url
            _ = config.branch_name
            _ = config.user_paths
            _ = config.system_paths
            _ = config.sync_paths
            _ = config.repository_name
            return config
        
        result = benchmark(load_and_validate)
        
        # Verify all properties are accessible
        assert result.repository_url is not None
    
    def test_config_save_performance(self, benchmark, benchmark_config_dir):
        """Benchmark Config.save() operation."""
        config_file = benchmark_config_dir / "orcasync-config.yaml"
        config = Config(config_path=config_file)
        config.set("repository_url", "https://github.com/test/repo.git")
        config.set("branch_name", "test-branch")
        
        # Benchmark the save operation
        benchmark(config.save)
        
        # Verify file was saved
        config_file = benchmark_config_dir / "orcasync-config.yaml"
        assert config_file.exists()
    
    def test_config_multiple_property_access(self, benchmark, benchmark_config_file):
        """Benchmark repeated property access (caching behavior)."""
        config = Config(config_path=benchmark_config_file)
        
        def access_properties():
            # Access properties multiple times
            for _ in range(10):
                _ = config.repository_url
                _ = config.branch_name
                _ = config.user_paths
                _ = config.system_paths
                _ = config.sync_paths
        
        benchmark(access_properties)


class TestPathDiscoveryPerformance:
    """Benchmark tests for path discovery operations."""
    
    def test_discover_orcaslicer_paths(self, benchmark):
        """Benchmark discover_orcaslicer_paths() operation."""
        result = benchmark(Config.discover_orcaslicer_paths)
        
        # Verify discovery returns expected structure
        assert isinstance(result, dict)
        assert "user" in result
        assert "system" in result
    
    def test_discover_with_filesystem_check(self, benchmark, tmp_path):
        """Benchmark path discovery with actual filesystem checks."""
        # Create mock OrcaSlicer directory structure
        orcaslicer_dir = tmp_path / "OrcaSlicer"
        user_dir = orcaslicer_dir / "user"
        system_dir = orcaslicer_dir / "system"
        user_dir.mkdir(parents=True)
        system_dir.mkdir(parents=True)
        
        # Create nested structure
        for subdir in ["filament", "machine", "process"]:
            (user_dir / subdir).mkdir()
            (system_dir / subdir).mkdir()
            
            # Add some files
            for i in range(10):
                (user_dir / subdir / f"profile_{i}.json").write_text("{}")
                (system_dir / subdir / f"profile_{i}.json").write_text("{}")
        
        # Benchmark the discovery (this will check the default paths)
        result = benchmark(Config.discover_orcaslicer_paths)
        
        # Verify result structure
        assert isinstance(result, dict)


class TestConfigComplexOperations:
    """Benchmark tests for complex config operations."""
    
    def test_config_full_workflow(self, benchmark, benchmark_config_dir):
        """Benchmark complete config workflow: create, set, save, load."""
        config_file = benchmark_config_dir / "orcasync-config.yaml"
        
        def full_workflow():
            # Create new config
            config = Config(config_path=config_file)
            
            # Set multiple values
            config.set("repository_url", "https://github.com/benchmark/test.git")
            config.set("branch_name", "benchmark-branch")
            config.set("user_paths", ["/path/to/user"])
            config.set("system_paths", ["/path/to/system"])
            
            # Save config
            config.save()
            
            # Load config back
            loaded_config = Config(config_path=config_file)
            
            # Access properties
            _ = loaded_config.repository_url
            _ = loaded_config.sync_paths
            
            return loaded_config
        
        result = benchmark(full_workflow)
        
        # Verify workflow completed successfully
        assert result.repository_url == "https://github.com/benchmark/test.git"
    
    def test_config_with_large_path_list(self, benchmark, benchmark_config_dir):
        """Benchmark config operations with large number of paths."""
        config_file = benchmark_config_dir / "orcasync-config.yaml"
        config = Config(config_path=config_file)
        
        # Create large list of paths
        large_path_list = [f"/path/to/profile_{i}" for i in range(100)]
        
        def set_and_access():
            config.set("user_paths", large_path_list)
            config.set("system_paths", large_path_list)
            
            # Access sync_paths which merges both lists
            paths = config.sync_paths
            return paths
        
        result = benchmark(set_and_access)
        
        # Verify large list was set in the configuration data
        assert len(config.data.get("user_paths", [])) == 100
        assert len(config.data.get("system_paths", [])) == 100
    
    def test_list_profiles_performance(self, benchmark, tmp_path):
        """Benchmark list_profiles() with multiple profile files."""
        # Create a base config that has profiles defined
        base_config_path = tmp_path / "orcasync-config.yaml"
        base_config_path.write_text(f"""
profiles:
  profile1:
    repository_url: https://github.com/user/profile1.git
    branch_name: profile1
  profile2:
    repository_url: https://github.com/user/profile2.git
    branch_name: profile2
  profile3:
    repository_url: https://github.com/user/profile3.git
    branch_name: profile3
  default:
    repository_url: https://github.com/user/default.git
    branch_name: default
""")
        
        # Benchmark listing profiles
        def list_profiles():
            config = Config(config_path=base_config_path)
            return config.list_profiles()
        
        result = benchmark(list_profiles)
        
        # Verify profiles were listed
        assert len(result) >= 4
    
    def test_profile_switching_performance(self, benchmark, tmp_path):
        """Benchmark switching between multiple profiles."""
        # Create multiple profiles
        profiles = []
        for i in range(5):
            profile_dir = tmp_path / f"profile_{i}"
            profile_dir.mkdir()
            config_file = profile_dir / "orcasync-config.yaml"
            config_file.write_text(f"""
repository_url: https://github.com/user/profile_{i}.git
branch_name: profile-{i}
""")
            profiles.append(profile_dir)
        
        def switch_profiles():
            # Load each profile in sequence
            configs = []
            for profile_dir in profiles:
                config_file = profile_dir / "orcasync-config.yaml"
                config = Config(config_path=config_file)
                # Access properties
                _ = config.repository_url
                _ = config.branch_name
                configs.append(config)
            return configs
        
        result = benchmark(switch_profiles)
        
        # Verify all profiles were loaded
        assert len(result) == 5


class TestConfigEdgeCases:
    """Benchmark tests for edge cases and error handling."""
    
    def test_missing_config_file_handling(self, benchmark, tmp_path):
        """Benchmark Config loading with missing file (creates default)."""
        nonexistent_file = tmp_path / "nonexistent" / "orcasync-config.yaml"
        
        def load_missing():
            return Config(config_path=nonexistent_file)
        
        result = benchmark(load_missing)
        
        # Verify default config was created
        assert result is not None
    
    def test_config_with_unicode_paths(self, benchmark, tmp_path):
        """Benchmark config operations with unicode in paths."""
        config_dir = tmp_path / "配置"
        config_dir.mkdir()
        config_file = config_dir / "orcasync-config.yaml"
        
        def unicode_workflow():
            config = Config(config_path=config_file)
            config.set("repository_url", "https://github.com/用户/repo.git")
            config.set("branch_name", "分支-机器")
            config.save()
            
            loaded = Config(config_path=config_file)
            _ = loaded.repository_url
            return loaded
        
        result = benchmark(unicode_workflow)
        
        # Verify unicode was handled correctly
        assert "用户" in result.repository_url
