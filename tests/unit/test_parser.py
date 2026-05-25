"""Tests for the YAML apply-document parser."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from univorch.parser import load_apply_document, load_apply_file

_DEMO_FILE = Path(__file__).resolve().parents[2] / "demo" / "setup.yml"

VALID = """
kind: apply
version: "1"
folders:
  - path: /lab
descriptors:
  - path: /lab/vm
    hypervisor: mock
    base_vm: linux-base
"""


def test_parses_a_valid_document() -> None:
    doc = load_apply_document(VALID)
    assert doc.kind == "apply"
    assert [f.path for f in doc.folders] == ["/lab"]
    assert doc.descriptors[0].hypervisor == "mock"


def test_rejects_wrong_kind() -> None:
    with pytest.raises(ValidationError):
        load_apply_document("kind: delete\nfolders: []\n")


def test_rejects_descriptor_missing_hypervisor() -> None:
    with pytest.raises(ValidationError):
        load_apply_document(
            "descriptors:\n  - path: /lab/vm\n    base_vm: linux-base\n"
        )


def test_rejects_invalid_path() -> None:
    with pytest.raises(ValidationError):
        load_apply_document("folders:\n  - path: lab\n")  # no leading slash


def test_rejects_unknown_field() -> None:
    # extra="forbid": a misspelled field is caught instead of silently dropped
    with pytest.raises(ValidationError):
        load_apply_document("folders:\n  - path: /lab\n    descripton: typo\n")


def test_loads_the_demo_file() -> None:
    doc = load_apply_file(_DEMO_FILE)
    assert doc.kind == "apply"
    assert len(doc.descriptors) == 3
