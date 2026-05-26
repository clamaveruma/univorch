"""Tests for the CLI shell: path resolution and navigation (C1)."""

import io
from pathlib import Path

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.interfaces.cli.app import UnivOrchShell, build_service
from univorch.models import ApplyDocument, Descriptor, Folder


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

    def test_dotdot_goes_up(self, shell: UnivOrchShell) -> None:
        shell._cwd = "/lab/networks"
        assert shell._resolve("..") == "/lab"

    def test_dotdot_combined(self, shell: UnivOrchShell) -> None:
        shell._cwd = "/lab/networks"
        assert shell._resolve("../other") == "/lab/other"

    def test_dot_is_current(self, shell: UnivOrchShell) -> None:
        shell._cwd = "/lab"
        assert shell._resolve(".") == "/lab"

    def test_dotdot_at_root_stays(self, shell: UnivOrchShell) -> None:
        assert shell._resolve("..") == "/"


def _mkdir(shell: UnivOrchShell, *paths: str) -> None:
    shell._service.apply(ApplyDocument(folders=[Folder(path=p) for p in paths]))


class TestNavigation:
    def test_cd_absolute_then_pwd(self, shell: UnivOrchShell) -> None:
        _mkdir(shell, "/lab", "/lab/networks")
        shell.onecmd_plus_hooks("cd /lab/networks")
        assert shell._cwd == "/lab/networks"
        assert "/lab/networks" in _run(shell, "pwd")

    def test_cd_relative_chains(self, shell: UnivOrchShell) -> None:
        _mkdir(shell, "/lab", "/lab/networks")
        shell.onecmd_plus_hooks("cd lab")
        shell.onecmd_plus_hooks("cd networks")
        assert shell._cwd == "/lab/networks"

    def test_cd_no_arg_stays(self, shell: UnivOrchShell) -> None:
        _mkdir(shell, "/lab")
        shell.onecmd_plus_hooks("cd /lab")
        shell.onecmd_plus_hooks("cd")
        assert shell._cwd == "/lab"  # no-op

    def test_cd_dotdot_goes_to_parent(self, shell: UnivOrchShell) -> None:
        _mkdir(shell, "/lab", "/lab/networks")
        shell.onecmd_plus_hooks("cd /lab/networks")
        shell.onecmd_plus_hooks("cd ..")
        assert shell._cwd == "/lab"

    def test_cd_missing_folder_stays(self, shell: UnivOrchShell) -> None:
        _mkdir(shell, "/lab")
        shell.onecmd_plus_hooks("cd /lab")
        shell.onecmd_plus_hooks("cd /nope")  # does not exist
        assert shell._cwd == "/lab"  # unchanged

    def test_cd_into_descriptor_stays(self, shell: UnivOrchShell) -> None:
        _provision(shell)  # creates /lab folder + /lab/vm descriptor
        shell.onecmd_plus_hooks("cd /lab/vm")  # a descriptor is not a folder
        assert shell._cwd == "/"  # no move


class TestList:
    def test_lists_subtree(self, shell: UnivOrchShell) -> None:
        shell._service.apply(
            ApplyDocument(folders=[Folder(path="/lab"), Folder(path="/lab/networks")])
        )
        out = _run(shell, "list /")
        assert "/lab" in out
        assert "/lab/networks" in out
        assert "folder" in out


def _provision(shell: UnivOrchShell) -> None:
    shell._service.apply(
        ApplyDocument(
            folders=[Folder(path="/lab")],
            descriptors=[
                Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
            ],
        )
    )


class TestMachineCommands:
    def test_deploy_then_status(self, shell: UnivOrchShell) -> None:
        _provision(shell)
        assert "deployed" in _run(shell, "deploy /lab/vm")
        out = _run(shell, "status /lab/vm")
        assert "deployed" in out  # descriptor state
        assert "stopped" in out  # runtime: freshly cloned

    def test_start_changes_runtime(self, shell: UnivOrchShell) -> None:
        _provision(shell)
        _run(shell, "deploy /lab/vm")
        _run(shell, "start /lab/vm")
        assert "running" in _run(shell, "status /lab/vm")

    def test_full_lifecycle(self, shell: UnivOrchShell) -> None:
        _provision(shell)
        _run(shell, "deploy /lab/vm")
        _run(shell, "start /lab/vm")
        assert "stopped" in _run(shell, "stop /lab/vm")
        assert "undeployed" in _run(shell, "undeploy /lab/vm")
        assert "provisioned" in _run(shell, "status /lab/vm")

    def test_status_provisioned_has_no_runtime(self, shell: UnivOrchShell) -> None:
        _provision(shell)
        out = _run(shell, "status /lab/vm")
        assert "provisioned" in out

    def test_unknown_path_shows_no_success(self, shell: UnivOrchShell) -> None:
        assert "deployed" not in _run(shell, "deploy /lab/nope")

    def test_status_unknown_shows_no_state(self, shell: UnivOrchShell) -> None:
        out = _run(shell, "status /lab/nope")
        assert "deployed" not in out and "provisioned" not in out


class TestApplyCommand:
    def test_applies_a_yaml_file(self, shell: UnivOrchShell, tmp_path: Path) -> None:
        f = tmp_path / "setup.yml"
        f.write_text(
            "kind: apply\n"
            "folders:\n  - path: /lab\n"
            "descriptors:\n"
            "  - path: /lab/vm\n    hypervisor: mock\n    base_vm: linux-base\n"
        )
        out = _run(shell, f"apply {f}")
        assert "/lab" in out  # report mentions the created items
        assert "/lab/vm" in _run(shell, "list /")  # tree was created

    def test_missing_file_creates_nothing(self, shell: UnivOrchShell) -> None:
        _run(shell, "apply /nope/missing.yml")  # error to stderr, no crash
        assert "/lab" not in _run(shell, "list /")
