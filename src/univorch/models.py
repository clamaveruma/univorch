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
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

_SEGMENT = re.compile(r"[A-Za-z0-9_-]+")  # provisional pattern, to be refined later


def _validate_segment_keys(value: dict[str, Any]) -> dict[str, Any]:
    """Reject dict keys that don't match the tree-segment pattern."""
    for name in value:
        if not _SEGMENT.fullmatch(name):
            raise ValueError(f"invalid name {name!r}; must match {_SEGMENT.pattern}")
    return value


def _split_items(data: Any, *, reserved: set[str]) -> Any:
    """Split a YAML dict body into reserved keys + ``folders`` + ``descriptors``.

    Keys ending in '/' go into ``folders`` (name normalized without the slash);
    every other non-reserved key goes into ``descriptors``. A None value means
    "empty container" (e.g. ``lab/:`` with no body). The result is the shape
    Pydantic then validates against the model's typed fields.

    Pass-through: if ``data`` already has explicit ``folders`` or ``descriptors``
    keys, it is taken as already normalized — useful for Python-side construction
    (``DefinitionDocument(folders={...})``) and for re-validation cycles.
    """
    if data is None:
        return {"folders": {}, "descriptors": {}}
    if not isinstance(data, dict):
        return data
    if "folders" in data or "descriptors" in data:
        return data  # already normalized; do not split a second time
    result: dict[str, Any] = {}
    folders: dict[str, Any] = {}
    descriptors: dict[str, Any] = {}
    for key, value in data.items():
        if key in reserved:
            result[key] = value
        elif isinstance(key, str) and key.endswith("/"):
            folders[key[:-1]] = value
        else:
            descriptors[key] = value
    result["folders"] = folders
    result["descriptors"] = descriptors
    return result


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

    model_config = ConfigDict(extra="forbid")  # reject unknown fields (typos)

    path: TreePath
    description: str | None = None


class Descriptor(BaseModel):
    """A VM definition in the tree (analogous to a file descriptor in an OS).

    Sprint 1 carries the configuration inline (``hypervisor``, ``base_vm``,
    specs); Sprint 2 moves it to an inherited ``definition`` (DEC-026/034).
    """

    model_config = ConfigDict(extra="forbid")  # reject unknown fields (typos)

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


class DescriptorDef(BaseModel):
    """A VM definition inside a YAML — no path; the load destination plus the
    nesting position give it its place in the tree."""

    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    hypervisor: str
    base_vm: str
    cpu: int | None = None
    memory_mb: int | None = None
    disk_gb: int | None = None


class FolderDef(BaseModel):
    """A folder inside a YAML. Mixed items: keys ending in ``/`` are subfolders,
    others are VMs. The model_validator splits them into ``folders`` and
    ``descriptors`` internally; ``description`` is the only reserved key here.
    """

    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    folders: dict[str, "FolderDef"] = Field(default_factory=dict)
    descriptors: dict[str, DescriptorDef] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _split(cls, data: Any) -> Any:
        return _split_items(data, reserved={"description"})

    @field_validator("folders", "descriptors")
    @classmethod
    def _check_names(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_segment_keys(value)


class DefinitionDocument(BaseModel):
    """A YAML definition to be loaded into a destination folder.

    The destination is given as an argument to ``service.load``; the document
    itself never carries absolute paths. The destination's own properties are
    not touched by loading — the document only describes what goes inside.
    Reserved at the top level: ``kind`` and ``version``; everything else is an
    item, split by the trailing ``/`` like inside a folder.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["definition"] = "definition"
    version: str = "1"
    folders: dict[str, FolderDef] = Field(default_factory=dict)
    descriptors: dict[str, DescriptorDef] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _split(cls, data: Any) -> Any:
        return _split_items(data, reserved={"kind", "version"})

    @field_validator("folders", "descriptors")
    @classmethod
    def _check_names(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_segment_keys(value)


FolderDef.model_rebuild()  # resolve the self-reference in folders: dict[str, FolderDef]
