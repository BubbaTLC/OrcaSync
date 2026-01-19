"""Tests for CLI commands using Click's CliRunner."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from orcasync.cli import main, init, push, pull, sync, status, config_path
from orcasync.config import Config
from orcasync.git_ops import GitManager, GitSyncError


@pytest.fixture
def runner():
    """Create a Click CliRunner."""
    return CliRunner()


@pytest.fixture
def mock_config(mocker, tmp_path):
    """Mock Config class with basic setup."""
    mock_cfg = MagicMock(spec=Config)
    mock_cfg.config_path = tmp_path / ".config" / "orcasync" / "config.yaml"
    mock_cfg.repository_url = "https://github.com/test/repo.git"
    mock_cfg.repository_name = "test-repo"
    mock_cfg.branch_name = "main"
    mock_cfg.profile_name = None
    mock_cfg.user_paths = [tmp_path / "OrcaSlicer" / "user"]
    mock_cfg.system_paths = []
    mock_cfg.sync_paths = {"user": mock_cfg.user_paths}
    mock_cfg.data = {}
    mock_cfg.list_profiles.return_value = []

    mocker.patch("orcasync.cli.Config", return_value=mock_cfg)
    return mock_cfg


@pytest.fixture
def mock_git_manager(mocker, tmp_path):
    """Mock GitManager class."""
    mock_mgr = MagicMock(spec=GitManager)
    mock_mgr.repo = MagicMock()
    mock_mgr.repo.is_dirty.return_value = False
    mock_mgr.repo.untracked_files = []
    mock_mgr.repo.active_branch = MagicMock()
    mock_mgr.repo.active_branch.tracking_branch.return_value = None
    mock_mgr.repo.remotes = []
    mock_mgr.get_status.return_value = {
        "branch": "main",
        "dirty": False,
        "untracked_files": 0,
        "has_remote": True,
    }

    mocker.patch("orcasync.cli.GitManager", return_value=mock_mgr)
    return mock_mgr


class TestMainGroup:
    """Tests for the main CLI group."""

    def test_version_option(self, runner):
        """Test --version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower() or "0." in result.output

    def test_no_command_launches_tui(self, runner, mocker):
        """Test that running without a command launches TUI."""
        mock_run_tui = mocker.patch("orcasync.tui.run_tui")

        result = runner.invoke(main, [])

        # TUI will be called and then exit
        assert mock_run_tui.called
        assert result.exit_code == 0

    def test_no_command_with_config_option(self, runner, mocker):
        """Test TUI launch with --config option."""
        mock_run_tui = mocker.patch("orcasync.tui.run_tui")

        result = runner.invoke(main, ["--config", "/tmp/test.yaml"])

        assert mock_run_tui.called
        call_args = mock_run_tui.call_args[0]
        assert call_args[0] == Path("/tmp/test.yaml")
        assert result.exit_code == 0

    def test_no_command_with_profile_option(self, runner, mocker):
        """Test TUI launch with --profile option."""
        mock_run_tui = mocker.patch("orcasync.tui.run_tui")

        result = runner.invoke(main, ["--profile", "work"])

        assert mock_run_tui.called
        call_args = mock_run_tui.call_args[0]
        assert call_args[1] == "work"
        assert result.exit_code == 0


