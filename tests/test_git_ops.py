"""Unit tests for GitManager class in git_ops.py."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from git import GitCommandError, InvalidGitRepositoryError
from orcasync.git_ops import GitManager, GitSyncError


class TestGitManagerInit:
    """Tests for GitManager initialization."""

    def test_init_creates_instance(self):
        """Test that GitManager can be instantiated with required parameters."""
        repo_path = Path("/tmp/test-repo")
        repo_url = "https://github.com/user/repo.git"
        branch_name = "main"

        manager = GitManager(repo_path, repo_url, branch_name)

        assert manager.repo_path == repo_path
        assert manager.repo_url == repo_url
        assert manager.branch_name == branch_name
        assert manager.repo is None

    def test_init_with_pathlib_path(self):
        """Test initialization with pathlib.Path objects."""
        repo_path = Path("/tmp/test-repo")
        manager = GitManager(repo_path, "https://github.com/user/repo.git", "main")
        assert isinstance(manager.repo_path, Path)

    def test_init_with_empty_url(self):
        """Test initialization with empty repository URL."""
        manager = GitManager(Path("/tmp/test"), "", "main")
        assert manager.repo_url == ""


class TestConfigureCredentials:
    """Tests for _configure_credentials method."""

    @pytest.mark.parametrize(
        "platform,expected_helper,call_count",
        [
            ("Darwin", "osxkeychain", 2),
            ("Windows", "wincred", 2),
            ("Linux", None, 1),  # Linux doesn't set credential helper
        ],
    )
    def test_configure_credentials_by_platform(
        self, mocker, tmp_path, platform_name, expected_helper, call_count
    ):
        """Test credential configuration for different platforms."""
        mocker.patch("platform.system", return_value=platform_name)
        mock_repo = MagicMock()
        mock_config_writer = MagicMock()
        mock_repo.config_writer.return_value.__enter__ = MagicMock(return_value=mock_config_writer)
        mock_repo.config_writer.return_value.__exit__ = MagicMock(return_value=None)

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo
        manager._configure_credentials()

        assert mock_config_writer.set_value.call_count == call_count
        if expected_helper:
            mock_config_writer.set_value.assert_any_call("credential", "helper", expected_helper)
        mock_config_writer.set_value.assert_any_call("pull", "rebase", "true")

    def test_configure_credentials_no_repo(self, tmp_path):
        """Test that _configure_credentials handles missing repo gracefully."""
        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = None
        manager._configure_credentials()  # Should not raise

    def test_configure_credentials_handles_exception(self, mocker, tmp_path):
        """Test that _configure_credentials handles exceptions gracefully."""
        mocker.patch("platform.system", return_value="Darwin")
        mock_repo = MagicMock()
        mock_repo.config_writer.side_effect = Exception("Config error")

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo
        manager._configure_credentials()  # Should not raise


class TestInitRepository:
    """Tests for init_repository method."""

    def test_init_repository_opens_existing_valid_repo(self, mocker, tmp_path):
        """Test opening an existing valid repository."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        mock_repo = MagicMock()
        mock_repo.remotes = {}
        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.return_value = mock_repo

        manager = GitManager(repo_path, "https://github.com/user/repo.git", "main")
        result = manager.init_repository()

        assert result == mock_repo
        assert manager.repo == mock_repo
        mock_repo_class.assert_called_once_with(repo_path)

    def test_init_repository_updates_remote_url_if_changed(self, mocker, tmp_path):
        """Test that remote URL is updated if it has changed."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        old_url = "https://github.com/user/old-repo.git"
        new_url = "https://github.com/user/new-repo.git"

        mock_origin = MagicMock()
        mock_origin.urls = [old_url]

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes

        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.return_value = mock_repo

        manager = GitManager(repo_path, new_url, "main")
        manager.init_repository()

        mock_origin.set_url.assert_called_once_with(new_url)

    def test_init_repository_adds_remote_if_missing(self, mocker, tmp_path):
        """Test that remote is added if it doesn't exist."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=False)

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes

        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.return_value = mock_repo

        manager = GitManager(repo_path, "https://github.com/user/repo.git", "main")
        manager.init_repository()

        mock_repo.create_remote.assert_called_once_with(
            "origin", "https://github.com/user/repo.git"
        )

    def test_init_repository_handles_invalid_repo(self, mocker, tmp_path):
        """Test handling of invalid git repository (removes and re-clones)."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / "dummy.txt").write_text("not a git repo")

        mock_repo = MagicMock()
        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.side_effect = [InvalidGitRepositoryError, mock_repo]
        mock_repo_class.clone_from.return_value = mock_repo

        mocker.patch("shutil.rmtree")

        manager = GitManager(repo_path, "https://github.com/user/repo.git", "main")
        result = manager.init_repository()

        assert result == mock_repo
        shutil.rmtree.assert_called_once_with(repo_path)
        mock_repo_class.clone_from.assert_called_once_with(
            "https://github.com/user/repo.git", repo_path
        )

    def test_init_repository_clones_if_not_exists(self, mocker, tmp_path):
        """Test cloning repository if path doesn't exist."""
        repo_path = tmp_path / "repo"

        mock_repo = MagicMock()
        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.clone_from.return_value = mock_repo

        manager = GitManager(repo_path, "https://github.com/user/repo.git", "main")
        result = manager.init_repository()

        assert result == mock_repo
        mock_repo_class.clone_from.assert_called_once_with(
            "https://github.com/user/repo.git", repo_path
        )

    def test_init_repository_clone_failure_raises_error(self, mocker, tmp_path):
        """Test that clone failures raise GitSyncError."""
        repo_path = tmp_path / "repo"

        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.clone_from.side_effect = GitCommandError("clone", "Clone failed")

        manager = GitManager(repo_path, "https://github.com/user/repo.git", "main")

        with pytest.raises(GitSyncError, match="Failed to clone repository"):
            manager.init_repository()

    def test_init_repository_creates_new_local_repo_without_url(self, mocker, tmp_path):
        """Test creating a new local repository when no URL is provided."""
        repo_path = tmp_path / "repo"

        mock_repo = MagicMock()
        mock_repo.heads = []  # Empty repo
        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.init.return_value = mock_repo

        manager = GitManager(repo_path, "", "main")
        result = manager.init_repository()

        assert result == mock_repo
        assert repo_path.exists()
        mock_repo_class.init.assert_called_once_with(repo_path)

    def test_init_repository_creates_initial_commit(self, mocker, tmp_path):
        """Test that initial commit is created for empty repository."""
        repo_path = tmp_path / "repo"

        mock_index = MagicMock()
        mock_repo = MagicMock()
        mock_repo.heads = []  # Empty repo
        mock_repo.index = mock_index

        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.init.return_value = mock_repo

        manager = GitManager(repo_path, "", "main")
        manager.init_repository()

        # Verify README was created
        readme_path = repo_path / "README.md"
        assert readme_path.exists()
        content = readme_path.read_text()
        assert "OrcaSync Profiles" in content

        # Verify git operations
        mock_index.add.assert_called_once_with(["README.md"])
        mock_index.commit.assert_called_once_with("Initial commit")

    def test_init_repository_handles_remote_already_exists(self, mocker, tmp_path):
        """Test that existing remote doesn't cause error."""
        repo_path = tmp_path / "repo"

        mock_repo = MagicMock()
        mock_repo.heads = ["main"]
        mock_repo.create_remote.side_effect = GitCommandError("create_remote", "already exists")

        mock_repo_class = mocker.patch("orcasync.git_ops.Repo")
        mock_repo_class.init.return_value = mock_repo

        manager = GitManager(repo_path, "https://github.com/user/repo.git", "main")
        manager.init_repository()  # Should not raise


