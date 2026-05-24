"""Domain entities: folders and descriptors.

Pydantic models, so they serialise to and from TinyDB with ``model_dump()`` /
``model_validate()`` (DEC-034). The tree uses a materialized path: each entity's
full path is its key.

Only *syntactic* path validation lives here. Contextual checks (parent exists,
create vs update, references) and RBAC belong to the apply/service layer
(DEC-027, DEC-031), which can see the whole tree.
"""

import re
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel

_SEGMENT = re.compile(r"[A-Za-z0-9_-]+")  # provisional pattern, to be refined later


def _validate_path(path: str) -> str:
    """Check that ``path`` is a well-formed absolute tree path.

    Raises:
        ValueError: If it is not absolute, has an empty segment (``//`` or a
            trailing slash), or a segment with disallowed characters.
    """
    if not path.startswith("/"):
        raise ValueError(f"path must start with '/': {path!r}")
    if path == "/":
        return path
    for segment in path[1:].split("/"):
        if not _SEGMENT.fullmatch(segment):
            raise ValueError(f"invalid path segment {segment!r} in {path!r}")
    return path


TreePath = Annotated[str, AfterValidator(_validate_path)]


class DescriptorState(StrEnum):
    """Orchestrator-side state of a descriptor (DEC-022/032)."""

    PROVISIONED = "provisioned"
    DEPLOYED = "deployed"
    BROKEN = "broken"
    UNREACHABLE = "unreachable"


class Folder(BaseModel):
    """A node in the descriptor tree, addressed by its materialized path."""

    path: TreePath
    description: str | None = None


class Descriptor(BaseModel):
    """A VM definition in the tree (analogous to a file descriptor in an OS).

    Sprint 1 carries the configuration inline (``hypervisor``, ``base_vm``,
    specs); Sprint 2 moves it to an inherited ``definition`` (DEC-026/034).
    """

    path: TreePath
    description: str | None = None
    hypervisor: str
    base_vm: str
    cpu: int | None = None
    memory_mb: int | None = None
    disk_gb: int | None = None
    state: DescriptorState = DescriptorState.PROVISIONED
    vm_id: str | None = None
