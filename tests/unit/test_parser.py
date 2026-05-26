"""Tests for the YAML definition parser (new envelope + trailing-/ format)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from univorch.parser import parse_definition, parse_definition_file

_DEMO_FILE = Path(__file__).resolve().parents[2] / "demo" / "setup.yml"

VALID = """
kind: definition
version: "1"
lab/:
  description: "Lab"
  vm:
    hypervisor: mock
    base_vm: linux-base
shared_vm:
  hypervisor: mock
  base_vm: linux-base
"""


def test_parses_a_valid_document() -> None:
    doc = parse_definition(VALID)
    assert doc.kind == "definition"
    assert list(doc.folders) == ["lab"]  # trailing / stripped from the key
    assert doc.folders["lab"].description == "Lab"
    assert "vm" in doc.folders["lab"].descriptors  # nested under the folder
    assert doc.descriptors["shared_vm"].hypervisor == "mock"  # top-level VM


def test_rejects_wrong_kind() -> None:
    with pytest.raises(ValidationError):
        parse_definition("kind: load\n")


def test_rejects_descriptor_missing_hypervisor() -> None:
    with pytest.raises(ValidationError):
        parse_definition("vm:\n  base_vm: linux-base\n")  # no hypervisor


def test_rejects_invalid_name() -> None:
    # names must match the segment pattern (alphanumerics + _ - )
    with pytest.raises(ValidationError):
        parse_definition("bad name/:\n")  # space in the folder name


def test_rejects_unknown_field_on_descriptor() -> None:
    # extra="forbid": a misspelled field on a VM is caught
    with pytest.raises(ValidationError):
        parse_definition(
            "vm:\n  hypervisor: mock\n  base_vm: linux-base\n  descripton: typo\n"
        )


def test_loads_the_demo_file() -> None:
    doc = parse_definition_file(_DEMO_FILE)
    assert doc.kind == "definition"
    # demo has /lab/networks/student01..03 — three VMs under nested folders
    assert "lab" in doc.folders
    assert "networks" in doc.folders["lab"].folders
    assert len(doc.folders["lab"].folders["networks"].descriptors) == 3