class TestEnsureBranch:
    """Tests for ensure_branch method."""

    def test_ensure_branch_raises_if_no_repo(self, tmp_path):
        """Test that ensure_branch raises error if repository not initialized."""
        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")

        with pytest.raises(GitSyncError, match="Repository not initialized"):
            manager.ensure_branch()

    def test_ensure_branch_creates_local_branch_if_missing(self, mocker, tmp_path):
        """Test creating a new local branch if it doesn't exist."""
        mock_head = MagicMock()

        mock_heads = MagicMock()
        mock_heads.__contains__ = MagicMock(return_value=False)
        mock_heads.__getitem__ = MagicMock(return_value=mock_head)

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=False)

        mock_repo = MagicMock()
        mock_repo.heads = mock_heads
        mock_repo.remotes = mock_remotes
        mock_repo.create_head.return_value = mock_head

        manager = GitManager(tmp_path, "", "feature-branch")
        manager.repo = mock_repo
        manager.ensure_branch()

        mock_repo.create_head.assert_called_once_with("feature-branch", "HEAD")
        mock_head.checkout.assert_called_once()

    def test_ensure_branch_creates_from_remote_if_exists(self, mocker, tmp_path):
        """Test creating local branch from remote if it exists."""
        mock_origin_ref = MagicMock()
        mock_origin_ref.name = "origin/feature-branch"

        mock_refs = MagicMock()
        mock_refs.__iter__ = MagicMock(return_value=iter([mock_origin_ref]))
        mock_refs.__getitem__ = MagicMock(return_value=mock_origin_ref)  # refs["feature-branch"]

        mock_origin = MagicMock()
        mock_origin.refs = mock_refs

        mock_head = MagicMock()

        mock_heads = MagicMock()
        mock_heads.__contains__ = MagicMock(return_value=False)
        mock_heads.__getitem__ = MagicMock(return_value=mock_head)

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.heads = mock_heads
        mock_repo.remotes = mock_remotes
        mock_repo.create_head.return_value = mock_head

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "feature-branch")
        manager.repo = mock_repo
        manager.ensure_branch()

        mock_origin.fetch.assert_called_once()
        mock_repo.create_head.assert_called_once_with("feature-branch", "origin/feature-branch")
        mock_head.set_tracking_branch.assert_called_once_with(mock_origin_ref)

    def test_ensure_branch_handles_fetch_failure(self, mocker, tmp_path):
        """Test graceful handling of fetch failures."""
        mock_origin = MagicMock()
        mock_origin.fetch.side_effect = GitCommandError("fetch", "network error")

        mock_head = MagicMock()

        mock_heads = MagicMock()
        mock_heads.__contains__ = MagicMock(return_value=False)
        mock_heads.__getitem__ = MagicMock(return_value=mock_head)

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.heads = mock_heads
        mock_repo.remotes = mock_remotes
        mock_repo.create_head.return_value = mock_head

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo
        manager.ensure_branch()

        # Should create local branch despite fetch failure
        mock_repo.create_head.assert_called_once_with("main", "HEAD")

    def test_ensure_branch_checks_out_existing_branch(self, mocker, tmp_path):
        """Test checking out an existing branch."""
        mock_head = MagicMock()

        mock_heads = MagicMock()
        mock_heads.__contains__ = MagicMock(return_value=True)
        mock_heads.__getitem__ = MagicMock(return_value=mock_head)

        mock_repo = MagicMock()
        mock_repo.heads = mock_heads

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo
        manager.ensure_branch()

        mock_head.checkout.assert_called_once()