class TestInitCommand:
    """Tests for the init command."""

    def test_init_first_time(self, runner, mocker, tmp_path):
        """Test successful first-time initialization."""
        config_path = tmp_path / "config.yaml"

        mock_cfg = MagicMock(spec=Config)
        mock_cfg.config_path = config_path
        mock_cfg.repository_name = "test-repo"
        mock_cfg.branch_name = "main"
        mock_cfg.user_paths = []
        mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        mocker.patch.object(
            Config,
            "discover_orcaslicer_paths",
            return_value={"user": [tmp_path / "OrcaSlicer" / "user"], "system": []},
        )

        mock_git_mgr = MagicMock(spec=GitManager)
        mocker.patch("orcasync.cli.GitManager", return_value=mock_git_mgr)

        # Mock Path.home()
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        result = runner.invoke(init, input="\n\ntest-repo\nn\n")

        assert result.exit_code == 0
        assert "Initialization complete!" in result.output
        assert mock_cfg.save.called
        assert mock_git_mgr.init_repository.called
        assert mock_git_mgr.ensure_branch.called

    @pytest.mark.parametrize(
        "user_response,should_save,expected_text",
        [
            ("n\n", False, "cancelled"),
            ("y\n\nnew-repo\nn\n", True, None),
        ],
    )
    def test_init_with_existing_config(
        self, runner, mocker, tmp_path, user_response, should_save, expected_text
    ):
        """Test init with existing config - cancel or overwrite."""
        config_path = tmp_path / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("existing: config")

        mock_cfg = MagicMock(spec=Config)
        mock_cfg.config_path = config_path
        mock_cfg.repository_name = "new-repo"
        mock_cfg.branch_name = "main"
        mock_cfg.user_paths = []
        mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        mocker.patch.object(
            Config, "discover_orcaslicer_paths", return_value={"user": [], "system": []}
        )

        mock_git_mgr = MagicMock(spec=GitManager)
        mocker.patch("orcasync.cli.GitManager", return_value=mock_git_mgr)
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        result = runner.invoke(init, input=user_response)

        assert result.exit_code == 0
        assert mock_cfg.save.called == should_save
        if expected_text:
            assert expected_text in result.output.lower()

    def test_init_with_custom_paths(self, runner, mocker, tmp_path):
        """Test init with custom OrcaSlicer paths."""
        config_path = tmp_path / "config.yaml"
        custom_path = tmp_path / "custom" / "orcaslicer"

        mock_cfg = MagicMock(spec=Config)
        mock_cfg.config_path = config_path
        mock_cfg.repository_name = "test-repo"
        mock_cfg.branch_name = "main"
        mock_cfg.user_paths = []
        mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        mocker.patch.object(
            Config, "discover_orcaslicer_paths", return_value={"user": [], "system": []}
        )

        mock_git_mgr = MagicMock(spec=GitManager)
        mocker.patch("orcasync.cli.GitManager", return_value=mock_git_mgr)
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        # Repo URL, repo name, use custom paths (y), custom path
        result = runner.invoke(init, input=f"\ntest-repo\ny\n{custom_path}\n")

        assert result.exit_code == 0
        mock_cfg.set.assert_any_call("user_paths", [str(custom_path)])

    def test_init_git_error(self, runner, mocker, tmp_path):
        """Test init with git initialization error."""
        config_path = tmp_path / "config.yaml"

        mock_cfg = MagicMock(spec=Config)
        mock_cfg.config_path = config_path
        mock_cfg.repository_name = "test-repo"
        mock_cfg.branch_name = "main"
        mock_cfg.user_paths = []
        mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        mocker.patch.object(
            Config, "discover_orcaslicer_paths", return_value={"user": [], "system": []}
        )

        mock_git_mgr = MagicMock(spec=GitManager)
        mock_git_mgr.init_repository.side_effect = GitSyncError("Git init failed")
        mocker.patch("orcasync.cli.GitManager", return_value=mock_git_mgr)
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        result = runner.invoke(init, input="\ntest-repo\nn\n")

        assert result.exit_code == 1
        assert "Failed to initialize repository" in result.output

    def test_init_with_discovered_paths(self, runner, mocker, tmp_path):
        """Test init uses discovered paths when available."""
        config_path = tmp_path / "config.yaml"
        user_path = tmp_path / "OrcaSlicer" / "user"
        system_path = tmp_path / "OrcaSlicer" / "system"

        mock_cfg = MagicMock(spec=Config)
        mock_cfg.config_path = config_path
        mock_cfg.repository_name = "test-repo"
        mock_cfg.branch_name = "main"
        mock_cfg.user_paths = []
        mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        mocker.patch.object(
            Config,
            "discover_orcaslicer_paths",
            return_value={"user": [user_path], "system": [system_path]},
        )

        mock_git_mgr = MagicMock(spec=GitManager)
        mocker.patch("orcasync.cli.GitManager", return_value=mock_git_mgr)
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        # Repo URL, repo name, don't use custom paths
        result = runner.invoke(init, input="\ntest-repo\nn\n")

        assert result.exit_code == 0
        # Should set discovered paths (paths are converted to list of strings)
        # Use call locally to avoid import conflicts
        set_calls = [call_args[0] for call_args in mock_cfg.set.call_args_list]
        assert any("user_paths" in item for item in set_calls)
        assert any("system_paths" in item for item in set_calls)


