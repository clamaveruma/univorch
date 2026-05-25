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
from univorch.service import OperationError, OrchestratorService

# Rich style per descriptor state (cmd2 3.x renders poutput with Rich)
_STATE_STYLE = {
    DescriptorState.PROVISIONED: "dim",
    DescriptorState.DEPLOYED: "green",
    DescriptorState.BROKEN: "red",
    DescriptorState.UNREACHABLE: "yellow",
}


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
        """Turn a path argument into an absolute tree path, relative to the CWD."""
        if not path:
            return self._cwd
        if path.startswith("/"):
            return path
        base = "" if self._cwd == "/" else self._cwd  # avoid a leading "//"
        return f"{base}/{path}"

    def do_cd(self, arg: str) -> None:
        """Change the current folder (absolute or relative path; no arg = root)."""
        target = arg.strip()
        self._cwd = self._resolve(target) if target else "/"
        self.prompt = self._prompt()

    def do_pwd(self, arg: str) -> None:
        """Print the current folder."""
        self.poutput(self._cwd)

    def do_list(self, arg: str) -> None:
        """List the folders and descriptors under a path (default: current folder)."""
        for entry in self._service.list_tree(self._resolve(arg.strip())):
            state = f"  [{entry.state}]" if entry.state else ""
            self.poutput(f"{entry.path}  ({entry.kind}){state}")

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
