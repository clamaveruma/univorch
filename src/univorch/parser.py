"""Parse a definition document from YAML.

ruamel.yaml does the YAML parsing; Pydantic (``DefinitionDocument``) validates
the schema — kind, names, required fields, unknown fields — and raises
``ValidationError`` on a malformed document.

v1 uses a plain (``safe``) load: comments are dropped at read time (Modelo A —
the DB is the operational truth; ``description`` is the place for documentation
that should persist).
"""

from pathlib import Path

from ruamel.yaml import YAML

from univorch.models import DefinitionDocument

_yaml = YAML(typ="safe")  # safe load → plain dicts/lists (no round-trip)


def parse_definition(text: str) -> DefinitionDocument:
    """Parse YAML ``text`` into a validated DefinitionDocument."""
    data = _yaml.load(text)
    return DefinitionDocument.model_validate(data)


def parse_definition_file(path: str | Path) -> DefinitionDocument:
    """Read ``path`` and parse it as a definition document."""
    return parse_definition(Path(path).read_text())
