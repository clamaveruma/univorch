"""Tests for the teaching layer: models, subject validation, generation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from univorch.models import DefinitionDocument
from univorch.teaching.models import StudentList
from univorch.teaching.students import build_student_document
from univorch.teaching.subject import find_subject, subject_desktop, validate_subject


def _subject_doc(
    *,
    kind: str = "subject",
    desktop: list[str] | None = None,
    define: list[str] | None = None,
    imports: list[str] | None = None,
    child_folder: bool = False,
) -> DefinitionDocument:
    """Build a one-folder subject document with the given metadata/templates."""
    desktop = ["workstation", "servidor"] if desktop is None else desktop
    define = ["workstation", "servidor"] if define is None else define
    folder: dict = {
        "metadata": {"kind": kind, "desktop": desktop},
        "define templates": {
            name: {"use hypervisor": "mock01", "base_vm": "linux-base"}
            for name in define
        },
    }
    if imports:
        folder["import"] = imports
    if child_folder:
        folder["group-a/"] = {}
    return DefinitionDocument.model_validate({"redes-2026/": folder})


class TestStudentList:
    def test_minimal(self) -> None:
        sl = StudentList(students=["alumno01", "alumno02"])
        assert sl.students == ["alumno01", "alumno02"]

    def test_duplicates_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StudentList(students=["alumno01", "alumno01"])

    def test_invalid_username_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StudentList(students=["alumno 01"])  # space not a path segment

    def test_email_username_accepted(self) -> None:
        sl = StudentList(students=["juan@uma.es", "ana.lopez@uma.es"])
        assert sl.students == ["juan@uma.es", "ana.lopez@uma.es"]


class TestSubjectValidation:
    def test_valid_subject(self) -> None:
        assert validate_subject(_subject_doc()) == []

    def test_find_subject(self) -> None:
        name, folder = find_subject(_subject_doc())  # type: ignore[misc]
        assert name == "redes-2026"
        assert subject_desktop(folder) == ["workstation", "servidor"]

    def test_missing_kind(self) -> None:
        errors = validate_subject(_subject_doc(kind="folder"))
        assert any("kind: subject" in e for e in errors)

    def test_empty_desktop(self) -> None:
        errors = validate_subject(_subject_doc(desktop=[]))
        assert any("non-empty 'desktop'" in e for e in errors)

    def test_desktop_template_not_defined(self) -> None:
        errors = validate_subject(
            _subject_doc(desktop=["ghost"], define=["workstation"])
        )
        assert any("ghost" in e for e in errors)

    def test_desktop_template_imported_is_ok(self) -> None:
        doc = _subject_doc(desktop=["shared-vm"], define=[], imports=["shared-vm"])
        assert validate_subject(doc) == []

    def test_wildcard_import_accepts_any_desktop(self) -> None:
        doc = _subject_doc(desktop=["anything"], define=[], imports=["*"])
        assert validate_subject(doc) == []

    def test_child_folder_rejected(self) -> None:
        errors = validate_subject(_subject_doc(child_folder=True))
        assert any("child folders" in e for e in errors)

    def test_two_folders_rejected(self) -> None:
        doc = DefinitionDocument.model_validate(
            {"a/": {"metadata": {"kind": "subject"}}, "b/": {}}
        )
        errors = validate_subject(doc)
        assert any("exactly one top-level folder" in e for e in errors)


class TestStudentGeneration:
    def test_one_folder_per_student_with_descriptors(self) -> None:
        doc = build_student_document(
            ["alumno01", "alumno02"], ["workstation", "servidor"]
        )
        assert sorted(doc.folders) == ["alumno01", "alumno02"]
        a1 = doc.folders["alumno01"]
        assert sorted(a1.descriptors) == ["servidor", "workstation"]
        assert a1.descriptors["workstation"].template == "workstation"

    def test_empty_list(self) -> None:
        doc = build_student_document([], ["workstation"])
        assert doc.folders == {}
