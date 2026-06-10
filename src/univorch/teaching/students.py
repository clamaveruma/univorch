"""Student-folder generation for the teaching layer (DEC-039).

Turns a student list plus a subject's desktop into a core
``DefinitionDocument`` of one folder per student, each containing one
descriptor per desktop template (``use template: <name>``). The document
is then loaded by the core at the subject's path. Add-only: existing
students are no-ops; none are removed.
"""

from __future__ import annotations

from typing import Any

from univorch.models import DefinitionDocument


def build_student_document(
    students: list[str], desktop: list[str]
) -> DefinitionDocument:
    """Build the core document that creates the per-student structure.

    For each student a folder (key ending in ``/``) holding one descriptor
    per desktop template, each carrying ``use template: <name>``. The
    returned document is loaded with destination = the subject's path.
    """
    items: dict[str, Any] = {}
    for student in students:
        # import: * so the student's descriptors resolve the subject's
        # templates by cascade (a student folder imports everything the
        # subject offers — the design's "cada carpeta de alumno hace import *").
        student_folder: dict[str, Any] = {"import": "*"}
        for template in desktop:
            student_folder[template] = {"use template": template}
        items[f"{student}/"] = student_folder
    return DefinitionDocument.model_validate(items)


def student_names_from_document(document: DefinitionDocument) -> list[str]:
    """Return the student folder names of a generated document (for save)."""
    return sorted(document.folders)
