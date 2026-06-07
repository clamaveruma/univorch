"""Tests for the daemon entry point's helpers (Sprint 3.2 + pendiente 5.1).

Only the pure helpers are tested here; ``main()`` itself spins up uvicorn
and is exercised by the end-to-end manual checks rather than unit tests.
"""

from pathlib import Path

import pytest

from univorch.interfaces.rest.__main__ import _default_db_path


class TestDefaultDbPath:
    def test_uses_container_dir_when_writable(self, tmp_path: Path) -> None:
        # tmp_path stands in for /data: it exists and we can write to it.
        result = _default_db_path(container_dir=tmp_path)
        assert result == tmp_path / "univorch.json"

    def test_falls_back_to_xdg_when_container_dir_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Point XDG to a tmp dir so the test does not touch ~/.local/share
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        missing = tmp_path / "does-not-exist"
        result = _default_db_path(container_dir=missing)
        assert result == tmp_path / "xdg" / "univorch" / "db.json"

    def test_falls_back_to_home_when_container_dir_not_writable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Read-only directory simulates the case "exists but not writable":
        # /data could exist with wrong perms in some misconfigured deploys.
        readonly = tmp_path / "readonly"
        readonly.mkdir()
        readonly.chmod(0o555)  # r-x: not writable
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        # Use a fake HOME so the assertion doesn't depend on the real one.
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        result = _default_db_path(container_dir=readonly)
        # Without XDG_DATA_HOME we fall back to $HOME/.local/share
        assert result == tmp_path / "home" / ".local" / "share" / "univorch" / "db.json"
        # cleanup so pytest can remove the tmp tree
        readonly.chmod(0o755)

    def test_xdg_env_overrides_default_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # XDG spec: $XDG_DATA_HOME beats $HOME/.local/share when set.
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "custom-xdg"))
        result = _default_db_path(container_dir=tmp_path / "nope")
        assert result == tmp_path / "custom-xdg" / "univorch" / "db.json"