class TestSyncFiles:
    """Tests for sync_files method."""

    def test_sync_files_raises_if_no_repo(self, tmp_path):
        """Test that sync_files raises error if repository not initialized."""
        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")

        with pytest.raises(GitSyncError, match="Repository not initialized"):
            manager.sync_files([tmp_path])

    def test_sync_files_copies_directory_tree(self, tmp_path):
        """Test that sync_files copies entire directory tree."""
        # Setup source directory
        source_dir = tmp_path / "source" / "user"
        source_dir.mkdir(parents=True)
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "subdir").mkdir()
        (source_dir / "subdir" / "file2.txt").write_text("content2")

        # Setup repo
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        # Sync files
        copied = manager.sync_files([source_dir])

        # Verify files were copied
        target_dir = repo_path / "profiles" / "user"
        assert (target_dir / "file1.txt").exists()
        assert (target_dir / "subdir" / "file2.txt").exists()
        assert len(copied) == 2

    def test_sync_files_replaces_existing_directory(self, tmp_path):
        """Test that sync_files replaces existing directory."""
        source_dir = tmp_path / "source" / "user"
        source_dir.mkdir(parents=True)
        (source_dir / "new.txt").write_text("new")

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        target_dir = repo_path / "profiles" / "user"
        target_dir.mkdir(parents=True)
        (target_dir / "old.txt").write_text("old")

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        manager.sync_files([source_dir])

        # Old file should be gone
        assert not (target_dir / "old.txt").exists()
        # New file should exist
        assert (target_dir / "new.txt").exists()

    def test_sync_files_skips_nonexistent_source(self, tmp_path):
        """Test that sync_files skips nonexistent source directories."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        nonexistent = tmp_path / "nonexistent"
        copied = manager.sync_files([nonexistent])

        assert len(copied) == 0

    def test_sync_files_handles_multiple_sources(self, tmp_path):
        """Test syncing from multiple source directories."""
        source1 = tmp_path / "source1" / "user"
        source1.mkdir(parents=True)
        (source1 / "file1.txt").write_text("content1")

        source2 = tmp_path / "source2" / "system"
        source2.mkdir(parents=True)
        (source2 / "file2.txt").write_text("content2")

        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        copied = manager.sync_files([source1, source2])

        assert len(copied) == 2
        assert (repo_path / "profiles" / "user" / "file1.txt").exists()
        assert (repo_path / "profiles" / "system" / "file2.txt").exists()

    def test_sync_files_custom_target_subdir(self, tmp_path):
        """Test syncing to custom target subdirectory."""
        source_dir = tmp_path / "source" / "data"
        source_dir.mkdir(parents=True)
        (source_dir / "file.txt").write_text("content")

        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        manager.sync_files([source_dir], target_subdir="custom")

        assert (repo_path / "custom" / "data" / "file.txt").exists()


class TestRestoreFiles:
    """Tests for restore_files method."""

    def test_restore_files_raises_if_no_repo(self, tmp_path):
        """Test that restore_files raises error if repository not initialized."""
        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")

        with pytest.raises(GitSyncError, match="Repository not initialized"):
            manager.restore_files([tmp_path])

    def test_restore_files_returns_empty_if_source_missing(self, tmp_path):
        """Test that restore_files returns empty list if source doesn't exist."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        target = tmp_path / "target"
        restored = manager.restore_files([target])

        assert len(restored) == 0

    def test_restore_files_copies_directory_tree(self, tmp_path):
        """Test that restore_files copies entire directory tree."""
        # Setup source in repo
        repo_path = tmp_path / "repo"
        source_dir = repo_path / "profiles" / "user"
        source_dir.mkdir(parents=True)
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "subdir").mkdir()
        (source_dir / "subdir" / "file2.txt").write_text("content2")

        # Setup target
        target_dir = tmp_path / "target" / "user"

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        restored = manager.restore_files([target_dir])

        assert (target_dir / "file1.txt").exists()
        assert (target_dir / "subdir" / "file2.txt").exists()
        assert len(restored) == 2

    def test_restore_files_replaces_existing_directory(self, tmp_path):
        """Test that restore_files replaces existing target directory."""
        # Setup source
        repo_path = tmp_path / "repo"
        source_dir = repo_path / "profiles" / "user"
        source_dir.mkdir(parents=True)
        (source_dir / "new.txt").write_text("new")

        # Setup existing target
        target_dir = tmp_path / "target" / "user"
        target_dir.mkdir(parents=True)
        (target_dir / "old.txt").write_text("old")

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        manager.restore_files([target_dir])

        assert not (target_dir / "old.txt").exists()
        assert (target_dir / "new.txt").exists()

    def test_restore_files_creates_parent_directories(self, tmp_path):
        """Test that restore_files creates parent directories if needed."""
        repo_path = tmp_path / "repo"
        source_dir = repo_path / "profiles" / "user"
        source_dir.mkdir(parents=True)
        (source_dir / "file.txt").write_text("content")

        target_dir = tmp_path / "deep" / "nested" / "path" / "user"

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        manager.restore_files([target_dir])

        assert target_dir.exists()
        assert (target_dir / "file.txt").exists()

    def test_restore_files_skips_missing_source_subdirs(self, tmp_path):
        """Test that restore_files skips source subdirectories that don't exist."""
        repo_path = tmp_path / "repo"
        source_dir = repo_path / "profiles" / "user"
        source_dir.mkdir(parents=True)
        (source_dir / "file.txt").write_text("content")

        target1 = tmp_path / "target1" / "user"
        target2 = tmp_path / "target2" / "nonexistent"

        mock_repo = MagicMock()
        manager = GitManager(repo_path, "", "main")
        manager.repo = mock_repo

        restored = manager.restore_files([target1, target2])

        assert len(restored) == 1
        assert (target1 / "file.txt").exists()
        assert not target2.exists()


