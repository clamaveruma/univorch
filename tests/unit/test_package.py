"""Sanity check: verifies the package is importable and versioned correctly."""

import univorch


def test_package_is_importable() -> None:
    """The univorch package must be importable after installation."""
    assert univorch.__version__ == "0.1.0"
