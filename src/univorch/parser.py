"""Parse an apply document from YAML.

ruamel.yaml does the YAML parsing; Pydantic (``ApplyDocument``) validates the
schema — kind, paths, required fields, unknown fields — and raises
``ValidationError`` on a malformed document.

v1 uses a plain (``safe``) load: we only read here. Round-trip loading that
preserves comments is a Sprint 2 concern (editing/exporting YAML, DEC-027).
"""

from pathlib import Path

from ruamel.yaml import YAML

from univorch.models import ApplyDocument

_yaml = YAML(typ="safe")  # safe load → plain dicts/lists (no round-trip)


def load_apply_document(text: str) -> ApplyDocument:
    """Parse YAML ``text`` into a validated ApplyDocument."""
    data = _yaml.load(text)
    return ApplyDocument.model_validate(data)


def load_apply_file(path: str | Path) -> ApplyDocument:
    """Read ``path`` and parse it as an apply document."""
    return load_apply_document(Path(path).read_text())