class TestCommitChanges:
    """Tests for commit_changes method."""

    def test_commit_changes_raises_if_no_repo(self, tmp_path):
        """Test that commit_changes raises error if repository not initialized."""
        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")

        with pytest.raises(GitSyncError, match="Repository not initialized"):
            manager.commit_changes()

    def test_commit_changes_returns_false_if_nothing_to_commit(self, mocker, tmp_path):
        """Test that commit_changes returns False when there are no changes."""
        mock_git = MagicMock()
        mock_repo = MagicMock()
        mock_repo.git = mock_git
        mock_repo.is_dirty.return_value = False
        mock_repo.untracked_files = []

        manager = GitManager(tmp_path, "", "main")
        manager.repo = mock_repo

        result = manager.commit_changes()

        assert result is False
        mock_git.add.assert_called_once_with(A=True)
        mock_repo.index.commit.assert_not_called()

    def test_commit_changes_commits_dirty_files(self, mocker, tmp_path):
        """Test that commit_changes commits dirty files."""
        mocker.patch("platform.node", return_value="testhost")

        mock_git = MagicMock()
        mock_index = MagicMock()
        mock_repo = MagicMock()
        mock_repo.git = mock_git
        mock_repo.index = mock_index
        mock_repo.is_dirty.return_value = True
        mock_repo.untracked_files = []

        manager = GitManager(tmp_path, "", "main")
        manager.repo = mock_repo

        result = manager.commit_changes()

        assert result is True
        mock_git.add.assert_called_once_with(A=True)
        mock_index.commit.assert_called_once()
        commit_message = mock_index.commit.call_args[0][0]
        assert "testhost" in commit_message

    def test_commit_changes_commits_untracked_files(self, mocker, tmp_path):
        """Test that commit_changes commits untracked files."""
        mocker.patch("platform.node", return_value="testhost")

        mock_git = MagicMock()
        mock_index = MagicMock()
        mock_repo = MagicMock()
        mock_repo.git = mock_git
        mock_repo.index = mock_index
        mock_repo.is_dirty.return_value = False
        mock_repo.untracked_files = ["new_file.txt"]

        manager = GitManager(tmp_path, "", "main")
        manager.repo = mock_repo

        result = manager.commit_changes()

        assert result is True
        mock_index.commit.assert_called_once()

    def test_commit_changes_uses_custom_message(self, mocker, tmp_path):
        """Test that commit_changes uses custom message when provided."""
        mock_git = MagicMock()
        mock_index = MagicMock()
        mock_repo = MagicMock()
        mock_repo.git = mock_git
        mock_repo.index = mock_index
        mock_repo.is_dirty.return_value = True

        manager = GitManager(tmp_path, "", "main")
        manager.repo = mock_repo

        custom_message = "Custom commit message"
        manager.commit_changes(message=custom_message)

        mock_index.commit.assert_called_once_with(custom_message)

    def test_commit_changes_generates_timestamp_in_message(self, mocker, tmp_path):
        """Test that auto-generated message includes timestamp."""
        mocker.patch("platform.node", return_value="testhost")
        mock_datetime = mocker.patch("orcasync.git_ops.datetime")
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2024-01-01 12:00:00"
        mock_datetime.now.return_value = mock_now

        mock_git = MagicMock()
        mock_index = MagicMock()
        mock_repo = MagicMock()
        mock_repo.git = mock_git
        mock_repo.index = mock_index
        mock_repo.is_dirty.return_value = True

        manager = GitManager(tmp_path, "", "main")
        manager.repo = mock_repo

        manager.commit_changes()

        commit_message = mock_index.commit.call_args[0][0]
        assert "2024-01-01 12:00:00" in commit_message


