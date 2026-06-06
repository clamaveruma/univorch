"""Tests for the cascade-inheritance Resolver (Sprint 2 Pieza 1.B).

Two flavours: direct tests for the walker / merge mechanics, and Hypothesis
property tests for the merge function (pure, scalar-replace rule from DEC-026).
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.models import Descriptor, Folder, HypervisorDef, VMTemplateDef
from univorch.persistence.tinydb.repositories import FolderRepository
from univorch.resolver import (
    _find_hypervisor,
    _find_template,
    _import_allows,
    _merge_template,
    resolve_descriptor,
)


@pytest.fixture
def folders() -> FolderRepository:
    return FolderRepository(TinyDB(storage=MemoryStorage))


def _put_template(
    folders: FolderRepository,
    path: str,
    template_name: str,
    template: VMTemplateDef,
    imports: list[str] | None = None,
) -> None:
    """Helper: save a folder with one template (and optional imports)."""
    folders.save(
        Folder(
            path=path,
            vm_templates={template_name: template},
            imports=imports or [],
        )
    )


def _put_hypervisor(
    folders: FolderRepository,
    path: str,
    hypervisor_name: str,
    hypervisor: HypervisorDef,
    imports: list[str] | None = None,
) -> None:
    """Helper: save a folder with one hypervisor (and optional imports)."""
    folders.save(
        Folder(
            path=path,
            hypervisors={hypervisor_name: hypervisor},
            imports=imports or [],
        )
    )


class TestImportAllows:
    def test_empty_imports_match_nothing(self) -> None:
        assert not _import_allows([], "linux-vm")

    def test_wildcard_matches_everything(self) -> None:
        assert _import_allows(["*"], "anything")
        assert _import_allows(["*"], "linux-vm")

    def test_exact_name(self) -> None:
        assert _import_allows(["linux-vm"], "linux-vm")
        assert not _import_allows(["linux-vm"], "windows-vm")

    def test_prefix_wildcard(self) -> None:
        assert _import_allows(["hyperv-*"], "hyperv-aulario")
        assert _import_allows(["hyperv-*"], "hyperv-x")
        assert not _import_allows(["hyperv-*"], "vmware-prod")

    def test_multiple_patterns_or(self) -> None:
        assert _import_allows(["linux-*", "windows-*"], "linux-vm")
        assert _import_allows(["linux-*", "windows-*"], "windows-server")
        assert not _import_allows(["linux-*", "windows-*"], "freebsd")


class TestMergeTemplate:
    def test_template_fills_missing_fields(self) -> None:
        descriptor = Descriptor(path="/lab/vm", template="t")
        template = VMTemplateDef(hypervisor="mock", base_vm="linux-base", cpu=2)
        result = _merge_template(descriptor, template)
        assert result.hypervisor == "mock"
        assert result.base_vm == "linux-base"
        assert result.cpu == 2

    def test_local_value_wins_over_template(self) -> None:
        descriptor = Descriptor(
            path="/lab/vm", template="t", hypervisor="local-hv", cpu=4
        )
        template = VMTemplateDef(hypervisor="template-hv", base_vm="linux-base", cpu=2)
        result = _merge_template(descriptor, template)
        assert result.hypervisor == "local-hv"  # local wins
        assert result.cpu == 4  # local wins
        assert result.base_vm == "linux-base"  # filled from template

    def test_template_name_is_preserved(self) -> None:
        descriptor = Descriptor(path="/lab/vm", template="linux-vm")
        template = VMTemplateDef(hypervisor="mock", base_vm="linux-base")
        result = _merge_template(descriptor, template)
        assert result.template == "linux-vm"  # traceability

    def test_path_and_state_are_unchanged(self) -> None:
        descriptor = Descriptor(path="/lab/vm", template="t")
        template = VMTemplateDef(hypervisor="mock")
        result = _merge_template(descriptor, template)
        assert result.path == "/lab/vm"
        assert result.state == descriptor.state
        assert result.vm_id is None


class TestFindTemplate:
    def test_template_defined_locally(self, folders: FolderRepository) -> None:
        _put_template(folders, "/lab", "linux-vm", VMTemplateDef(hypervisor="mock"))
        result = _find_template("linux-vm", "/lab", folders)
        assert result is not None
        assert result.hypervisor == "mock"

    def test_template_in_parent_with_explicit_import(
        self, folders: FolderRepository
    ) -> None:
        _put_template(folders, "/lab", "linux-vm", VMTemplateDef(hypervisor="mock"))
        folders.save(Folder(path="/lab/networks", imports=["linux-vm"]))
        result = _find_template("linux-vm", "/lab/networks", folders)
        assert result is not None

    def test_template_in_parent_blocked_by_missing_import(
        self, folders: FolderRepository
    ) -> None:
        _put_template(folders, "/lab", "linux-vm", VMTemplateDef(hypervisor="mock"))
        folders.save(Folder(path="/lab/networks", imports=[]))
        assert _find_template("linux-vm", "/lab/networks", folders) is None

    def test_template_in_parent_with_import_ALL(
        self, folders: FolderRepository
    ) -> None:
        _put_template(folders, "/lab", "linux-vm", VMTemplateDef(hypervisor="mock"))
        # imports=["*"] is the normalised form of "import: ALL" (Pieza 1.A)
        folders.save(Folder(path="/lab/networks", imports=["*"]))
        assert _find_template("linux-vm", "/lab/networks", folders) is not None

    def test_template_through_two_levels_with_imports(
        self, folders: FolderRepository
    ) -> None:
        # /lab defines the template; both /lab/sub and /lab/sub/inner must
        # import it (or *) for the chain to reach the bottom.
        _put_template(folders, "/lab", "linux-vm", VMTemplateDef(hypervisor="mock"))
        folders.save(Folder(path="/lab/sub", imports=["*"]))
        folders.save(Folder(path="/lab/sub/inner", imports=["linux-vm"]))
        result = _find_template("linux-vm", "/lab/sub/inner", folders)
        assert result is not None

    def test_template_not_found_returns_none(self, folders: FolderRepository) -> None:
        folders.save(Folder(path="/lab"))
        assert _find_template("missing", "/lab", folders) is None

    def test_unknown_parent_folder_returns_none(
        self, folders: FolderRepository
    ) -> None:
        # asking from a folder that has no Folder record at all
        assert _find_template("anything", "/orphan/path", folders) is None

    def test_reaches_root_without_finding(self, folders: FolderRepository) -> None:
        # imports=["*"] at every level pass anything through, but no folder
        # actually defines the template → the walk reaches the (resource-less)
        # root and returns None
        folders.save(Folder(path="/lab", imports=["*"]))
        folders.save(Folder(path="/lab/inner", imports=["*"]))
        assert _find_template("missing", "/lab/inner", folders) is None


class TestFindHypervisor:
    """Walker for hypervisors: same rules as templates, but returns the path
    of the folder that defined the hypervisor — the service uses that path as
    the connection-pool key (Pieza 3c).
    """

    def test_hypervisor_defined_locally(self, folders: FolderRepository) -> None:
        _put_hypervisor(folders, "/lab", "mock", HypervisorDef(connector_type="mock"))
        result = _find_hypervisor("mock", "/lab", folders)
        assert result is not None
        hv, path = result
        assert hv.connector_type == "mock"
        assert path == "/lab"  # found here, this is the pool key

    def test_hypervisor_in_parent_with_explicit_import(
        self, folders: FolderRepository
    ) -> None:
        _put_hypervisor(folders, "/lab", "mock", HypervisorDef(connector_type="mock"))
        folders.save(Folder(path="/lab/networks", imports=["mock"]))
        result = _find_hypervisor("mock", "/lab/networks", folders)
        assert result is not None
        _, path = result
        assert path == "/lab"  # the folder that *defined* it, not the one asking

    def test_hypervisor_in_parent_blocked_by_missing_import(
        self, folders: FolderRepository
    ) -> None:
        _put_hypervisor(folders, "/lab", "mock", HypervisorDef(connector_type="mock"))
        folders.save(Folder(path="/lab/networks", imports=[]))
        assert _find_hypervisor("mock", "/lab/networks", folders) is None

    def test_hypervisor_in_parent_with_import_ALL(
        self, folders: FolderRepository
    ) -> None:
        _put_hypervisor(folders, "/lab", "mock", HypervisorDef(connector_type="mock"))
        folders.save(Folder(path="/lab/networks", imports=["*"]))
        assert _find_hypervisor("mock", "/lab/networks", folders) is not None

    def test_hypervisor_through_two_levels_with_imports(
        self, folders: FolderRepository
    ) -> None:
        _put_hypervisor(folders, "/lab", "mock", HypervisorDef(connector_type="mock"))
        folders.save(Folder(path="/lab/sub", imports=["*"]))
        folders.save(Folder(path="/lab/sub/inner", imports=["mock"]))
        result = _find_hypervisor("mock", "/lab/sub/inner", folders)
        assert result is not None
        _, path = result
        assert path == "/lab"

    def test_hypervisor_not_found_returns_none(self, folders: FolderRepository) -> None:
        folders.save(Folder(path="/lab"))
        assert _find_hypervisor("missing", "/lab", folders) is None

    def test_unknown_parent_folder_returns_none(
        self, folders: FolderRepository
    ) -> None:
        assert _find_hypervisor("anything", "/orphan/path", folders) is None

    def test_reaches_root_without_finding(self, folders: FolderRepository) -> None:
        folders.save(Folder(path="/lab", imports=["*"]))
        folders.save(Folder(path="/lab/inner", imports=["*"]))
        assert _find_hypervisor("missing", "/lab/inner", folders) is None

    def test_same_name_in_different_branches_are_distinct(
        self, folders: FolderRepository
    ) -> None:
        # Two hypervisors named 'aulario' in unrelated branches: each find
        # returns its own folder's path, so the pool keys are distinct and
        # the live sessions won't collide.
        _put_hypervisor(
            folders, "/lab", "aulario", HypervisorDef(connector_type="mock")
        )
        _put_hypervisor(
            folders, "/research", "aulario", HypervisorDef(connector_type="mock")
        )
        left = _find_hypervisor("aulario", "/lab", folders)
        right = _find_hypervisor("aulario", "/research", folders)
        assert left is not None and right is not None
        assert left[1] == "/lab"
        assert right[1] == "/research"


class TestResolveDescriptor:
    def test_descriptor_without_template_passes_through(
        self, folders: FolderRepository
    ) -> None:
        descriptor = Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
        assert resolve_descriptor(descriptor, folders) == descriptor

    def test_descriptor_with_template_resolves(self, folders: FolderRepository) -> None:
        _put_template(
            folders,
            "/lab",
            "linux-vm",
            VMTemplateDef(hypervisor="mock", base_vm="linux-base", cpu=2),
        )
        folders.save(Folder(path="/lab/networks", imports=["linux-vm"]))
        descriptor = Descriptor(path="/lab/networks/vm", template="linux-vm")
        result = resolve_descriptor(descriptor, folders)
        assert result.hypervisor == "mock"
        assert result.base_vm == "linux-base"
        assert result.cpu == 2

    def test_descriptor_local_field_wins_after_resolve(
        self, folders: FolderRepository
    ) -> None:
        _put_template(
            folders, "/lab", "linux-vm", VMTemplateDef(hypervisor="mock", cpu=2)
        )
        descriptor = Descriptor(path="/lab/vm", template="linux-vm", cpu=4)
        result = resolve_descriptor(descriptor, folders)
        assert result.hypervisor == "mock"  # from template
        assert result.cpu == 4  # local wins

    def test_unknown_template_raises(self, folders: FolderRepository) -> None:
        folders.save(Folder(path="/lab"))
        descriptor = Descriptor(path="/lab/vm", template="missing")
        with pytest.raises(ValueError, match="not accessible"):
            resolve_descriptor(descriptor, folders)

    def test_resolve_is_idempotent(self, folders: FolderRepository) -> None:
        _put_template(
            folders, "/lab", "linux-vm", VMTemplateDef(hypervisor="mock", cpu=2)
        )
        descriptor = Descriptor(path="/lab/vm", template="linux-vm")
        once = resolve_descriptor(descriptor, folders)
        twice = resolve_descriptor(once, folders)
        assert once == twice


# --- Hypothesis property tests for _merge_template -------------------------

# Only fields the resolver merges; description, hypervisor, base_vm are strings,
# cpu/memory_mb/disk_gb are positive ints. Using simple types to keep strategies
# fast and the failure messages readable.
_STRING_OR_NONE = st.one_of(st.none(), st.text(min_size=1, max_size=10))
_INT_OR_NONE = st.one_of(st.none(), st.integers(min_value=1, max_value=64))


@st.composite
def _descriptor_and_template(draw: st.DrawFn) -> tuple[Descriptor, VMTemplateDef]:
    desc_fields: dict[str, Any] = {
        "description": draw(_STRING_OR_NONE),
        "hypervisor": draw(_STRING_OR_NONE),
        "base_vm": draw(_STRING_OR_NONE),
        "cpu": draw(_INT_OR_NONE),
        "memory_mb": draw(_INT_OR_NONE),
        "disk_gb": draw(_INT_OR_NONE),
    }
    tpl_fields: dict[str, Any] = {
        "description": draw(_STRING_OR_NONE),
        "hypervisor": draw(_STRING_OR_NONE),
        "base_vm": draw(_STRING_OR_NONE),
        "cpu": draw(_INT_OR_NONE),
        "memory_mb": draw(_INT_OR_NONE),
        "disk_gb": draw(_INT_OR_NONE),
    }
    descriptor = Descriptor(path="/lab/vm", template="t", **desc_fields)
    template = VMTemplateDef(**tpl_fields)
    return descriptor, template


_FIELDS = ("description", "hypervisor", "base_vm", "cpu", "memory_mb", "disk_gb")


@given(_descriptor_and_template())
def test_local_value_always_wins_when_set(
    pair: tuple[Descriptor, VMTemplateDef],
) -> None:
    descriptor, template = pair
    merged = _merge_template(descriptor, template)
    for name in _FIELDS:
        if getattr(descriptor, name) is not None:
            assert getattr(merged, name) == getattr(descriptor, name)


@given(_descriptor_and_template())
def test_template_fills_when_local_is_none(
    pair: tuple[Descriptor, VMTemplateDef],
) -> None:
    descriptor, template = pair
    merged = _merge_template(descriptor, template)
    for name in _FIELDS:
        if getattr(descriptor, name) is None:
            assert getattr(merged, name) == getattr(template, name)


@given(_descriptor_and_template())
def test_merge_is_idempotent(
    pair: tuple[Descriptor, VMTemplateDef],
) -> None:
    descriptor, template = pair
    once = _merge_template(descriptor, template)
    twice = _merge_template(once, template)
    assert once == twice
