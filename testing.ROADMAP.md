# Plan: Comprehensive Testing System for OrcaSync (Revised)

Build a robust, multi-layered testing infrastructure with pytest covering unit, integration, CLI, TUI snapshot, and performance tests. Address 0% functional coverage across 1,712 lines with focus on pytest-mock, benchmark testing, and Textual snapshots. Remove WSL dependency for cleaner, more maintainable codebase.

## Steps

1. ✅ **Set up pytest infrastructure and WSL removal** - COMPLETED
   - ✅ Updated [pyproject.toml](pyproject.toml) with pytest-cov, pytest-mock, pytest-benchmark, pytest-asyncio, and textual[dev]
   - ✅ Created `tests/conftest.py` with shared fixtures (mock_git_repo, mock_orcaslicer_dir, tmp_config_dir using mocker fixture)
   - ✅ Removed WSL detection code (lines 74-84) from [orcasync/config.py](orcasync/config.py#L74-L84)
   - ✅ Updated [README.md](README.md) and [TROUBLESHOOTING.md](TROUBLESHOOTING.md) with manual WSL path configuration examples

2. ✅ **Implement Config module unit tests** - COMPLETED
   - ✅ Created `tests/test_config.py` with 61 comprehensive tests covering all functionality
   - ✅ Tests cover `discover_orcaslicer_paths()` for Windows/macOS/Linux (WSL excluded as planned)
   - ✅ Tests cover YAML parsing (valid/invalid/missing/empty files)
   - ✅ Tests cover profile merging and platform detection with `mocker.patch('platform.system')`
   - ✅ Tests cover all property getters (repository_url, repository_name, branch_name, user_paths, system_paths, sync_paths)
   - ✅ Tests cover get/set methods, save functionality, and list_profiles
   - ✅ Tests cover edge cases: null values, unicode, special characters, long values, symlinks
   - ✅ **Achieved 100% coverage** of [orcasync/config.py](orcasync/config.py) (119 statements, 0 missed)
   - ✅ All 61 tests pass successfully

3. ✅ **Implement GitManager unit tests** - COMPLETED
   - ✅ Created `tests/test_git_ops.py` with 62 comprehensive tests covering all functionality
   - ✅ Tests cover repository initialization (clone vs create, existing repo handling)
   - ✅ Tests cover credential configuration for macOS/Windows/Linux platforms
   - ✅ Tests cover branch operations (create local, track remote, checkout, fetch failures)
   - ✅ Tests cover sync_files and restore_files with multiple sources/destinations
   - ✅ Tests cover commit workflows (dirty files, untracked files, custom messages, timestamps)
   - ✅ Tests cover push operations (upstream setting, error flags, authentication errors, 404s, non-fast-forward)
   - ✅ Tests cover pull operations (rebase strategy, merge fallback for divergent branches, error handling)
   - ✅ Tests cover status reporting and edge cases
   - ✅ **Achieved 96% coverage** of [orcasync/git_ops.py](orcasync/git_ops.py) (192 statements, 8 missed - error handling edge cases)
   - ✅ All 62 tests pass successfully

4. **Build integration and CLI test suites** - Create `tests/test_cli.py` using Click's `CliRunner` to test all commands in [orcasync/cli.py](orcasync/cli.py) (init/push/pull/sync/status/config-path with options). Create `tests/test_integration.py` with 30-40 tests using real temp git repos and directories for full push/pull/sync workflows, multi-path syncing, and error propagation.

5. **Add performance benchmarks** - Create `tests/benchmarks/test_sync_performance.py` and `tests/benchmarks/test_path_discovery.py` using pytest-benchmark plugin. Benchmark sync_files with small (100 files), medium (500 files), and large (2000 files) profiles. Set regression threshold at +20% with baseline comparisons. Include config loading (<50ms) and commit operations (<2s for medium profiles).

6. **Implement TUI snapshot tests** - Create `tests/test_tui_snapshots.py` using Textual's built-in snapshot testing with `app.run_test()` and `snap_compare()`. Test StatusPanel (empty/loaded/dirty states), InitDialog (auto-detected vs manual paths), CompactLogView (empty/populated/100+ messages), main screen rendering, and worker states from [orcasync/tui.py](orcasync/tui.py). SVG snapshots stored in `tests/snapshots/`. Target: 25-35 tests.

7. **Configure CI/CD and coverage reporting** - Create `.github/workflows/test.yml` with matrix testing (Ubuntu/macOS/Windows × Python 3.10-3.12), run pytest with `--cov --benchmark-skip` for coverage and separate benchmark job with `--benchmark-only`. Configure pytest.ini for coverage thresholds (>80%), integrate Codecov for PR reporting, and exclude WSL-specific tests. Add pre-commit hooks for black/flake8/mypy.

## Further Considerations

1. **WSL user migration path** - Update [README.md](README.md) and [TROUBLESHOOTING.md](TROUBLESHOOTING.md) with manual WSL path configuration examples showing how to set `/mnt/c/Users/.../AppData/Roaming/OrcaSlicer/user` in YAML. Should we add a deprecation notice in v0.2.0 changelog before removing in v0.3.0, or remove immediately?

2. **Benchmark baseline storage** - pytest-benchmark can store baselines in JSON for comparison. Should we: (A) Commit baselines to git for CI regression detection, (B) Store per-machine in .gitignore, or (C) Only fail on >20% regression without baseline? Recommend (A) for CI automation.

3. **Test execution speed** - With 135-195 total tests, runtime could be 2-5 minutes. Should we use pytest-xdist for parallel execution (`-n auto`) to speed up CI, or keep sequential for easier debugging? Recommend parallel in CI, sequential for local development.
