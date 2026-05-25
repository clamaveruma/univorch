"""Tests for the Jobs engine."""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.jobs.commands import Command
from univorch.jobs.engine import JobEngine
from univorch.models import JobStatus, OperationType
from univorch.persistence.tinydb.repositories import JobRepository


class _OkCommand(Command):
    operation_type = OperationType.DEPLOY

    def __init__(self, target: str = "/lab/vm", message: str = "done") -> None:
        self.target = target
        self._message = message

    def validate(self) -> list[str]:
        return []

    def execute(self) -> str:
        return self._message


class _FailCommand(Command):
    operation_type = OperationType.START

    def __init__(self, target: str = "/lab/vm") -> None:
        self.target = target

    def validate(self) -> list[str]:
        return []

    def execute(self) -> str:
        raise ValueError("boom")


@pytest.fixture
def jobs() -> JobRepository:
    return JobRepository(TinyDB(storage=MemoryStorage))


def test_successful_command_records_completed_job(jobs: JobRepository) -> None:
    job = JobEngine(jobs).run(_OkCommand(message="deployed"))
    assert job.status == JobStatus.COMPLETED
    assert job.message == "deployed"
    assert job.operation_type == OperationType.DEPLOY
    assert job.target == "/lab/vm"
    assert job.finished_at is not None
    assert jobs.get(job.id) is not None  # persisted


def test_failing_command_records_failed_job(jobs: JobRepository) -> None:
    job = JobEngine(jobs).run(_FailCommand())
    assert job.status == JobStatus.FAILED
    assert job.message is not None and "boom" in job.message
    assert job.finished_at is not None


def test_job_is_persisted_running_during_execute(jobs: JobRepository) -> None:
    seen: dict[str, int] = {}

    class _InspectCommand(Command):
        operation_type = OperationType.DEPLOY
        target = "/lab/vm"

        def validate(self) -> list[str]:
            return []

        def execute(self) -> str:
            # the job already exists and is RUNNING while we execute (DEC-028)
            seen["running"] = len(jobs.find_by_status(JobStatus.RUNNING))
            return "ok"

    JobEngine(jobs).run(_InspectCommand())
    assert seen["running"] == 1
