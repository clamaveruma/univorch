"""Cascade-inheritance Resolver (Sprint 2 Pieza 1.B; DEC-026, DEC-012).

Pure function that, given a stored descriptor and the folder repository, returns
the same descriptor with its referenced template's fields merged in. The
Resolver never writes to the database: the stored descriptor keeps its local
definition exactly as the user wrote it, and what the rest of the orchestrator
sees when it acts on a VM is the resolved version this module returns.

What's in scope of Pieza 1.B:
- A descriptor with ``template: X`` looks for ``X`` walking up from its own
  folder, honouring each ancestor's ``import:`` filter. The first ancestor
  that defines ``X`` (in its ``vm_templates``) provides the template.
- Once found, the template's fields are merged into the descriptor's: a field
  set locally (non-None) on the descriptor wins; an unset field is filled
  from the template (scalar-replace rule, DEC-026).

What's NOT yet in scope (later pieces):
- Templates that derive from other templates (``based on:``) — Pieza 4.
- Validation that a descriptor's hypervisor name (locally set or carried
  from the template) actually points at a hypervisor declared somewhere
  accessible — the service still relies on its connector registry.
- The annotated mode ("from which folder did each field come?") — future
  ``inspect`` work.
"""

from __future__ import annotations

import fnmatch
import posixpath
from collections.abc import Iterable

from univorch.models import Descriptor, VMTemplateDef
from univorch.persistence.tinydb.repositories import FolderRepository

# Fields shared between Descriptor and VMTemplateDef; only these participate in
# the merge. path/template/state/vm_id stay as they are on the descriptor.
_TEMPLATE_FIELDS: tuple[str, ...] = (
    "description",
    "hypervisor",
    "base_vm",
    "cpu",
    "memory_mb",
    "disk_gb",
)


def resolve_descriptor(
    descriptor: Descriptor, folders_repo: FolderRepository
) -> Descriptor:
    """Return ``descriptor`` with its template (if any) merged in.

    Raises:
        ValueError: if the descriptor references a template that is not
            accessible from its folder (the name is not defined locally and
            no ancestor's ``import:`` filter lets it pass).
    """
    if descriptor.template is None:
        return descriptor  # nothing to resolve; pass through
    folder_path = posixpath.dirname(descriptor.path) or "/"
    template = _find_template(descriptor.template, folder_path, folders_repo)
    if template is None:
        raise ValueError(
            f"template not accessible from {descriptor.path}: {descriptor.template!r}"
        )
    return _merge_template(descriptor, template)


def _merge_template(descriptor: Descriptor, template: VMTemplateDef) -> Descriptor:
    """Local fields win; missing ones are filled from ``template``.

    Returns a new Descriptor; the input is left unchanged (pure function).
    """
    updates: dict[str, object | None] = {}
    for field in _TEMPLATE_FIELDS:
        if getattr(descriptor, field) is None:
            updates[field] = getattr(template, field)
    return descriptor.model_copy(update=updates)


def _find_template(
    name: str, start: str, folders_repo: FolderRepository
) -> VMTemplateDef | None:
    """Walk ancestors from ``start`` looking for the template ``name``.

    Each level is checked in this order:
      1. The folder defines ``name`` locally → return that template.
      2. Otherwise, the folder's ``import:`` filter allows ``name`` to pass
         from the parent → climb to the parent and repeat.
      3. Otherwise the import chain breaks at this level → not found.
    Returns ``None`` on a broken chain or when the walk reaches the (resource-
    less) root without finding the name.
    """
    current = start
    while current != "/":
        folder = folders_repo.get(current)
        if folder is None:
            return None  # broken tree: parent should have been created at load
        if name in folder.vm_templates:
            return folder.vm_templates[name]
        if not _import_allows(folder.imports, name):
            return None  # this level does not import the name; chain stops
        current = posixpath.dirname(current) or "/"
    return None  # reached root; root has no Folder record and no resources


def _import_allows(imports: Iterable[str], name: str) -> bool:
    """True if ``name`` passes the import filter of a folder.

    Accepts shell-style wildcards (``*``, ``?``, ``[...]``) via ``fnmatch``;
    ``*`` alone matches everything (the normalised form of ``import: ALL``).
    An empty list matches nothing.
    """
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in imports)
