"""Anti-drift check: the hand-written JSON Schema must agree with Pydantic.

The schema in ``docs/schema/definition.schema.json`` is the contract editors
see (VSCode autocompletion via the YAML language server). Pydantic is the
runtime validator. This test corners both with the same documents: a valid
one must pass both; an invalid one must fail both. If they diverge, the test
goes red — that's the signal to update one of them.
"""

import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError
from ruamel.yaml import YAML

from univorch.models import DefinitionDocument

_REPO = Path(__file__).resolve().parents[2]
_SCHEMA_FILE = _REPO / "docs" / "schema" / "definition.schema.json"
_DEMO_FILE = _REPO / "demo" / "setup.yml"

_yaml = YAML(typ="safe")


@pytest.fixture(scope="module")
def schema() -> dict[str, object]:
    return json.loads(_SCHEMA_FILE.read_text())


def _load_yaml_text(text: str) -> object:
    return _yaml.load(text)


def _load_yaml_file(path: Path) -> object:
    return _yaml.load(path.read_text())


def test_demo_setup_passes_both(schema: dict[str, object]) -> None:
    """The reference demo YAML validates against schema AND Pydantic."""
    data = _load_yaml_file(_DEMO_FILE)
    jsonschema.validate(data, schema)  # raises if invalid
    DefinitionDocument.model_validate(data)


def test_minimal_document_passes_both(schema: dict[str, object]) -> None:
    """An almost-empty document (just kind) is valid in both."""
    data = _load_yaml_text("kind: definition\n")
    jsonschema.validate(data, schema)
    DefinitionDocument.model_validate(data)


def test_missing_required_field_fails_both(schema: dict[str, object]) -> None:
    """A VM without ``hypervisor`` is rejected by both validators."""
    bad = _load_yaml_text("kind: definition\nvm:\n  base_vm: linux-base\n")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
    with pytest.raises(ValidationError):
        DefinitionDocument.model_validate(bad)


def test_unknown_field_fails_both(schema: dict[str, object]) -> None:
    """An unknown field on a VM is rejected by both validators."""
    bad = _load_yaml_text(
        "kind: definition\nvm:\n  hypervisor: mock\n  base_vm: linux-base\n  cpuu: 2\n"
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
    with pytest.raises(ValidationError):
        DefinitionDocument.model_validate(bad)


def test_wrong_kind_fails_both(schema: dict[str, object]) -> None:
    """A wrong ``kind`` is rejected by both validators."""
    bad = _load_yaml_text("kind: load\n")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
    with pytest.raises(ValidationError):
        DefinitionDocument.model_validate(bad)
