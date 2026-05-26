"""Tests for the CLI shell: path resolution and navigation (C1)."""

import io
from pathlib import Path

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.interfaces.cli.app import UnivOrchShell, build_service
from univorch.models import DefinitionDocument, DescriptorDef, FolderDef


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
    """Seed folders by absolute path via the service.load mechanism.

    Each path is loaded as a leaf folder under its parent (which must already
    exist or be the root). Paths must be listed parent-first.
    """
    for path in paths:
        parent, name = path.rsplit("/", 1)
        parent = parent or "/"
        shell._service.load(
            DefinitionDocument(folders={name: FolderDef()}), destination=parent
        )


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
    def test_lists_direct_children_only(self, shell: UnivOrchShell) -> None:
        _mkdir(shell, "/lab", "/lab/networks")
        out = _run(shell, "list /")
        assert "lab/" in out  # direct child, ls -F style
        assert "networks" not in out  # one level only

    def test_parent_row_except_at_root(self, shell: UnivOrchShell) -> None:
        _mkdir(shell, "/lab")
        assert "../" not in _run(shell, "list /")  # root has no parent row
        assert "../" in _run(shell, "list /lab")

    def test_descriptor_shows_state_glyph(self, shell: UnivOrchShell) -> None:
        _provision(shell)  # /lab + /lab/vm (provisioned)
        out = _run(shell, "list /lab")
        assert "□ vm" in out  # provisioned glyph + basename

    def test_ls_is_alias_for_list(self, shell: UnivOrchShell) -> None:
        _mkdir(shell, "/lab")
        assert "lab/" in _run(shell, "ls /")

    def test_list_missing_folder_prints_nothing(self, shell: UnivOrchShell) -> None:
        assert _run(shell, "list /nope") == ""  # error goes to stderr


class TestTree:
    def test_shows_full_subtree(self, shell: UnivOrchShell) -> None:
        _provision(shell)  # /lab + /lab/vm
        out = _run(shell, "tree /")
        assert "lab/" in out
        assert "vm" in out  # descendant shown, not just direct children

    def test_missing_folder_prints_nothing(self, shell: UnivOrchShell) -> None:
        assert _run(shell, "tree /nope") == ""


def _provision(shell: UnivOrchShell) -> None:
    """Seed /lab + /lab/vm via load (vm is provisioned, ready for deploy)."""
    shell._service.load(
        DefinitionDocument(
            folders={
                "lab": FolderDef(
                    descriptors={
                        "vm": DescriptorDef(hypervisor="mock", base_vm="linux-base")
                    }
                )
            }
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


class TestLoadCommand:
    _YAML = (
        "kind: definition\n"
        "lab/:\n"
        "  vm:\n"
        "    hypervisor: mock\n"
        "    base_vm: linux-base\n"
    )

    def test_loads_at_root_by_default(
        self, shell: UnivOrchShell, tmp_path: Path
    ) -> None:
        f = tmp_path / "setup.yml"
        f.write_text(self._YAML)
        out = _run(shell, f"load {f}")  # no destination → pwd = /
        assert "/lab" in out  # report mentions the created items
        assert "vm" in _run(shell, "list /lab")  # tree got created

    def test_loads_at_explicit_destination(
        self, shell: UnivOrchShell, tmp_path: Path
    ) -> None:
        _mkdir(shell, "/area")  # destination must exist first
        f = tmp_path / "setup.yml"
        f.write_text(self._YAML)
        _run(shell, f"load {f} /area")
        assert "vm" in _run(shell, "list /area/lab")  # hung under /area

    def test_destination_missing_errors(
        self, shell: UnivOrchShell, tmp_path: Path
    ) -> None:
        f = tmp_path / "setup.yml"
        f.write_text(self._YAML)
        _run(shell, f"load {f} /nope")  # error to stderr
        assert "lab" not in _run(shell, "list /")  # nothing created

    def test_missing_file_creates_nothing(self, shell: UnivOrchShell) -> None:
        _run(shell, "load /nope/missing.yml")  # error to stderr, no crash
        assert "lab" not in _run(shell, "list /")
