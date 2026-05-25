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

import cmd2
from tinydb import TinyDB

from univorch.connectors.mock import MockConnector
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.service import OrchestratorService


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


def main() -> None:
    db_path = os.environ.get("UNIVORCH_DB", "univorch.tinydb.json")
    shell = UnivOrchShell(build_service(TinyDB(db_path)))
    if len(sys.argv) > 1:
        shell.onecmd_plus_hooks(" ".join(sys.argv[1:]))  # bash mode: one command
    else:
        shell.cmdloop()  # interactive REPL
