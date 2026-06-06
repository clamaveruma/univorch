"""Command-line interface (cmd2): a single dual-mode shell.

A thin interface (DEC-031): each command translates user input into a call to the
``OrchestratorService`` and renders the result. The same ``do_*`` methods serve
both the interactive REPL (a shell with a prompt and history) and bash mode (a
single command passed as arguments).

Each command declares an argparse parser via ``@cmd2.with_argparser``; cmd2 then
parses the arguments and autogenerates structured, coloured help (``help <cmd>``).

In Sprint 1 the CLI assembles the service itself, in its own process (the
composition root): a disk-backed TinyDB plus the in-memory mock connector. Each
CLI process therefore has its own mock state — fine within one REPL session
(the demo), reset across separate invocations. A persistent daemon is Sprint 2.
"""

import argparse
import os
import posixpath
import sys
from collections.abc import Callable

import cmd2
from pydantic import ValidationError
from ruamel.yaml.error import YAMLError
from tinydb import TinyDB

from univorch.models import Descriptor, DescriptorState, Folder, Job, JobStatus
from univorch.parser import parse_definition_file
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.service import OperationError, OrchestratorService, TreeEntry

# Rich style per descriptor state (cmd2 3.x renders poutput with Rich)
# 'deployed' uses the terminal's default colour on purpose: green would suggest
# 'running' (runtime), but list/status only show the descriptor's own state — the
# runtime state of the VM lives in the hypervisor and is reported separately.
_STATE_STYLE = {
    DescriptorState.PROVISIONED: "dim",
    DescriptorState.DEPLOYED: "default",
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

# Shared by 'list' and 'ls'; the glyph legend lives in the help so users can find it.
_LIST_DESC = (
    "List one level of a folder, like ls. Folders show as 'name/' (blue); "
    "descriptors show a state glyph:  □ provisioned   ■ deployed   "
    "✗ broken   ▲ unreachable"
)


def _path_arg_parser(description: str, *, required: bool) -> cmd2.Cmd2ArgumentParser:
    """Build a parser for a command that takes a single tree path."""
    parser = cmd2.Cmd2ArgumentParser(description=description)
    if required:
        parser.add_argument("path", help="tree path (absolute or relative)")
    else:
        parser.add_argument(
            "path", nargs="?", default="", help="tree path (default: current folder)"
        )
    return parser


def _tree_arg_parser() -> cmd2.Cmd2ArgumentParser:
    """Build the parser for 'tree' (path + optional folders-only flag)."""
    parser = cmd2.Cmd2ArgumentParser(
        description="Print the whole subtree under a path (default: current folder)."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="",
        help="tree path (default: current folder)",
    )
    parser.add_argument(
        "-d",
        "--folders-only",
        action="store_true",
        help="show only folders, hide VMs (like Linux 'tree -d')",
    )
    return parser


def _load_arg_parser() -> cmd2.Cmd2ArgumentParser:
    """Build the parser for 'load' (file path + optional destination)."""
    parser = cmd2.Cmd2ArgumentParser(
        description=(
            "Load a YAML definition into a folder. The file describes folders "
            "and VMs to place inside the destination (default: current folder); "
            "it never modifies the destination's own properties."
        )
    )
    parser.add_argument(
        "file",
        help="path to the YAML definition file",
        completer=cmd2.Cmd.path_complete,
    )
    parser.add_argument(
        "destination",
        nargs="?",
        default="",
        help="tree folder to load into (default: current folder)",
    )
    return parser


def _folder_label(path: str) -> str:
    """Render a folder path with the trailing '/' that YAML uses (except root)."""
    return path if path == "/" else f"{path}/"


def _inspect_arg_parser() -> cmd2.Cmd2ArgumentParser:
    """Build the parser for 'inspect' (a tree path + the --local flag)."""
    parser = cmd2.Cmd2ArgumentParser(
        description=(
            "Show the entity at a tree path (descriptor or folder). "
            "By default, descriptors are shown with their template merged in; "
            "with --local, only what's written at that node."
        )
    )
    parser.add_argument("path", help="tree path (absolute or relative)")
    parser.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="show the local definition only, without resolving templates",
    )
    return parser


def build_service(db: TinyDB) -> OrchestratorService:
    """Wire the service from a TinyDB. Connector types come from the registry
    default (``CONNECTOR_TYPES``); live sessions spin up on demand from the
    hypervisors declared in the tree."""
    return OrchestratorService(
        FolderRepository(db),
        DescriptorRepository(db),
        JobRepository(db),
    )


