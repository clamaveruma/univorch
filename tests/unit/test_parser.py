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
    use hypervisor: mock
    base_vm: linux-base
shared_vm:
  use hypervisor: mock
  base_vm: linux-base
"""


def test_parses_a_valid_document() -> None:
    doc = parse_definition(VALID)
    assert doc.kind == "definition"
    assert list(doc.folders) == ["lab"]  # trailing / stripped from the key
    assert doc.folders["lab"].description == "Lab"
    assert "vm" in doc.folders["lab"].descriptors  # nested under the folder
    # 'use hypervisor:' (YAML alias) → 'hypervisor' (Python field) via Pydantic
    assert doc.descriptors["shared_vm"].hypervisor == "mock"


def test_parses_define_hypervisors() -> None:
    yaml = (
        "kind: definition\n"
        "lab/:\n"
        "  define hypervisors:\n"
        "    mock:\n"
        "      type: mock\n"
        "      description: in-memory mock\n"
    )
    doc = parse_definition(yaml)
    assert "mock" in doc.folders["lab"].hypervisors
    h = doc.folders["lab"].hypervisors["mock"]
    assert h.connector_type == "mock"  # YAML 'type:' → Python 'connector_type'
    assert h.description == "in-memory mock"


def test_parses_define_machine_templates() -> None:
    yaml = (
        "kind: definition\n"
        "lab/:\n"
        "  define templates:\n"
        "    linux-vm:\n"
        "      use hypervisor: mock\n"
        "      base_vm: linux-base\n"
        "      cpu: 2\n"
    )
    doc = parse_definition(yaml)
    t = doc.folders["lab"].vm_templates["linux-vm"]
    assert t.hypervisor == "mock"
    assert t.base_vm == "linux-base"
    assert t.cpu == 2


def test_import_ALL_normalizes_to_wildcard() -> None:
    yaml = "kind: definition\nlab/:\n  import: ALL\n"
    doc = parse_definition(yaml)
    assert doc.folders["lab"].imports == ["*"]


def test_import_star_normalizes_to_wildcard() -> None:
    # '*' is the readable form of the wildcard; ALL and * are equivalent
    yaml = "kind: definition\nlab/:\n  import: '*'\n"
    doc = parse_definition(yaml)
    assert doc.folders["lab"].imports == ["*"]


def test_import_list_kept_as_is() -> None:
    yaml = "kind: definition\nlab/:\n  import: [a, b, hyperv-*]\n"
    doc = parse_definition(yaml)
    assert doc.folders["lab"].imports == ["a", "b", "hyperv-*"]


def test_descriptor_with_only_template_is_valid() -> None:
    yaml = "kind: definition\nvm:\n  use template: linux-vm\n"
    doc = parse_definition(yaml)
    d = doc.descriptors["vm"]
    assert d.template == "linux-vm"
    assert d.hypervisor is None
    assert d.base_vm is None


def test_rejects_top_level_resources() -> None:
    # Resources and 'import' cannot live at the document root — they belong
    # inside a folder.
    yaml = "kind: definition\ndefine hypervisors:\n  mock: { type: mock }\n"
    with pytest.raises(ValidationError):
        parse_definition(yaml)


def test_rejects_top_level_import() -> None:
    yaml = "kind: definition\nimport: ALL\n"
    with pytest.raises(ValidationError):
        parse_definition(yaml)


def test_rejects_wrong_kind() -> None:
    with pytest.raises(ValidationError):
        parse_definition("kind: load\n")


def test_rejects_hypervisor_definition_missing_type() -> None:
    # Pieza 1.A: descriptor's hypervisor/base_vm are optional (may be inherited
    # from a template). What's still required: a *defined* hypervisor needs a
    # 'type' (the connector type).
    yaml = (
        "kind: definition\n"
        "lab/:\n"
        "  define hypervisors:\n"
        "    mock:\n"
        "      description: 'no type'\n"
    )
    with pytest.raises(ValidationError):
        parse_definition(yaml)


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
