"""Domain entities: folders and descriptors.

Pydantic models, so they serialise to and from TinyDB with ``model_dump()`` /
``model_validate()`` (DEC-034). The tree uses a materialized path: each entity's
full path is its key.

Only *syntactic* path validation lives here. Contextual checks (parent exists,
create vs update, references) and RBAC belong to the apply/service layer
(DEC-027, DEC-031), which can see the whole tree.
"""

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import AfterValidator, BaseModel, Field

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


class JobStatus(StrEnum):
    """Lifecycle state of a Job."""

    PENDING = "pending"  # created, not started yet
    RUNNING = "running"  # executing
    COMPLETED = "completed"  # finished successfully
    FAILED = "failed"  # finished with an error


class OperationType(StrEnum):
    """Kind of operation recorded by a Job; grows as new operations are added."""

    DEPLOY = "deploy"
    UNDEPLOY = "undeploy"
    START = "start"
    STOP = "stop"
    CREATE_FOLDER = "create_folder"
    CREATE_DESCRIPTOR = "create_descriptor"


class Job(BaseModel):
    """An operation recorded for audit and state tracking (DEC-014/028).

    A descriptor's state changes only as the result of a Job (DEC-032).
    """

    # uuid: a job has no natural key like a path; generated on creation
    id: str = Field(default_factory=lambda: uuid4().hex)
    operation_type: OperationType
    target: str  # path of the affected folder or descriptor
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    message: str | None = None


class ApplyDocument(BaseModel):
    """A batch of folders and descriptors to create/update (the ``apply`` input).

    Flat in v1: every item carries its full path. Nested definitions with cascade
    inheritance (a folder's children inheriting its properties) are a Sprint 2
    refinement.
    """

    kind: Literal["apply"] = "apply"
    version: str = "1"
    folders: list[Folder] = Field(default_factory=list)
    descriptors: list[Descriptor] = Field(default_factory=list)
