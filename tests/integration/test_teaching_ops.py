"""Integration tests for the teaching operations against a real service."""

from __future__ import annotations

from pathlib import Path

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.models import DescriptorState
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.service import OrchestratorService
from univorch.teaching import operations as ops

_SUBJECT_YAML = """\
kind: definition
version: "1"
redes-2026/:
  metadata: { kind: subject, desktop: [workstation, servidor] }
  define hypervisors: { mock01: { type: mock } }
  define templates:
    workstation: { use hypervisor: mock01, base_vm: linux-base }
    servidor:    { use hypervisor: mock01, base_vm: linux-base }
"""

_STUDENTS_YAML = """\
kind: student-list
version: "1"
students:
  - alumno01
  - alumno02
"""


@pytest.fixture
def service() -> OrchestratorService:
    db = TinyDB(storage=MemoryStorage)
    return OrchestratorService(
        FolderRepository(db),
        DescriptorRepository(db),
        JobRepository(db),
        {"mock": MockConnector},
    )


def _write(tmp: Path, name: str, content: str) -> str:
    p = tmp / name
    p.write_text(content)
    return str(p)


def test_load_subject_creates_marked_folder(
    service: OrchestratorService, tmp_path: Path
) -> None:
    f = _write(tmp_path, "subject.yml", _SUBJECT_YAML)
    ops.load_subject(service, f, "/")
    folder = service.inspect("/redes-2026", resolved=False)
    assert folder.metadata["kind"] == "subject"  # type: ignore[union-attr]
    assert folder.metadata["desktop"] == ["workstation", "servidor"]  # type: ignore[union-attr]


def test_load_subject_rejects_non_subject(
    service: OrchestratorService, tmp_path: Path
) -> None:
    bad = _SUBJECT_YAML.replace("kind: subject", "kind: folder")
    f = _write(tmp_path, "bad.yml", bad)
    with pytest.raises(ops.TeachingError):
        ops.load_subject(service, f, "/")
    assert not service.folder_exists("/redes-2026")  # nothing created


def test_load_students_generates_structure(
    service: OrchestratorService, tmp_path: Path
) -> None:
    ops.load_subject(service, _write(tmp_path, "s.yml", _SUBJECT_YAML), "/")
    ops.load_students(
        service, "/redes-2026", _write(tmp_path, "students.yml", _STUDENTS_YAML)
    )
    # two student folders, each with two descriptors
    assert service.folder_exists("/redes-2026/alumno01")
    assert service.folder_exists("/redes-2026/alumno02")
    for student in ("alumno01", "alumno02"):
        for vm in ("workstation", "servidor"):
            d = service.inspect(f"/redes-2026/{student}/{vm}", resolved=False)
            assert d.template == vm  # type: ignore[union-attr]


def test_load_students_then_deploy(
    service: OrchestratorService, tmp_path: Path
) -> None:
    # end-to-end: the generated descriptors resolve their template via import
    ops.load_subject(service, _write(tmp_path, "s.yml", _SUBJECT_YAML), "/")
    ops.load_students(
        service, "/redes-2026", _write(tmp_path, "st.yml", _STUDENTS_YAML)
    )
    service.deploy("/redes-2026/alumno01/workstation")
    d = service.inspect("/redes-2026/alumno01/workstation", resolved=False)
    assert d.state == DescriptorState.DEPLOYED  # type: ignore[union-attr]


def test_load_students_on_non_subject_rejected(
    service: OrchestratorService, tmp_path: Path
) -> None:
    service.load(  # create a plain folder, not a subject
        __import__("univorch.parser", fromlist=["parse_definition"]).parse_definition(
            'kind: definition\nversion: "1"\nplain/: {}\n'
        ),
        "/",
    )
    with pytest.raises(ops.TeachingError):
        ops.load_students(service, "/plain", _write(tmp_path, "st.yml", _STUDENTS_YAML))


def test_load_subject_with_student_list_gives_clear_message(
    service: OrchestratorService, tmp_path: Path
) -> None:
    # the symmetric mistake: passing a student list where a subject is expected
    wrong = _write(tmp_path, "wrong.yml", _STUDENTS_YAML)  # a list, not a subject
    with pytest.raises(ops.TeachingError) as exc:
        ops.load_subject(service, wrong, "/")
    assert "not a subject definition" in "; ".join(exc.value.errors)


def test_load_students_on_root_gives_clear_message(
    service: OrchestratorService, tmp_path: Path
) -> None:
    # the implicit root is not a subject: a clear message, not "not found: /"
    with pytest.raises(ops.TeachingError) as exc:
        ops.load_students(service, "/", _write(tmp_path, "st.yml", _STUDENTS_YAML))
    assert "is not a subject" in "; ".join(exc.value.errors)


def test_load_students_with_subject_file_gives_clear_message(
    service: OrchestratorService, tmp_path: Path
) -> None:
    # passing the subject file where a student list is expected
    ops.load_subject(service, _write(tmp_path, "s.yml", _SUBJECT_YAML), "/")
    wrong = _write(tmp_path, "wrong.yml", _SUBJECT_YAML)  # a subject, not a list
    with pytest.raises(ops.TeachingError) as exc:
        ops.load_students(service, "/redes-2026", wrong)
    assert "not a student list" in "; ".join(exc.value.errors)


def test_save_students_roundtrip(service: OrchestratorService, tmp_path: Path) -> None:
    ops.load_subject(service, _write(tmp_path, "s.yml", _SUBJECT_YAML), "/")
    ops.load_students(
        service, "/redes-2026", _write(tmp_path, "st.yml", _STUDENTS_YAML)
    )
    out = ops.save_students(service, "/redes-2026")
    assert "kind: student-list" in out
    assert "- alumno01" in out
    assert "- alumno02" in out