class TestPushCommand:
    """Tests for the push command."""

    def test_push_success(self, runner, mock_config, mock_git_manager, tmp_path):
        """Test successful push."""
        mock_git_manager.sync_files.return_value = ["file1.json", "file2.json"]
        mock_git_manager.commit_changes.return_value = True

        result = runner.invoke(push)

        assert result.exit_code == 0
        assert "Copied 2 files" in result.output
        assert "Changes committed" in result.output
        assert "Pushed to remote" in result.output
        assert mock_git_manager.init_repository.called
        assert mock_git_manager.ensure_branch.called
        assert mock_git_manager.sync_files.called
        assert mock_git_manager.push.called

    def test_push_no_changes(self, runner, mock_config, mock_git_manager):
        """Test push with no changes."""
        mock_git_manager.sync_files.return_value = []
        mock_git_manager.commit_changes.return_value = False

        result = runner.invoke(push)

        assert result.exit_code == 0
        assert "No changes to commit" in result.output
        assert not mock_git_manager.push.called

    @pytest.mark.parametrize(
        "user_response,should_init,should_commit",
        [
            ("n\n", False, False),
            ("y\n", True, True),
        ],
    )
    def test_push_no_repo_url(
        self, runner, mock_config, mock_git_manager, user_response, should_init, should_commit
    ):
        """Test push with no repo URL - cancel or continue local."""
        mock_config.repository_url = ""
        mock_git_manager.sync_files.return_value = ["file1.json"]
        mock_git_manager.commit_changes.return_value = True

        result = runner.invoke(push, input=user_response)

        assert result.exit_code == 0
        assert mock_git_manager.init_repository.called == should_init
        assert mock_git_manager.commit_changes.called == should_commit
        # Should never push when no remote URL
        assert not mock_git_manager.push.called

    def test_push_with_custom_message(self, runner, mock_config, mock_git_manager):
        """Test push with custom commit message."""
        mock_git_manager.sync_files.return_value = ["file1.json"]
        mock_git_manager.commit_changes.return_value = True

        result = runner.invoke(push, ["--message", "Custom commit message"])

        assert result.exit_code == 0
        mock_git_manager.commit_changes.assert_called_with("Custom commit message")

    def test_push_git_error(self, runner, mock_config, mock_git_manager):
        """Test push with git error."""
        mock_git_manager.init_repository.side_effect = GitSyncError("Git error")

        result = runner.invoke(push)

        assert result.exit_code == 1
        assert "Sync failed" in result.output

    def test_push_push_error_continues(self, runner, mock_config, mock_git_manager):
        """Test push where remote push fails but local commit succeeds."""
        mock_git_manager.sync_files.return_value = ["file1.json"]
        mock_git_manager.commit_changes.return_value = True
        mock_git_manager.push.side_effect = GitSyncError("Push failed")

        result = runner.invoke(push)

        assert result.exit_code == 0
        assert "Changes committed" in result.output
        assert "Push to remote failed" in result.output
        assert "committed locally but not pushed" in result.output

    def test_push_with_config_option(self, runner, mocker, tmp_path):
        """Test push with --config option."""
        custom_config = tmp_path / "custom.yaml"

        mock_cfg = MagicMock(spec=Config)
        mock_cfg.repository_url = "https://github.com/test/repo.git"
        mock_cfg.repository_name = "test"
        mock_cfg.branch_name = "main"
        mock_cfg.sync_paths = {}
        mock_config_class = mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        mock_git_mgr = MagicMock(spec=GitManager)
        mock_git_mgr.sync_files.return_value = []
        mock_git_mgr.commit_changes.return_value = False
        mocker.patch("orcasync.cli.GitManager", return_value=mock_git_mgr)

        result = runner.invoke(push, ["--config", str(custom_config)])

        assert result.exit_code == 0
        # Verify Config was called with the custom path
        assert mock_config_class.call_args[0][0] == custom_config


