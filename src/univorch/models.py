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

# A folder/descriptor name: starts with a letter or digit, then may contain
# letters, digits and _ - @ . — enough for usernames-as-emails (juan@uma.es).
# The leading-char restriction keeps '.' and '..' (and dot-files) out, so a
# segment can never be confused with the current/parent directory.
_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_@.-]*")


def is_valid_segment(name: str) -> bool:
    """True if ``name`` is a valid tree-segment (folder/descriptor) name.

    The single source of truth for what a name may look like; both the core
    models and the teaching layer use it instead of duplicating the pattern.
    """
    return _SEGMENT.fullmatch(name) is not None


def _validate_segment_keys(value: dict[str, Any]) -> dict[str, Any]:
    """Reject dict keys that don't match the tree-segment pattern."""
    for name in value:
        if not is_valid_segment(name):
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
        if not is_valid_segment(segment):
            raise ValueError(f"invalid path segment {segment!r} in {path!r}")
    return path


TreePath = Annotated[str, AfterValidator(_validate_path)]


class DescriptorState(StrEnum):
    """Orchestrator-side state of a descriptor (DEC-022/032)."""

    PROVISIONED = "provisioned"
    DEPLOYED = "deployed"
    BROKEN = "broken"
    UNREACHABLE = "unreachable"


class HypervisorDef(BaseModel):
    """A hypervisor declared with ``define hypervisors:`` inside a folder.

    Used both by the YAML input (parsed by ``FolderDef``) and by the persisted
    ``Folder`` record. In YAML, the key is the hypervisor's name (e.g.
    ``mock``); the body lives in this model. ``connector_type`` is the
    registered connector that talks to this hypervisor (today only ``mock``;
    Sprint 3+ adds ``vmware`` and ``proxmox``).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    description: str | None = None
    connector_type: str = Field(alias="type")


class VMTemplateDef(BaseModel):
    """A VM template declared with ``define templates:`` in a folder.

    Same shape as a ``DescriptorDef`` minus the ability to reference another
    template (Pieza 1.A; Pieza 4 will add ``based on:`` for derivation). Used
    both by the YAML input and by the persisted ``Folder`` record.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    description: str | None = None
    hypervisor: str | None = Field(default=None, alias="use hypervisor")
    base_vm: str | None = None
    cpu: int | None = None
    memory_mb: int | None = None
    disk_gb: int | None = None


class Folder(BaseModel):
    """A node in the descriptor tree, addressed by its materialized path.

    Sprint 2 (Pieza 1.A): a folder also carries declared resources
    (hypervisors, VM templates) and an explicit ``imports`` list naming what it
    pulls in from its parent — the basis of cascade inheritance (DEC-012,
    DEC-026). Resolution itself happens elsewhere (Pieza 1.B).
    """

    model_config = ConfigDict(extra="forbid")  # reject unknown fields (typos)

    path: TreePath
    description: str | None = None
    imports: list[str] = Field(default_factory=list)
    hypervisors: dict[str, HypervisorDef] = Field(default_factory=dict)
    vm_templates: dict[str, VMTemplateDef] = Field(default_factory=dict)
    # Opaque metadata for layer-2 applications (DEC-038). The core stores it
    # and never interprets it; the teaching layer keeps {kind, desktop} here.
    metadata: dict[str, Any] = Field(default_factory=dict)


class Descriptor(BaseModel):
    """A VM definition in the tree (analogous to a file descriptor in an OS).

    Sprint 2 (Pieza 1.A): ``hypervisor`` and ``base_vm`` are now optional —
    a descriptor may instead reference a template via ``template`` and let the
    Resolver fill in the rest later (Pieza 1.B/1.C). Until then, deploy of a
    template-based descriptor will fail (the connector lookup needs a name).
    """

    model_config = ConfigDict(extra="forbid")  # reject unknown fields (typos)

    path: TreePath
    description: str | None = None
    hypervisor: str | None = None
    base_vm: str | None = None
    template: str | None = None
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
    nesting position give it its place in the tree.

    YAML uses ``use hypervisor:`` and ``use template:`` for references to
    declared resources; both map to Python field names via Pydantic aliases.
    ``hypervisor`` and ``base_vm`` are optional because they can come from a
    template (Pieza 1.A; resolution in Pieza 1.B).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    description: str | None = None
    hypervisor: str | None = Field(default=None, alias="use hypervisor")
    base_vm: str | None = None
    template: str | None = Field(default=None, alias="use template")
    cpu: int | None = None
    memory_mb: int | None = None
    disk_gb: int | None = None


class FolderDef(BaseModel):
    """A folder inside a YAML. Mixed items: keys ending in ``/`` are subfolders,
    others are VMs. The model_validator splits them into ``folders`` and
    ``descriptors`` internally.

    Sprint 2 (Pieza 1.A): folders can declare resources (``define hypervisors:``,
    ``define templates:``) and an explicit ``import:`` list. The YAML
    keys with spaces are mapped to Python field names via Pydantic aliases.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    description: str | None = None
    imports: list[str] = Field(default_factory=list, alias="import")
    hypervisors: dict[str, HypervisorDef] = Field(
        default_factory=dict, alias="define hypervisors"
    )
    vm_templates: dict[str, VMTemplateDef] = Field(
        default_factory=dict, alias="define templates"
    )
    # Opaque metadata for layer-2 applications (DEC-038); passed through to the
    # persisted Folder unchanged. The teaching layer puts {kind, desktop} here.
    metadata: dict[str, Any] = Field(default_factory=dict)
    folders: dict[str, "FolderDef"] = Field(default_factory=dict)
    descriptors: dict[str, DescriptorDef] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _split(cls, data: Any) -> Any:
        return _split_items(
            data,
            reserved={
                "description",
                "import",
                "define hypervisors",
                "define templates",
                "metadata",
            },
        )

    @field_validator("imports", mode="before")
    @classmethod
    def _normalize_imports(cls, value: Any) -> Any:
        """Accept ``import: ALL`` and single strings; normalize to a list."""
        if isinstance(value, str):
            return ["*"] if value == "ALL" else [value]
        return value

    @field_validator("folders", "descriptors", "hypervisors", "vm_templates")
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

    Resources (``define hypervisors:``, ``define templates:``) and
    ``import:`` are **rejected** at this level — they belong inside a folder
    definition. The destination folder's own resources are not modifiable by a
    load.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["definition"] = "definition"
    version: str = "1"
    folders: dict[str, FolderDef] = Field(default_factory=dict)
    descriptors: dict[str, DescriptorDef] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _split(cls, data: Any) -> Any:
        if isinstance(data, dict):
            forbidden = {"import", "define hypervisors", "define templates"}
            present = sorted(forbidden & set(data.keys()))
            if present:
                raise ValueError(
                    f"{present} cannot appear at the top of the document; "
                    "they belong inside a folder definition. Wrap them in a "
                    "first-level folder (e.g. 'lab/:')."
                )
        return _split_items(data, reserved={"kind", "version"})

    @field_validator("folders", "descriptors")
    @classmethod
    def _check_names(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_segment_keys(value)


FolderDef.model_rebuild()  # resolve the self-reference in folders: dict[str, FolderDef]
