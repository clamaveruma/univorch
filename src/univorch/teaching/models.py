"""Pydantic models specific to the teaching layer.

- ``StudentList``: the standalone YAML a professor uploads with the
  enrolled usernames (DEC-039).
- Subject documents are ordinary core ``DefinitionDocument``s; the
  teaching layer reads ``kind``/``desktop`` from the folder's opaque
  ``metadata`` (DEC-038) rather than introducing a new core model.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from univorch.models import is_valid_segment

SUBJECT_KIND = "subject"


class StudentList(BaseModel):
    """A list of enrolled students. Minimal for the PoC: usernames only."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["student-list"] = "student-list"
    version: str = "1"
    students: list[str]

    @field_validator("students")
    @classmethod
    def _no_duplicates(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        dups: list[str] = []
        for name in value:
            if name in seen:
                dups.append(name)
            seen.add(name)
        if dups:
            raise ValueError(f"duplicate students in the list: {sorted(set(dups))}")
        return value

    @field_validator("students")
    @classmethod
    def _segment_names(cls, value: list[str]) -> list[str]:
        # usernames become folder names, so they must be valid tree segments
        # (single source of truth: the core's is_valid_segment)
        bad = [n for n in value if not is_valid_segment(n)]
        if bad:
            raise ValueError(f"invalid student usernames (not a path segment): {bad}")
        return value
