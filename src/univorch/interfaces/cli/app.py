"""Command-line interface (cmd2): a single dual-mode shell.

A thin interface (DEC-031): each command translates user input into a call to the
``OrchestratorService`` and renders the result. The same ``do_*`` methods serve
both the interactive REPL (a shell with a prompt and history) and bash mode (a
single command passed as arguments).

In Sprint 1 the CLI assembles the service itself, in its own process (the
composition root): a disk-backed TinyDB plus the in-memory mock connector. Each
CLI process therefore has its own mock state — fine within one REPL session
(the demo), reset across separate invocations. A persistent daemon is Sprint 2.
"""

import os
import posixpath
import sys
from collections.abc import Callable

import cmd2
from pydantic import ValidationError
from ruamel.yaml.error import YAMLError
from tinydb import TinyDB

from univorch.connectors.mock import MockConnector
from univorch.models import DescriptorState, Job, JobStatus
from univorch.parser import load_apply_file
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.service import OperationError, OrchestratorService, TreeEntry

# Rich style per descriptor state (cmd2 3.x renders poutput with Rich)
_STATE_STYLE = {
    DescriptorState.PROVISIONED: "dim",
    DescriptorState.DEPLOYED: "green",
    DescriptorState.BROKEN: "red",
    DescriptorState.UNREACHABLE: "yellow",
}

# A fixed-width glyph per descriptor state, shown as the leading marker in listings.
# Geometric shapes (single cell) so columns line up in any terminal.
_STATE_GLYPH = {
    DescriptorState.PROVISIONED: "□",  # empty box: no VM
    DescriptorState.DEPLOYED: "■",  # filled box: the VM exists
    DescriptorState.BROKEN: "✗",  # error
    DescriptorState.UNREACHABLE: "▲",  # alert: hypervisor not reachable
}
_FOLDER_STYLE = "blue"  # folders shown in blue, like 'ls' dircolors


def build_service(db: TinyDB) -> OrchestratorService:
    """Wire the service from a TinyDB: the repositories + the mock connector."""
    return OrchestratorService(
        FolderRepository(db),
        DescriptorRepository(db),
        JobRepository(db),
        {"mock": MockConnector.with_demo_templates()},
    )


class UnivOrchShell(cmd2.Cmd):
    """The UnivOrch interactive shell."""

    def __init__(self, service: OrchestratorService) -> None:
        super().__init__()
        self._service = service
        self._cwd = "/"  # current folder, like a shell working directory
        self.prompt = self._prompt()

    def _prompt(self) -> str:
        return f"univorch {self._cwd}> "

    def _resolve(self, path: str) -> str:
        """Normalize a path argument to an absolute tree path.

        Relative paths join onto the current folder; '.' and '..' are resolved
        and the result never climbs above the root (``..`` at ``/`` stays ``/``).
        """
        if not path:
            return self._cwd
        combined = path if path.startswith("/") else posixpath.join(self._cwd, path)
        return posixpath.normpath(combined)

    def do_cd(self, arg: str) -> None:
        """Change the current folder ('..' allowed; no arg does nothing)."""
        target = arg.strip()
        if not target:
            return  # no-op; use 'pwd' to see the current folder
        resolved = self._resolve(target)
        if not self._service.folder_exists(resolved):
            self.perror(f"cd: {resolved}: no such folder")
            return
        self._cwd = resolved
        self.prompt = self._prompt()

    def do_pwd(self, arg: str) -> None:
        """Print the current folder."""
        self.poutput(self._cwd)

    def do_list(self, arg: str) -> None:
        """List the current folder's contents, one level (like ls)."""
        path = self._resolve(arg.strip())
        if not self._service.folder_exists(path):
            self.perror(f"list: {path}: no such folder")
            return
        if path != "/":
            self.poutput("  ../", style=_FOLDER_STYLE)  # row to go up a level
        for entry in self._service.list_tree(path):
            text, style = self._render_entry(entry)
            self.poutput(text, style=style)

    def do_ls(self, arg: str) -> None:
        """Alias for 'list'."""
        self.do_list(arg)

    def do_tree(self, arg: str) -> None:
        """Print the whole subtree under a path (default: current folder)."""
        path = self._resolve(arg.strip())
        if not self._service.folder_exists(path):
            self.perror(f"tree: {path}: no such folder")
            return
        root_depth = 0 if path == "/" else path.count("/")
        for entry in self._service.list_tree(path, recursive=True):
            indent = "  " * (entry.path.count("/") - root_depth - 1)
            text, style = self._render_entry(entry)
            self.poutput(indent + text, style=style)

    def complete_apply(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        """Tab-complete the YAML file argument against the filesystem."""
        return self.path_complete(text, line, begidx, endidx)

    def _render_entry(self, entry: TreeEntry) -> tuple[str, str]:
        """Return the (text, Rich style) for one listing row.

        Folders get a trailing '/' and no glyph (ls -F style); descriptors get a
        state glyph. Both indent the name to the same column so listings align.
        """
        name = posixpath.basename(entry.path)
        if entry.kind == "folder" or entry.state is None:
            return f"  {name}/", _FOLDER_STYLE
        return f"{_STATE_GLYPH[entry.state]} {name}", _STATE_STYLE[entry.state]

    def do_deploy(self, arg: str) -> None:
        """Deploy a descriptor: clone its base VM (provisioned -> deployed)."""
        self._machine(self._service.deploy, arg)

    def do_undeploy(self, arg: str) -> None:
        """Undeploy a descriptor: delete its VM (-> provisioned)."""
        self._machine(self._service.undeploy, arg)

    def do_start(self, arg: str) -> None:
        """Start (power on) a deployed descriptor's VM."""
        self._machine(self._service.start, arg)

    def do_stop(self, arg: str) -> None:
        """Stop (power off) a deployed descriptor's VM."""
        self._machine(self._service.stop, arg)

    def _machine(self, operation: Callable[[str], Job], arg: str) -> None:
        """Run a machine command; print the Job message (green/red) or the error."""
        try:
            job = operation(self._resolve(arg.strip()))
        except OperationError as error:
            self.perror("; ".join(error.errors))
            return
        style = "green" if job.status == JobStatus.COMPLETED else "red"
        self.poutput(job.message or "", style=style)

    def do_status(self, arg: str) -> None:
        """Show a descriptor's state and, if deployed, its runtime state."""
        try:
            info = self._service.status(self._resolve(arg.strip()))
        except OperationError as error:
            self.perror("; ".join(error.errors))
            return
        style = _STATE_STYLE.get(info.state, "white")
        runtime = info.runtime_state or "-"
        vm_id = info.vm_id or "-"
        self.poutput(
            f"{info.path}  state=[{style}]{info.state}[/]  "
            f"runtime={runtime}  vm_id={vm_id}",
            markup=True,
        )

    def do_apply(self, arg: str) -> None:
        """Apply a YAML file: create/update folders and descriptors from it."""
        try:
            document = load_apply_file(arg.strip())
        except (OSError, YAMLError, ValidationError) as error:
            self.perror(str(error))
            return
        for result in self._service.apply(document):
            style = "green" if result.ok else "red"
            self.poutput(f"{result.path}  {result.message}", style=style)


def main() -> None:
    db_path = os.environ.get("UNIVORCH_DB", "univorch.tinydb.json")
    shell = UnivOrchShell(build_service(TinyDB(db_path)))
    if len(sys.argv) > 1:
        shell.onecmd_plus_hooks(" ".join(sys.argv[1:]))  # bash mode: one command
    else:
        shell.cmdloop()  # interactive REPL