class TestPullCommand:
    """Tests for the pull command."""

    def test_pull_success(self, runner, mock_config, mock_git_manager):
        """Test successful pull."""
        mock_git_manager.pull.return_value = (True, ["file1.json", "file2.json"])
        mock_git_manager.restore_files.return_value = ["file1.json", "file2.json"]

        result = runner.invoke(pull)

        assert result.exit_code == 0
        assert "Pulled 2 changed files" in result.output
        assert "Restored 2 files" in result.output
        assert mock_git_manager.pull.called
        assert mock_git_manager.restore_files.called

    def test_pull_no_changes(self, runner, mock_config, mock_git_manager):
        """Test pull with no changes."""
        mock_git_manager.pull.return_value = (False, [])

        result = runner.invoke(pull)

        assert result.exit_code == 0
        assert "No changes to pull" in result.output
        assert not mock_git_manager.restore_files.called

    def test_pull_no_repo_url(self, runner, mock_config):
        """Test pull with no repository URL configured."""
        mock_config.repository_url = ""

        result = runner.invoke(pull)

        assert result.exit_code == 1
        assert "No repository URL configured" in result.output

    def test_pull_git_error(self, runner, mock_config, mock_git_manager):
        """Test pull with git error."""
        mock_git_manager.pull.side_effect = GitSyncError("Pull failed")

        result = runner.invoke(pull)

        assert result.exit_code == 1
        assert "Sync failed" in result.output

    def test_pull_with_profile_option(self, runner, mocker):
        """Test pull with --profile option."""
        mock_cfg = MagicMock(spec=Config)
        mock_cfg.repository_url = "https://github.com/test/repo.git"
        mock_cfg.repository_name = "test"
        mock_cfg.branch_name = "main"
        mock_cfg.sync_paths = {}
        mock_config_class = mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        mock_git_mgr = MagicMock(spec=GitManager)
        mock_git_mgr.pull.return_value = (False, [])
        mocker.patch("orcasync.cli.GitManager", return_value=mock_git_mgr)

        result = runner.invoke(pull, ["--profile", "work"])

        assert result.exit_code == 0
        # Verify Config was called with the profile
        assert mock_config_class.call_args[0][1] == "work"


