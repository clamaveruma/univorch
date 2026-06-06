"""Orchestrator service: the single entry point for all interfaces (DEC-031).

CLI, web GUI and the teaching layer all go through this facade; none talk to the
repositories, the connectors or the Jobs engine directly. The facade validates a
request and rejects the invalid ones (raising ``OperationError``, no Job created),
then builds the Command and hands it to the Jobs engine.
"""

import posixpath
from typing import Literal

from pydantic import BaseModel

from univorch.connectors import CONNECTOR_TYPES
from univorch.connectors.base import HypervisorConnector
from univorch.connectors.types import RuntimeState
from univorch.jobs.commands import (
    Command,
    CreateDescriptorCommand,
    CreateFolderCommand,
    DeployCommand,
    StartCommand,
    StopCommand,
    UndeployCommand,
)
from univorch.jobs.engine import JobEngine
from univorch.models import (
    DefinitionDocument,
    Descriptor,
    DescriptorDef,
    DescriptorState,
    Folder,
    FolderDef,
    Job,
    JobStatus,
)
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.resolver import _find_hypervisor, resolve_descriptor

# the four machine commands share the same constructor (path, descriptors_repo,
# folders_repo, connector) — DeployCommand uses folders_repo to resolve the
# effective base_vm; the others accept it for signature uniformity (Pieza 1.C)
type MachineCommand = type[DeployCommand | UndeployCommand | StartCommand | StopCommand]


