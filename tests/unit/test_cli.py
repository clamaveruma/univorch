"""Tests for the CLI shell: path resolution and navigation (C1)."""

import io

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.interfaces.cli.app import UnivOrchShell, build_service
from univorch.models import ApplyDocument, Folder


@pytest.fixture
def shell() -> UnivOrchShell:
    return UnivOrchShell(build_service(TinyDB(storage=MemoryStorage)))


def _run(shell: UnivOrchShell, line: str) -> str:
    """Run one command and capture what it printed."""
    buffer = io.StringIO()
    shell.stdout = buffer
    shell.onecmd_plus_hooks(line)
    return buffer.getvalue()


class TestResolve:
    def test_absolute_path_unchanged(self, shell: UnivOrchShell) -> None:
        assert shell._resolve("/lab/vm") == "/lab/vm"

    def test_relative_from_root(self, shell: UnivOrchShell) -> None:
        assert shell._resolve("lab") == "/lab"

    def test_relative_from_subfolder(self, shell: UnivOrchShell) -> None:
        shell._cwd = "/lab"
        assert shell._resolve("networks") == "/lab/networks"

    def test_empty_is_current_folder(self, shell: UnivOrchShell) -> None:
        shell._cwd = "/lab"
        assert shell._resolve("") == "/lab"


class TestNavigation:
    def test_cd_absolute_then_pwd(self, shell: UnivOrchShell) -> None:
        shell.onecmd_plus_hooks("cd /lab/networks")
        assert shell._cwd == "/lab/networks"
        assert "/lab/networks" in _run(shell, "pwd")

    def test_cd_relative_chains(self, shell: UnivOrchShell) -> None:
        shell.onecmd_plus_hooks("cd lab")
        shell.onecmd_plus_hooks("cd networks")
        assert shell._cwd == "/lab/networks"

    def test_cd_no_arg_goes_to_root(self, shell: UnivOrchShell) -> None:
        shell.onecmd_plus_hooks("cd /lab")
        shell.onecmd_plus_hooks("cd")
        assert shell._cwd == "/"


class TestList:
    def test_lists_subtree(self, shell: UnivOrchShell) -> None:
        shell._service.apply(
            ApplyDocument(folders=[Folder(path="/lab"), Folder(path="/lab/networks")])
        )
        out = _run(shell, "list /")
        assert "/lab" in out
        assert "/lab/networks" in out
        assert "folder" in out