class UnivOrchShell(cmd2.Cmd):
    """The UnivOrch interactive shell."""

    def __init__(self, service: OrchestratorService) -> None:
        super().__init__()
        self._service = service
        self._cwd = "/"  # current folder, like a shell working directory
        self.prompt = self._prompt()

    def _prompt(self) -> str:
        return f"univorch {_folder_label(self._cwd)}> "

    def _resolve(self, path: str) -> str:
        """Normalize a path argument to an absolute tree path.

        Relative paths join onto the current folder; '.' and '..' are resolved
        and the result never climbs above the root (``..`` at ``/`` stays ``/``).
        """
        if not path:
            return self._cwd
        combined = path if path.startswith("/") else posixpath.join(self._cwd, path)
        return posixpath.normpath(combined)

    @cmd2.with_argparser(
        _path_arg_parser(
            "Change the current folder ('..' allowed; no arg does nothing).",
            required=False,
        )
    )
    def do_cd(self, args: argparse.Namespace) -> None:
        target = args.path.strip()
        if not target:
            return  # no-op; use 'pwd' to see the current folder
        resolved = self._resolve(target)
        if not self._service.folder_exists(resolved):
            self.perror(f"cd: {resolved}: no such folder")
            return
        self._cwd = resolved
        self.prompt = self._prompt()

    @cmd2.with_argparser(
        cmd2.Cmd2ArgumentParser(description="Print the current folder.")
    )
    def do_pwd(self, args: argparse.Namespace) -> None:
        self.poutput(_folder_label(self._cwd))

    @cmd2.with_argparser(_path_arg_parser(_LIST_DESC, required=False))
    def do_list(self, args: argparse.Namespace) -> None:
        self._list(args.path.strip())

    @cmd2.with_argparser(_path_arg_parser(_LIST_DESC, required=False))
    def do_ls(self, args: argparse.Namespace) -> None:
        self._list(args.path.strip())

    def _list(self, path_arg: str) -> None:
        """List one level of a folder (shared by 'list' and 'ls')."""
        path = self._resolve(path_arg)
        if not self._service.folder_exists(path):
            self.perror(f"list: {path}: no such folder")
            return
        if path != "/":
            self.poutput("  ../", style=_FOLDER_STYLE)  # row to go up a level
        for entry in self._service.list_tree(path):
            text, style = self._render_entry(entry)
            self.poutput(text, style=style)

    @cmd2.with_argparser(_tree_arg_parser())
    def do_tree(self, args: argparse.Namespace) -> None:
        path = self._resolve(args.path.strip())
        if not self._service.folder_exists(path):
            self.perror(f"tree: {path}: no such folder")
            return
        root_depth = 0 if path == "/" else path.count("/")
        entries = self._service.list_tree(path, recursive=True)
        if args.folders_only:
            entries = [e for e in entries if e.kind == "folder"]
        for entry in entries:
            indent = "  " * (entry.path.count("/") - root_depth - 1)
            text, style = self._render_entry(entry)
            self.poutput(indent + text, style=style)

    def _render_entry(self, entry: TreeEntry) -> tuple[str, str]:
        """Return the (text, Rich style) for one listing row.

        Folders get a trailing '/' and no glyph (ls -F style); descriptors get a
        state glyph. Both indent the name to the same column so listings align.
        """
        name = posixpath.basename(entry.path)
        if entry.kind == "folder" or entry.state is None:
            return f"  {name}/", _FOLDER_STYLE
        return f"{_STATE_GLYPH[entry.state]} {name}", _STATE_STYLE[entry.state]

    @cmd2.with_argparser(
        _path_arg_parser(
            "Deploy a VM: clone its base image on the hypervisor "
            "(provisioned -> deployed).",
            required=True,
        )
    )
    def do_deploy(self, args: argparse.Namespace) -> None:
        self._machine(self._service.deploy, args.path)

    @cmd2.with_argparser(
        _path_arg_parser(
            "Undeploy a VM: delete it from the hypervisor (-> provisioned). "
            "The definition stays.",
            required=True,
        )
    )
    def do_undeploy(self, args: argparse.Namespace) -> None:
        self._machine(self._service.undeploy, args.path)

    @cmd2.with_argparser(
        _path_arg_parser("Start (power on) a deployed VM.", required=True)
    )
    def do_start(self, args: argparse.Namespace) -> None:
        self._machine(self._service.start, args.path)

    @cmd2.with_argparser(
        _path_arg_parser("Stop (power off) a deployed VM.", required=True)
    )
    def do_stop(self, args: argparse.Namespace) -> None:
        self._machine(self._service.stop, args.path)

    def _machine(self, operation: Callable[[str], Job], arg: str) -> None:
        """Run a machine command; print the Job message (green/red) or the error."""
        try:
            job = operation(self._resolve(arg.strip()))
        except OperationError as error:
            self.perror("; ".join(error.errors))
            return
        style = "green" if job.status == JobStatus.COMPLETED else "red"
        self.poutput(job.message or "", style=style)

    @cmd2.with_argparser(
        _path_arg_parser(
            "Show a VM's state and, if deployed, its runtime state on the hypervisor.",
            required=True,
        )
    )
    def do_status(self, args: argparse.Namespace) -> None:
        try:
            info = self._service.status(self._resolve(args.path))
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

    @cmd2.with_argparser(_load_arg_parser())
    def do_load(self, args: argparse.Namespace) -> None:
        try:
            document = parse_definition_file(args.file)
        except (OSError, YAMLError, ValidationError) as error:
            self.perror(str(error))
            return
        destination = self._resolve(args.destination)
        try:
            results = self._service.load(document, destination)
        except OperationError as error:  # destination doesn't exist, etc.
            self.perror("; ".join(error.errors))
            return
        for result in results:
            style = "green" if result.ok else "red"
            self.poutput(f"{result.path}  {result.message}", style=style)

    @cmd2.with_argparser(_inspect_arg_parser())
    def do_inspect(self, args: argparse.Namespace) -> None:
        path = self._resolve(args.path)
        try:
            entity = self._service.inspect(path, resolved=not args.local)
        except OperationError as error:
            self.perror("; ".join(error.errors))
            return
        # the simplified Pieza 2 splits rendering by kind; the future annotated
        # mode will share the same dispatch and add colours + provenance
        if isinstance(entity, Descriptor):
            self._render_descriptor(entity)
        else:
            self._render_folder(entity)

    def _render_descriptor(self, d: Descriptor) -> None:
        """Pretty-print a Descriptor with YAML-like labels; skip unset fields."""
        self.poutput(f"{d.path}   (descriptor)")
        # YAML aliases for the user-facing labels (definition fields)
        rows: list[tuple[str, object | None]] = [
            ("description", d.description),
            ("use hypervisor", d.hypervisor),
            ("base_vm", d.base_vm),
            ("use template", d.template),
            ("cpu", d.cpu),
            ("memory_mb", d.memory_mb),
            ("disk_gb", d.disk_gb),
        ]
        for label, value in rows:
            if value is not None:
                self.poutput(f"  {label + ':':18} {value}")
        # runtime info: state is always set; vm_id only when deployed
        self.poutput(f"  {'state:':18} {d.state.value}")
        if d.vm_id is not None:
            self.poutput(f"  {'vm_id:':18} {d.vm_id}")

    def _render_folder(self, f: Folder) -> None:
        """Pretty-print a Folder with YAML-like labels; skip unset fields."""
        self.poutput(f"{_folder_label(f.path)}   (folder)")
        if f.description is not None:
            self.poutput(f"  {'description:':26} {f.description}")
        if f.imports:
            self.poutput(f"  {'import:':26} {', '.join(f.imports)}")
        if f.hypervisors:
            self.poutput("  define hypervisors:")
            for name, hyp in f.hypervisors.items():
                self.poutput(f"    {name}:")
                self.poutput(f"      {'type:':18} {hyp.connector_type}")
                if hyp.description is not None:
                    self.poutput(f"      {'description:':18} {hyp.description}")
        if f.vm_templates:
            self.poutput("  define templates:")
            for name, tpl in f.vm_templates.items():
                self.poutput(f"    {name}:")
                tpl_rows: list[tuple[str, object | None]] = [
                    ("description", tpl.description),
                    ("use hypervisor", tpl.hypervisor),
                    ("base_vm", tpl.base_vm),
                    ("cpu", tpl.cpu),
                    ("memory_mb", tpl.memory_mb),
                    ("disk_gb", tpl.disk_gb),
                ]
                for label, value in tpl_rows:
                    if value is not None:
                        self.poutput(f"      {label + ':':18} {value}")


def main() -> None:
    db_path = os.environ.get("UNIVORCH_DB", "univorch.tinydb.json")
    shell = UnivOrchShell(build_service(TinyDB(db_path)))
    if len(sys.argv) > 1:
        shell.onecmd_plus_hooks(" ".join(sys.argv[1:]))  # bash mode: one command
    else:
        shell.cmdloop()  # interactive REPL
