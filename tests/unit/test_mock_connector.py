"""Tests for the MockConnector: state, constructors, clone and get_status (M1)."""

import pytest

from univorch.connectors.mock import MockConnector
from univorch.connectors.types import CloneMode, RuntimeState


class TestConstructors:
    def test_empty_has_no_templates(self) -> None:
        mock = MockConnector.empty()
        with pytest.raises(ValueError):
            mock.clone("linux-base", "vm")

    def test_with_demo_templates_can_clone_linux_base(self) -> None:
        mock = MockConnector.with_demo_templates()
        vm_id = mock.clone("linux-base", "student01")
        assert mock.get_status(vm_id) == RuntimeState.STOPPED

    def test_with_templates_uses_given_templates(self) -> None:
        mock = MockConnector.with_templates(["custom-base"])
        vm_id = mock.clone("custom-base", "vm")
        assert mock.get_status(vm_id) == RuntimeState.STOPPED


class TestClone:
    def test_returns_deterministic_ids(self) -> None:
        mock = MockConnector.with_demo_templates()
        assert mock.clone("linux-base", "a") == "mock-vm-1"
        assert mock.clone("linux-base", "b") == "mock-vm-2"

    def test_unknown_template_raises(self) -> None:
        mock = MockConnector.with_demo_templates()
        with pytest.raises(ValueError):
            mock.clone("does-not-exist", "vm")

    def test_full_clone_not_supported(self) -> None:
        mock = MockConnector.with_demo_templates()
        with pytest.raises(NotImplementedError):
            mock.clone("linux-base", "vm", mode=CloneMode.FULL)

    def test_cloned_vm_starts_stopped(self) -> None:
        mock = MockConnector.with_demo_templates()
        vm_id = mock.clone("linux-base", "vm")
        assert mock.get_status(vm_id) == RuntimeState.STOPPED


class TestGetStatus:
    def test_unknown_vm_raises(self) -> None:
        mock = MockConnector.with_demo_templates()
        with pytest.raises(ValueError):
            mock.get_status("nope")