class OperationError(Exception):
    """A request rejected during validation; no Job is created.

    Carries all the validation messages so the interface can show them.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class DescriptorStatus(BaseModel):
    """Read result for one descriptor: orchestrator state + hypervisor runtime."""

    path: str
    state: DescriptorState
    runtime_state: RuntimeState | None = None  # None unless deployed
    vm_id: str | None = None


class TreeEntry(BaseModel):
    """One node in a tree listing (a folder or a descriptor)."""

    path: str
    kind: Literal["folder", "descriptor"]
    state: DescriptorState | None = None  # None for folders


class LoadResult(BaseModel):
    """Per-item outcome of a ``load`` (best-effort report, DEC-027)."""

    path: str
    ok: bool
    message: str


class OrchestratorService:
    """Single facade over repositories, connectors and the Jobs engine.

    Folders and descriptors are identified by their ``path``: the full
    materialized path in the tree (e.g. ``/lab/networks/student01``).

    Hypervisors are NOT injected as live instances any more. The service
    receives the **connector types registry** (``connector_types``) and
    instantiates a live session on demand whenever a hypervisor declared in
    the tree is first used. The live sessions live in ``_connection_pool``,
    indexed by the path of the folder that declared each hypervisor — two
    hypervisors with the same name in different branches keep distinct
    sessions (Sprint 2 Pieza 3c; DEC-029).
    """

    def __init__(
        self,
        folders_repo: FolderRepository,
        descriptors_repo: DescriptorRepository,
        jobs_repo: JobRepository,
        connector_types: dict[str, type[HypervisorConnector]] = CONNECTOR_TYPES,
    ) -> None:
        self._folders = folders_repo
        self._descriptors = descriptors_repo
        self._connector_types = connector_types
        # live sessions keyed by the folder path where the hypervisor is declared
        self._connection_pool: dict[str, HypervisorConnector] = {}
        self._engine = JobEngine(jobs_repo)

    def deploy(self, path: str) -> Job:
        return self._run(self._machine_command(DeployCommand, path))

    def undeploy(self, path: str) -> Job:
        return self._run(self._machine_command(UndeployCommand, path))

    def start(self, path: str) -> Job:
        return self._run(self._machine_command(StartCommand, path))

    def stop(self, path: str) -> Job:
        return self._run(self._machine_command(StopCommand, path))

    def status(self, path: str) -> DescriptorStatus:
        """Report a descriptor's status: its orchestrator state and, only when it
        is deployed, the live runtime state queried from its hypervisor.

        A read — creates no Job. Raises OperationError if the path is unknown.
        """
        descriptor = self._descriptors.get(path)
        if descriptor is None:
            raise OperationError([f"VM not found: {path}"])
        runtime: RuntimeState | None = None
        # runtime state only exists for a deployed VM — ask its hypervisor.
        # Pieza 1.C: resolve template references to find the effective hypervisor;
        # tolerant on failure (status is a read, must not raise) — if the
        # resolver can't determine a hypervisor we leave runtime as None.
        if descriptor.state == DescriptorState.DEPLOYED and descriptor.vm_id:
            try:
                resolved = resolve_descriptor(descriptor, self._folders)
            except ValueError:
                resolved = descriptor
            if resolved.hypervisor:
                # status is a read — never raise on a misconfigured tree; report
                # UNKNOWN runtime if we can't reach the hypervisor record.
                try:
                    connector = self._resolve_hypervisor(resolved)
                except OperationError:
                    runtime = RuntimeState.UNKNOWN
                else:
                    runtime = connector.get_status(descriptor.vm_id)
        return DescriptorStatus(
            path=path,
            state=descriptor.state,
            runtime_state=runtime,
            vm_id=descriptor.vm_id,
        )

    def list_tree(self, path: str = "/", recursive: bool = False) -> list[TreeEntry]:
        """List what lives under ``path``, sorted by path.

        Returns the descendants of ``path`` (not ``path`` itself). By default only
        the direct children are returned (like ``ls``); with ``recursive=True`` the
        whole subtree is returned (like ``tree``). Folders and descriptors live in
        separate tables, so this reads each one's subtree and merges them. Reads the
        DB only (no hypervisor calls) and creates no Job.
        """
        nodes: list[TreeEntry] = [
            TreeEntry(path=folder.path, kind="folder")
            for folder in self._folders.subtree(path)
        ]
        nodes += [
            TreeEntry(path=d.path, kind="descriptor", state=d.state)
            for d in self._descriptors.subtree(path)
        ]
        entries = [n for n in nodes if n.path != path]  # exclude the listed folder
        if not recursive:  # keep only direct children (one level down)
            entries = [e for e in entries if posixpath.dirname(e.path) == path]
        return sorted(entries, key=lambda entry: entry.path)

    def folder_exists(self, path: str) -> bool:
        """True if ``path`` is the root or an existing folder (a read; no Job).

        Used by the interfaces to validate navigation (``cd``/``list``) before
        acting. The root ``/`` has no stored Folder record, so it is implicit.
        """
        return path == "/" or self._folders.exists(path)

    def inspect(self, path: str, *, resolved: bool = True) -> Descriptor | Folder:
        """Return the entity at ``path`` (descriptor or folder).

        For descriptors, ``resolved=True`` runs the cascade resolver so the
        returned record has fields filled in via templates. Tolerant: if the
        resolver fails (template not accessible) the local descriptor is
        returned instead — inspect is a read and must not raise.

        For folders, both modes return the persisted record (the cascade-aware
        view for folders will arrive with the annotated mode, future sprint).
        Raises ``OperationError`` if ``path`` is neither a descriptor nor a folder.
        """
        descriptor = self._descriptors.get(path)
        if descriptor is not None:
            if resolved:
                try:
                    return resolve_descriptor(descriptor, self._folders)
                except ValueError:
                    return descriptor  # tolerant: degraded info is still useful
            return descriptor
        folder = self._folders.get(path)
        if folder is not None:
            return folder
        raise OperationError([f"not found: {path}"])

    def load(
        self, document: DefinitionDocument, destination: str = "/"
    ) -> list[LoadResult]:
        """Load ``document`` into ``destination``: create the folders and VMs.

        The document is **relative** (no paths inside); ``destination`` is where
        it gets attached. The destination must already exist (an explicit pre-
        condition, separate from per-item validation — DEC-027).

        Items are run parent-first by walking the nested structure: a folder is
        created before its children, every folder before its sibling descriptors
        at the same level. Each item is its own Job; best-effort means rejected
        items are recorded while the rest continue. (Batch all-or-reject and a
        parent Job for the whole load are future work, DEC-028.)
        """
        if not self.folder_exists(destination):
            raise OperationError([f"destination folder not found: {destination}"])
        results: list[LoadResult] = []
        # walk folders first at this level, then descriptors — same recursive shape
        for name, folder_def in document.folders.items():
            results.extend(self._load_folder(name, folder_def, destination))
        for name, descriptor_def in document.descriptors.items():
            path = posixpath.join(destination, name)
            results.append(self._load_descriptor(path, descriptor_def))
        return results

    def _load_folder(
        self, name: str, folder_def: FolderDef, base: str
    ) -> list[LoadResult]:
        """Materialize one folder and its contents under ``base``."""
        path = posixpath.join(base, name)
        # carry across the folder's own resources and imports; folder defs and
        # persisted folders mirror these fields exactly so a plain copy works
        folder = Folder(
            path=path,
            description=folder_def.description,
            imports=folder_def.imports,
            hypervisors=folder_def.hypervisors,
            vm_templates=folder_def.vm_templates,
        )
        results = [self._load_one(CreateFolderCommand(folder, self._folders))]
        # recurse: subfolders first (so they exist when their items try to attach),
        # then this folder's own descriptors at the same level
        for sub_name, sub_def in folder_def.folders.items():
            results.extend(self._load_folder(sub_name, sub_def, path))
        for descriptor_name, descriptor_def in folder_def.descriptors.items():
            descriptor_path = posixpath.join(path, descriptor_name)
            results.append(self._load_descriptor(descriptor_path, descriptor_def))
        return results

    def _load_descriptor(self, path: str, def_: DescriptorDef) -> LoadResult:
        """Materialize one descriptor at ``path``."""
        # exclude_none keeps optional fields (cpu/memory_mb/disk_gb/description)
        # absent from the YAML out of the Descriptor too, matching the user's intent
        descriptor = Descriptor(path=path, **def_.model_dump(exclude_none=True))
        return self._load_one(
            CreateDescriptorCommand(descriptor, self._descriptors, self._folders)
        )

    def _resolve_hypervisor(self, resolved: Descriptor) -> HypervisorConnector:
        """Return a live connector for the hypervisor named in ``resolved``.

        Walks the tree from the descriptor's folder, finds the ``HypervisorDef``
        with that name, and returns a live session — from the connection pool if
        one already exists, freshly minted otherwise. The pool key is the path
        of the folder that declared the hypervisor (Pieza 3c).

        Raises ``OperationError`` if the name is not accessible from the
        descriptor's folder or its ``type:`` is not in the connector registry
        (a misconfigured tree caught at use time, the only check we keep —
        see DEC-027's fail-fast spirit).
        """
        assert resolved.hypervisor is not None  # caller's responsibility
        folder_path = posixpath.dirname(resolved.path) or "/"
        found = _find_hypervisor(resolved.hypervisor, folder_path, self._folders)
        if found is None:
            raise OperationError(
                [
                    f"hypervisor not accessible from {resolved.path}: "
                    f"{resolved.hypervisor!r}"
                ]
            )
        hv_def, hv_path = found
        if hv_def.connector_type not in self._connector_types:
            raise OperationError(
                [
                    f"hypervisor {resolved.hypervisor!r} has unknown connector "
                    f"type {hv_def.connector_type!r} "
                    f"(available: {sorted(self._connector_types)})"
                ]
            )
        if hv_path not in self._connection_pool:
            cls = self._connector_types[hv_def.connector_type]
            self._connection_pool[hv_path] = cls()  # spawn live session
        return self._connection_pool[hv_path]

    def _machine_command(self, command_cls: MachineCommand, path: str) -> Command:
        """Build a machine command for ``path``.

        Loads the descriptor (rejects if missing) and resolves its hypervisor's
        connector (rejects if unknown), then constructs the command with both.
        """
        descriptor = self._descriptors.get(path)
        if descriptor is None:
            raise OperationError([f"VM not found: {path}"])
        # Pieza 1.C: resolve template references before looking up the connector,
        # so descriptors that inherit hypervisor from a template work end-to-end.
        # A resolver failure (template not accessible) or a still-None hypervisor
        # become OperationErrors with a clear message; the front-ends turn them
        # into red lines without ever creating a Job (DEC-027).
        try:
            resolved = resolve_descriptor(descriptor, self._folders)
        except ValueError as resolver_error:
            raise OperationError([str(resolver_error)]) from resolver_error
        if resolved.hypervisor is None:
            raise OperationError([f"VM has no effective hypervisor: {path}"])
        connector = self._resolve_hypervisor(resolved)
        return command_cls(path, self._descriptors, self._folders, connector)

    def _run(self, command: Command) -> Job:
        """Run an already-built command.

        Validates first — any error raises OperationError and creates no Job —
        then hands it to the engine, which records and returns the Job.
        """
        errors = command.validate()
        if errors:
            raise OperationError(errors)  # rejected: no Job created
        return self._engine.run(command)

    def _load_one(self, command: Command) -> LoadResult:
        """Run one load item and return its result row; never raises.

        Wraps the two outcomes of ``_run`` so ``load`` can collect a result per
        item and keep going (best-effort).
        """
        try:
            job = self._run(command)  # it ran: there is a Job (COMPLETED or FAILED)
            return LoadResult(
                path=command.target,
                ok=job.status == JobStatus.COMPLETED,
                message=job.message or "",
            )
        except OperationError as error:  # rejected by validation: no Job created
            return LoadResult(
                path=command.target, ok=False, message="; ".join(error.errors)
            )