class TestPush:
    """Tests for push method."""

    def test_push_raises_if_no_repo(self, tmp_path):
        """Test that push raises error if repository not initialized."""
        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")

        with pytest.raises(GitSyncError, match="Repository not initialized"):
            manager.push()

    def test_push_raises_if_no_remote(self, mocker, tmp_path):
        """Test that push raises error if no remote configured."""
        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=False)

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes

        manager = GitManager(tmp_path, "", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="No remote 'origin' configured"):
            manager.push()

    def test_push_sets_upstream_on_first_push(self, mocker, tmp_path):
        """Test that push sets upstream on first push."""
        mock_branch = MagicMock()
        mock_branch.tracking_branch.return_value = None

        mock_origin = MagicMock()
        mock_push_info = MagicMock()
        mock_push_info.flags = 0  # No flags = success
        # Mock the flag constants to avoid bitwise check issues
        mock_push_info.ERROR = 1
        mock_push_info.REJECTED = 2
        mock_push_info.REMOTE_REJECTED = 4
        mock_push_info.REMOTE_FAILURE = 8
        mock_origin.push.return_value = [mock_push_info]

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        manager.push()

        mock_origin.push.assert_called_once()
        call_kwargs = mock_origin.push.call_args[1]
        assert call_kwargs["set_upstream"] is True
        assert call_kwargs["refspec"] == "main:main"

    def test_push_regular_push_with_tracking(self, mocker, tmp_path):
        """Test regular push when tracking branch is set."""
        mock_tracking = MagicMock()

        mock_branch = MagicMock()
        mock_branch.tracking_branch.return_value = mock_tracking

        mock_origin = MagicMock()
        mock_push_info = MagicMock()
        mock_push_info.flags = 0
        # Mock flag constants
        mock_push_info.ERROR = 1
        mock_push_info.REJECTED = 2
        mock_push_info.REMOTE_REJECTED = 4
        mock_push_info.REMOTE_FAILURE = 8
        mock_origin.push.return_value = [mock_push_info]

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        manager.push()

        mock_origin.push.assert_called_once_with("main", env=mocker.ANY)

    def test_push_disables_terminal_prompts(self, mocker, tmp_path):
        """Test that push disables terminal prompts for credentials."""
        mock_branch = MagicMock()
        mock_branch.tracking_branch.return_value = MagicMock()

        mock_origin = MagicMock()
        mock_push_info = MagicMock()
        mock_push_info.flags = 0
        # Mock flag constants
        mock_push_info.ERROR = 1
        mock_push_info.REJECTED = 2
        mock_push_info.REMOTE_REJECTED = 4
        mock_push_info.REMOTE_FAILURE = 8
        mock_origin.push.return_value = [mock_push_info]

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        manager.push()

        call_env = mock_origin.push.call_args[1]["env"]
        assert call_env["GIT_TERMINAL_PROMPT"] == "0"

    def test_push_handles_error_flag(self, mocker, tmp_path):
        """Test that push handles ERROR flag in push result."""
        mock_branch = MagicMock()
        mock_branch.tracking_branch.return_value = MagicMock()

        mock_push_info = MagicMock()
        mock_push_info.flags = mock_push_info.ERROR
        mock_push_info.summary = "Error message"

        mock_origin = MagicMock()
        mock_origin.push.return_value = [mock_push_info]

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="Push failed"):
            manager.push()

    def test_push_handles_rejected_flag(self, mocker, tmp_path):
        """Test that push handles REJECTED flag in push result."""
        mock_branch = MagicMock()
        mock_branch.tracking_branch.return_value = MagicMock()

        mock_push_info = MagicMock()
        # Set flag constants
        mock_push_info.ERROR = 1
        mock_push_info.REJECTED = 2
        mock_push_info.REMOTE_REJECTED = 4
        mock_push_info.REMOTE_FAILURE = 8
        mock_push_info.flags = 2  # Only REJECTED flag set
        mock_push_info.summary = "Rejected"

        mock_origin = MagicMock()
        mock_origin.push.return_value = [mock_push_info]

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="Push rejected"):
            manager.push()

    def test_push_authentication_error_message(self, mocker, tmp_path):
        """Test authentication error provides helpful message."""
        mock_branch = MagicMock()
        mock_origin = MagicMock()
        mock_origin.push.side_effect = GitCommandError("push", "authentication failed")

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="Authentication failed"):
            manager.push()

    def test_push_authentication_error_macos_help(self, mocker, tmp_path):
        """Test authentication error includes macOS-specific help."""
        mocker.patch("platform.system", return_value="Darwin")

        mock_branch = MagicMock()
        mock_origin = MagicMock()
        mock_origin.push.side_effect = GitCommandError("push", "authentication failed")

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="Solutions for macOS"):
            manager.push()

    def test_push_404_error_message(self, mocker, tmp_path):
        """Test 404 error provides helpful message."""
        mock_branch = MagicMock()
        mock_origin = MagicMock()
        mock_origin.push.side_effect = GitCommandError("push", "repository not found (404)")

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="Repository not found"):
            manager.push()

    def test_push_non_fast_forward_error(self, mocker, tmp_path):
        """Test non-fast-forward error suggests pulling first."""
        mock_branch = MagicMock()
        mock_origin = MagicMock()
        mock_origin.push.side_effect = GitCommandError("push", "non-fast-forward")

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = mock_branch

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="Run 'orcasync pull' first"):
            manager.push()


