#!/usr/bin/env python3
"""Quick test to verify TUI can be instantiated."""

from orcasync.tui import OrcaSyncApp
from orcasync.config import Config

# Test that the app can be created
app = OrcaSyncApp()
print("✓ TUI app created successfully")

# Test that config works
config = Config()
print(f"✓ Config loaded from: {config.config_path}")

# Test imports
from textual.app import App
from textual.widgets import Button, Header, Footer
print("✓ All Textual imports working")

print("\n[SUCCESS] TUI is ready to use!")
print("\nTo launch the TUI:")
print("  - Run: orcasync")
print("  - Or: uv run orcasync")
print("\nTo use CLI commands:")
print("  - Run: orcasync <command>")
print("  - Example: orcasync push")
