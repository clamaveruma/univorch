"""Teaching operations, decoupled from the CLI for testability.

Each function takes an ``OrchestratorAPI`` (the in-process service or the
HTTP client) plus arguments, performs the teaching workflow against the
core, and returns lines to print. Validation failures raise
``TeachingError`` with the list of reasons; the CLI renders them.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from univorch.models import Folder
from univorch.parser import parse_definition_file
from univorch.teaching.models import SUBJECT_KIND, StudentList
from univorch.teaching.students import build_student_document
from univorch.teaching.subject import validate_subject

if TYPE_CHECKING:
    from univorch.service import OrchestratorAPI

_yaml = YAML(typ="safe")


class TeachingError(Exception):
    """A teaching-level validation failure. Carries the list of reasons."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def load_subject(api: OrchestratorAPI, file: str, destination: str) -> list[str]:
    """Validate a subject document and load it at ``destination``."""
    document = parse_definition_file(file)
    errors = validate_subject(document)
    if errors:
        raise TeachingError(errors)
    results = api.load(document, destination)
    return [f"{r.path}  {r.message}" for r in results]


def load_students(api: OrchestratorAPI, subject_path: str, file: str) -> list[str]:
    """Create one folder + desktop descriptors per student under a subject."""
    entity = api.inspect(subject_path, resolved=False)
    if not isinstance(entity, Folder):
        raise TeachingError([f"{subject_path} is not a folder"])
    if entity.metadata.get("kind") != SUBJECT_KIND:
        raise TeachingError([f"{subject_path} is not a subject (no 'kind: subject')"])
    desktop = subject_desktop_from_folder(entity)
    if not desktop:
        raise TeachingError([f"subject {subject_path} has no desktop defined"])

    data = _yaml.load(Path(file).read_text())
    student_list = StudentList.model_validate(data)

    document = build_student_document(student_list.students, desktop)
    results = api.load(document, subject_path)
    return [f"{r.path}  {r.message}" for r in results]


def save_students(api: OrchestratorAPI, subject_path: str) -> str:
    """Return a student-list YAML for the students currently under a subject."""
    children = api.list_tree(subject_path, recursive=False)
    names = sorted(e.path.rsplit("/", 1)[-1] for e in children if e.kind == "folder")
    lines = ["kind: student-list", 'version: "1"', "students:"]
    lines += [f"  - {name}" for name in names]
    return "\n".join(lines) + "\n"


def subject_desktop_from_folder(folder: Folder) -> list[str]:
    """Read the desktop list from a persisted subject folder's metadata."""
    desktop = folder.metadata.get("desktop", [])
    return list(desktop) if isinstance(desktop, list) else []