class TestPull:
    """Tests for pull method."""

    def test_pull_raises_if_no_repo(self, tmp_path):
        """Test that pull raises error if repository not initialized."""
        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")

        with pytest.raises(GitSyncError, match="Repository not initialized"):
            manager.pull()

    def test_pull_raises_if_no_remote(self, mocker, tmp_path):
        """Test that pull raises error if no remote configured."""
        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=False)

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes

        manager = GitManager(tmp_path, "", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="No remote 'origin' configured"):
            manager.pull()

    def test_pull_with_no_changes(self, mocker, tmp_path):
        """Test pull when there are no remote changes."""
        mock_commit = MagicMock()
        mock_head = MagicMock()
        mock_head.commit = mock_commit

        mock_origin = MagicMock()

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.head = mock_head

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        has_changes, changed_files = manager.pull()

        assert has_changes is False
        assert changed_files == []
        mock_origin.pull.assert_called_once_with("main", rebase=True)

    def test_pull_with_changes(self, mocker, tmp_path):
        """Test pull when there are remote changes."""
        old_commit = MagicMock()
        new_commit = MagicMock()

        mock_diff_item = MagicMock()
        mock_diff_item.a_path = "changed_file.txt"
        old_commit.diff.return_value = [mock_diff_item]

        mock_head = MagicMock()
        mock_head.commit = old_commit

        mock_origin = MagicMock()

        def pull_side_effect(*args, **kwargs):
            mock_head.commit = new_commit

        mock_origin.pull.side_effect = pull_side_effect

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.head = mock_head

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        has_changes, changed_files = manager.pull()

        assert has_changes is True
        assert "changed_file.txt" in changed_files

    def test_pull_uses_rebase_strategy(self, mocker, tmp_path):
        """Test that pull uses rebase strategy by default."""
        mock_commit = MagicMock()
        mock_head = MagicMock()
        mock_head.commit = mock_commit

        mock_origin = MagicMock()

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.head = mock_head

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        manager.pull()

        mock_origin.pull.assert_called_once_with("main", rebase=True)

    def test_pull_falls_back_to_merge_on_divergent_branches(self, mocker, tmp_path):
        """Test that pull falls back to merge strategy on divergent branches."""
        mock_commit = MagicMock()
        mock_head = MagicMock()
        mock_head.commit = mock_commit

        mock_origin = MagicMock()
        mock_origin.pull.side_effect = [
            GitCommandError("pull", "divergent branches"),
            None,  # Second call succeeds
        ]

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.head = mock_head

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        manager.pull()

        # First call with rebase, second with merge
        assert mock_origin.pull.call_count == 2
        calls = mock_origin.pull.call_args_list
        assert calls[0][1]["rebase"] is True
        assert calls[1][1]["rebase"] is False

    def test_pull_raises_on_merge_failure(self, mocker, tmp_path):
        """Test that pull raises error if merge fallback also fails."""
        mock_head = MagicMock()

        mock_origin = MagicMock()
        mock_origin.pull.side_effect = [
            GitCommandError("pull", "divergent branches"),
            GitCommandError("pull", "merge conflict"),
        ]

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.head = mock_head

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="Failed to pull and merge"):
            manager.pull()

    def test_pull_general_error(self, mocker, tmp_path):
        """Test that pull handles general errors."""
        mock_head = MagicMock()

        mock_origin = MagicMock()
        mock_origin.pull.side_effect = GitCommandError("pull", "network error")

        mock_remotes = MagicMock()
        mock_remotes.__contains__ = MagicMock(return_value=True)
        mock_remotes.origin = mock_origin

        mock_repo = MagicMock()
        mock_repo.remotes = mock_remotes
        mock_repo.head = mock_head

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        with pytest.raises(GitSyncError, match="Failed to pull"):
            manager.pull()


