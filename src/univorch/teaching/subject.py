"""Subject validation for the teaching layer (DEC-038).

A subject is a core ``DefinitionDocument`` with exactly one top-level
folder marked, in its opaque ``metadata``, with ``kind: subject`` and a
non-empty ``desktop`` list. These functions validate that shape before
the document is handed to the core ``load``.
"""

from __future__ import annotations

from univorch.models import DefinitionDocument, FolderDef
from univorch.teaching.models import SUBJECT_KIND


def find_subject(document: DefinitionDocument) -> tuple[str, FolderDef] | None:
    """Return the single (name, folder) that is a subject, or None.

    A valid subject document has exactly one top-level folder; this returns
    it regardless of whether it is well-formed (validation reports why).
    """
    folders = list(document.folders.items())
    if len(folders) != 1:
        return None
    return folders[0]


def validate_subject(document: DefinitionDocument) -> list[str]:
    """Return the list of reasons the document is not a valid subject.

    Empty list means valid. Checks (requirements 4.1):
      1. exactly one top-level folder;
      2. metadata.kind == 'subject';
      3. metadata.desktop is a non-empty list;
      4. every desktop name is a template defined locally or imported;
      5. the subject folder has no child folders.
    Duplicate-list checks are handled by Pydantic at parse time.
    """
    errors: list[str] = []

    folders = list(document.folders.items())
    if len(folders) != 1:
        errors.append(
            f"a subject document must have exactly one top-level folder, "
            f"found {len(folders)}"
        )
        return errors

    name, folder = folders[0]
    meta = folder.metadata

    if meta.get("kind") != SUBJECT_KIND:
        errors.append(f"folder '{name}' is not marked 'kind: subject' in its metadata")

    desktop = meta.get("desktop")
    if not isinstance(desktop, list) or not desktop:
        errors.append(f"subject '{name}' must declare a non-empty 'desktop' list")
        desktop = []

    if folder.folders:
        errors.append(
            f"subject '{name}' must not contain child folders "
            f"(found: {sorted(folder.folders)})"
        )

    # every desktop entry must be resolvable: defined locally or imported
    available = set(folder.vm_templates) | set(folder.imports)
    wildcard = "*" in folder.imports
    for tmpl in desktop:
        if not wildcard and tmpl not in available:
            errors.append(
                f"desktop template '{tmpl}' is neither defined "
                f"('define templates:') nor imported in subject '{name}'"
            )

    return errors


def subject_desktop(folder: FolderDef) -> list[str]:
    """Return the desktop list from a subject folder's metadata."""
    desktop = folder.metadata.get("desktop", [])
    return list(desktop) if isinstance(desktop, list) else []
