"""Tests for the pure-function helpers of the web GUI.

NiceGUI pages themselves (``index``, ``descriptor_detail``) are exercised
by smoke tests that hit the running daemon; here we cover the data-shape
helpers in isolation because they are plain functions with no NiceGUI
dependency in their bodies.
"""

from univorch.interfaces.web.app import _build_tree_nodes, _descriptor_counts
from univorch.models import DescriptorState
from univorch.service import TreeEntry


def _folder(path: str) -> TreeEntry:
    return TreeEntry(path=path, kind="folder", state=None)


def _descriptor(path: str, state: DescriptorState) -> TreeEntry:
    return TreeEntry(path=path, kind="descriptor", state=state)


class TestBuildTreeNodes:
    def test_empty_input_yields_empty_list(self) -> None:
        assert _build_tree_nodes([]) == []

    def test_two_top_level_folders_become_two_roots(self) -> None:
        roots = _build_tree_nodes([_folder("/lab"), _folder("/research")])
        ids = sorted(node["id"] for node in roots)
        assert ids == ["/lab", "/research"]
        assert all(node["children"] == [] for node in roots)

    def test_label_is_the_basename(self) -> None:
        roots = _build_tree_nodes([_folder("/lab/networks")])
        assert roots[0]["label"] == "networks"

    def test_descriptor_under_folder_becomes_child(self) -> None:
        roots = _build_tree_nodes(
            [
                _folder("/lab"),
                _descriptor("/lab/vm1", DescriptorState.PROVISIONED),
            ]
        )
        assert len(roots) == 1
        assert roots[0]["id"] == "/lab"
        assert len(roots[0]["children"]) == 1
        assert roots[0]["children"][0]["id"] == "/lab/vm1"
        assert roots[0]["children"][0]["state"] == DescriptorState.PROVISIONED

    def test_deep_nesting_three_levels(self) -> None:
        roots = _build_tree_nodes(
            [
                _folder("/lab"),
                _folder("/lab/networks"),
                _descriptor("/lab/networks/s01", DescriptorState.DEPLOYED),
            ]
        )
        assert len(roots) == 1
        lab = roots[0]
        assert lab["id"] == "/lab"
        assert len(lab["children"]) == 1
        networks = lab["children"][0]
        assert networks["id"] == "/lab/networks"
        assert len(networks["children"]) == 1
        assert networks["children"][0]["id"] == "/lab/networks/s01"

    def test_descriptor_without_parent_in_input_becomes_root(self) -> None:
        # If list_tree is called with recursive=True on a subtree, ancestors
        # may be missing from the result; the function must not crash.
        roots = _build_tree_nodes(
            [_descriptor("/lab/orphan", DescriptorState.PROVISIONED)]
        )
        assert len(roots) == 1
        assert roots[0]["id"] == "/lab/orphan"


class TestDescriptorCounts:
    def test_empty_input(self) -> None:
        c = _descriptor_counts([])
        assert c["total"] == 0
        assert all(c[state.value] == 0 for state in DescriptorState)

    def test_folders_are_not_counted(self) -> None:
        c = _descriptor_counts([_folder("/lab"), _folder("/research")])
        assert c["total"] == 0

    def test_mixed_states(self) -> None:
        entries = [
            _folder("/lab"),
            _descriptor("/lab/a", DescriptorState.PROVISIONED),
            _descriptor("/lab/b", DescriptorState.DEPLOYED),
            _descriptor("/lab/c", DescriptorState.DEPLOYED),
            _descriptor("/lab/d", DescriptorState.BROKEN),
            _descriptor("/lab/e", DescriptorState.UNREACHABLE),
        ]
        c = _descriptor_counts(entries)
        assert c["total"] == 5
        assert c["provisioned"] == 1
        assert c["deployed"] == 2
        assert c["broken"] == 1
        assert c["unreachable"] == 1