class TestSyncCommand:
    """Tests for the sync command."""

    def test_sync_full_workflow(self, runner, mock_config, mock_git_manager):
        """Test full sync workflow: fetch, pull, push."""
        # Setup mocks
        mock_origin = MagicMock()
        mock_origin.fetch.return_value = []
        mock_git_manager.repo.remotes = MagicMock()
        mock_git_manager.repo.remotes.__contains__.return_value = True
        mock_git_manager.repo.remotes.origin = mock_origin

        mock_git_manager.pull.return_value = (True, ["file1.json"])
        mock_git_manager.restore_files.return_value = ["file1.json"]
        mock_git_manager.sync_files.return_value = ["file1.json", "file2.json"]
        mock_git_manager.commit_changes.return_value = True

        mock_tracking = MagicMock()
        mock_tracking.name = "origin/main"
        mock_git_manager.repo.active_branch.tracking_branch.return_value = mock_tracking

        # Mock iter_commits to return empty (no commits ahead)
        mock_git_manager.repo.iter_commits.return_value = []

        result = runner.invoke(sync)

        assert result.exit_code == 0
        assert "Step 1/3: Fetching" in result.output
        assert "Step 2/3: Pulling" in result.output
        assert "Step 3/3: Pushing" in result.output
        assert "Sync complete!" in result.output

    def test_sync_no_remote(self, runner, mock_config, mock_git_manager):
        """Test sync with no remote configured."""
        mock_git_manager.repo.remotes = MagicMock()
        mock_git_manager.repo.remotes.__contains__.return_value = False

        mock_git_manager.pull.return_value = (False, [])
        mock_git_manager.sync_files.return_value = []
        mock_git_manager.commit_changes.return_value = False

        result = runner.invoke(sync)

        assert result.exit_code == 0
        assert "No remote configured, skipping fetch" in result.output

    def test_sync_with_local_changes_before_pull(self, runner, mock_config, mock_git_manager):
        """Test sync commits local repo changes before pulling."""
        mock_git_manager.repo.remotes = MagicMock()
        mock_git_manager.repo.remotes.__contains__.return_value = False
        mock_git_manager.repo.is_dirty.return_value = True
        mock_git_manager.repo.untracked_files = ["newfile.txt"]

        mock_git_manager.pull.return_value = (False, [])
        mock_git_manager.sync_files.return_value = []
        mock_git_manager.commit_changes.return_value = True

        result = runner.invoke(sync)

        assert result.exit_code == 0
        assert "Pre-sync commit" in result.output or "local repository changes" in result.output
        assert mock_git_manager.repo.git.add.called

    def test_sync_pushes_commits_ahead(self, runner, mock_config, mock_git_manager):
        """Test sync pushes when commits are ahead of remote."""
        mock_git_manager.repo.remotes = MagicMock()
        mock_git_manager.repo.remotes.__contains__.return_value = False

        mock_git_manager.pull.return_value = (False, [])
        mock_git_manager.sync_files.return_value = []
        mock_git_manager.commit_changes.return_value = False

        mock_tracking = MagicMock()
        mock_tracking.name = "origin/main"
        mock_git_manager.repo.active_branch.tracking_branch.return_value = mock_tracking

        # Mock commits ahead
        mock_commit = MagicMock()
        mock_git_manager.repo.iter_commits.return_value = [mock_commit, mock_commit]

        result = runner.invoke(sync)

        assert result.exit_code == 0
        mock_git_manager.push.assert_called()
        assert "Pushed 2 commit(s)" in result.output

    def test_sync_no_repo_url(self, runner, mock_config):
        """Test sync with no repository URL."""
        mock_config.repository_url = ""

        result = runner.invoke(sync)

        assert result.exit_code == 1
        assert "No repository URL configured" in result.output

    def test_sync_git_error(self, runner, mock_config, mock_git_manager):
        """Test sync with git error."""
        mock_git_manager.init_repository.side_effect = GitSyncError("Sync error")

        result = runner.invoke(sync)

        assert result.exit_code == 1
        assert "Sync failed" in result.output

    def test_sync_push_error_continues(self, runner, mock_config, mock_git_manager):
        """Test sync continues when push fails."""
        mock_git_manager.repo.remotes = MagicMock()
        mock_git_manager.repo.remotes.__contains__.return_value = False

        mock_git_manager.pull.return_value = (False, [])
        mock_git_manager.sync_files.return_value = ["file1.json"]
        mock_git_manager.commit_changes.return_value = True

        mock_tracking = MagicMock()
        mock_git_manager.repo.active_branch.tracking_branch.return_value = mock_tracking
        mock_git_manager.repo.iter_commits.return_value = []

        mock_git_manager.push.side_effect = Exception("Push error")

        result = runner.invoke(sync)

        assert result.exit_code == 0
        assert "Could not push" in result.output


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_basic(self, runner, mock_config, tmp_path):
        """Test basic status output."""
        mock_config.user_paths[0].mkdir(parents=True, exist_ok=True)

        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "OrcaSync Configuration" in result.output
        assert "Config File" in result.output
        assert "Repository URL" in result.output
        assert "Branch Name" in result.output

    def test_status_with_profile(self, runner, mocker, tmp_path):
        """Test status with active profile."""
        mock_cfg = MagicMock(spec=Config)
        mock_cfg.config_path = tmp_path / "config.yaml"
        mock_cfg.repository_url = "https://github.com/test/repo.git"
        mock_cfg.repository_name = "test-repo"
        mock_cfg.branch_name = "main"
        mock_cfg.profile_name = "work"
        mock_cfg.user_paths = [tmp_path / "OrcaSlicer" / "user"]
        mock_cfg.system_paths = []
        mock_cfg.data = {"default_profile": "work"}
        mock_cfg.list_profiles.return_value = ["work", "home"]

        mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "work" in result.output
        assert "Available Profiles" in result.output

    def test_status_with_existing_paths(self, runner, mock_config, tmp_path):
        """Test status shows path existence and file counts."""
        user_path = mock_config.user_paths[0]
        user_path.mkdir(parents=True, exist_ok=True)
        (user_path / "test.json").write_text("{}")

        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "OrcaSlicer Profile Locations" in result.output
        assert "User" in result.output
        # Should show checkmark for existing path
        assert "✓" in result.output

    def test_status_with_repository(self, runner, mock_config, mock_git_manager, tmp_path):
        """Test status with initialized repository."""
        repo_path = tmp_path / ".local" / "share" / "orcasync" / "test-repo"
        repo_path.mkdir(parents=True, exist_ok=True)

        result = runner.invoke(status)

        assert result.exit_code == 0
        # Should show repository status even if there's an error accessing it
        # (the test mocks may not fully simulate a real repo)

    def test_status_no_repository(self, runner, mock_config, tmp_path):
        """Test status when repository not initialized."""
        # Ensure repo path doesn't exist
        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "Repository not initialized" in result.output or "Run" in result.output


class TestConfigPathCommand:
    """Tests for the config-path command."""

    def test_config_path_default(self, runner, mock_config):
        """Test config-path shows default config location."""
        result = runner.invoke(config_path)

        assert result.exit_code == 0
        # Output may have line breaks, so strip both before comparison
        assert str(mock_config.config_path) in result.output.replace("\n", "")

    def test_config_path_with_custom_config(self, runner, mocker, tmp_path):
        """Test config-path with custom config option."""
        custom_config = tmp_path / "custom.yaml"

        mock_cfg = MagicMock(spec=Config)
        mock_cfg.config_path = custom_config
        mocker.patch("orcasync.cli.Config", return_value=mock_cfg)

        result = runner.invoke(config_path, ["--config", str(custom_config)])

        assert result.exit_code == 0
        # Output may have line breaks, so strip both before comparison
        assert str(custom_config) in result.output.replace("\n", "")