class TestGetStatus:
    """Tests for get_status method."""

    def test_get_status_not_initialized(self, tmp_path):
        """Test get_status when repository is not initialized."""
        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")

        status = manager.get_status()

        assert status == {"initialized": False}

    def test_get_status_clean_repo(self, mocker, tmp_path):
        """Test get_status with a clean repository."""
        mock_branch = MagicMock()
        mock_branch.name = "main"

        mock_repo = MagicMock()
        mock_repo.active_branch = mock_branch
        mock_repo.is_dirty.return_value = False
        mock_repo.untracked_files = []
        mock_repo.remotes = {"origin": MagicMock()}

        manager = GitManager(tmp_path, "https://github.com/user/repo.git", "main")
        manager.repo = mock_repo

        status = manager.get_status()

        assert status["initialized"] is True
        assert status["branch"] == "main"
        assert status["dirty"] is False
        assert status["untracked_files"] == 0
        assert status["has_remote"] is True

    def test_get_status_dirty_repo(self, mocker, tmp_path):
        """Test get_status with a dirty repository."""
        mock_branch = MagicMock()
        mock_branch.name = "feature"

        mock_repo = MagicMock()
        mock_repo.active_branch = mock_branch
        mock_repo.is_dirty.return_value = True
        mock_repo.untracked_files = ["file1.txt", "file2.txt"]
        mock_repo.remotes = {}

        manager = GitManager(tmp_path, "", "feature")
        manager.repo = mock_repo

        status = manager.get_status()

        assert status["initialized"] is True
        assert status["branch"] == "feature"
        assert status["dirty"] is True
        assert status["untracked_files"] == 2
        assert status["has_remote"] is False
