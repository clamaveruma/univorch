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


class TestLifecycle:
    def _deployed(self) -> tuple[MockConnector, str]:
        mock = MockConnector.with_demo_templates()
        return mock, mock.clone("linux-base", "vm")

    def test_start_powers_on(self) -> None:
        mock, vm = self._deployed()
        mock.start(vm)
        assert mock.get_status(vm) == RuntimeState.RUNNING

    def test_start_is_harmless_when_already_running(self) -> None:
        mock, vm = self._deployed()
        mock.start(vm)
        mock.start(vm)
        assert mock.get_status(vm) == RuntimeState.RUNNING

    def test_start_resumes_a_paused_vm(self) -> None:
        mock, vm = self._deployed()
        mock.start(vm)
        mock.pause(vm)
        mock.start(vm)
        assert mock.get_status(vm) == RuntimeState.RUNNING

    def test_stop_powers_off(self) -> None:
        mock, vm = self._deployed()
        mock.start(vm)
        mock.stop(vm)
        assert mock.get_status(vm) == RuntimeState.STOPPED

    def test_stop_is_harmless_when_already_stopped(self) -> None:
        mock, vm = self._deployed()
        mock.stop(vm)
        assert mock.get_status(vm) == RuntimeState.STOPPED

    def test_force_stop_powers_off(self) -> None:
        mock, vm = self._deployed()
        mock.start(vm)
        mock.force_stop(vm)
        assert mock.get_status(vm) == RuntimeState.STOPPED

    def test_pause_suspends_a_running_vm(self) -> None:
        mock, vm = self._deployed()
        mock.start(vm)
        mock.pause(vm)
        assert mock.get_status(vm) == RuntimeState.PAUSED

    def test_pause_a_stopped_vm_raises(self) -> None:
        mock, vm = self._deployed()
        with pytest.raises(ValueError):
            mock.pause(vm)

    def test_resume_returns_a_paused_vm_to_running(self) -> None:
        mock, vm = self._deployed()
        mock.start(vm)
        mock.pause(vm)
        mock.resume(vm)
        assert mock.get_status(vm) == RuntimeState.RUNNING

    def test_resume_a_stopped_vm_raises(self) -> None:
        mock, vm = self._deployed()
        with pytest.raises(ValueError):
            mock.resume(vm)

    def test_lifecycle_on_unknown_vm_raises(self) -> None:
        mock = MockConnector.with_demo_templates()
        with pytest.raises(ValueError):
            mock.start("nope")


class TestDelete:
    def test_removes_the_vm(self) -> None:
        mock = MockConnector.with_demo_templates()
        vm = mock.clone("linux-base", "vm")
        mock.delete(vm)
        with pytest.raises(ValueError):
            mock.get_status(vm)

    def test_unknown_raises(self) -> None:
        mock = MockConnector.with_demo_templates()
        with pytest.raises(ValueError):
            mock.delete("nope")

    def test_is_not_idempotent(self) -> None:
        mock = MockConnector.with_demo_templates()
        vm = mock.clone("linux-base", "vm")
        mock.delete(vm)
        with pytest.raises(ValueError):
            mock.delete(vm)


class TestGetInfo:
    def test_returns_vm_fields(self) -> None:
        mock = MockConnector.with_demo_templates()
        vm = mock.clone("linux-base", "student01")
        info = mock.get_info(vm)
        assert info.id == vm
        assert info.name == "student01"
        assert info.runtime_state == RuntimeState.STOPPED
        assert info.cpu is None

    def test_unknown_raises(self) -> None:
        mock = MockConnector.with_demo_templates()
        with pytest.raises(ValueError):
            mock.get_info("nope")


class TestDeployedVms:
    def test_empty_initially(self) -> None:
        mock = MockConnector.with_demo_templates()
        assert mock.deployed_vms() == []

    def test_reflects_clone_and_delete(self) -> None:
        mock = MockConnector.with_demo_templates()
        vm = mock.clone("linux-base", "vm")
        assert [info.id for info in mock.deployed_vms()] == [vm]
        mock.delete(vm)
        assert mock.deployed_vms() == []
