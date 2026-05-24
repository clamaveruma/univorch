"""Tests for the TinyDB repositories."""

from datetime import UTC, datetime

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.models import (
    Descriptor,
    DescriptorState,
    Folder,
    Job,
    JobStatus,
    Operation,
)
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)


@pytest.fixture
def db() -> TinyDB:
    return TinyDB(storage=MemoryStorage)


class TestFolderRepository:
    def test_save_and_get(self, db: TinyDB) -> None:
        repo = FolderRepository(db)
        repo.save(Folder(path="/lab", description="Lab"))
        got = repo.get("/lab")
        assert got is not None
        assert got.path == "/lab"
        assert got.description == "Lab"

    def test_get_absent_returns_none(self, db: TinyDB) -> None:
        assert FolderRepository(db).get("/nope") is None

    def test_save_is_upsert(self, db: TinyDB) -> None:
        repo = FolderRepository(db)
        repo.save(Folder(path="/lab", description="v1"))
        repo.save(Folder(path="/lab", description="v2"))
        got = repo.get("/lab")
        assert got is not None and got.description == "v2"
        assert len(repo.subtree("/lab")) == 1

    def test_exists(self, db: TinyDB) -> None:
        repo = FolderRepository(db)
        assert not repo.exists("/lab")
        repo.save(Folder(path="/lab"))
        assert repo.exists("/lab")

    def test_delete(self, db: TinyDB) -> None:
        repo = FolderRepository(db)
        repo.save(Folder(path="/lab"))
        repo.delete("/lab")
        assert not repo.exists("/lab")


class TestSubtree:
    def test_returns_subtree_on_segment_boundary(self, db: TinyDB) -> None:
        repo = FolderRepository(db)
        for p in ["/lab", "/lab/networks", "/lab2"]:
            repo.save(Folder(path=p))
        paths = {f.path for f in repo.subtree("/lab")}
        assert paths == {"/lab", "/lab/networks"}  # /lab2 excluded


class TestDescriptorRepository:
    def test_round_trip_with_state(self, db: TinyDB) -> None:
        repo = DescriptorRepository(db)
        repo.save(Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base"))
        got = repo.get("/lab/vm")
        assert got is not None
        assert got.state == DescriptorState.PROVISIONED
        assert got.hypervisor == "mock"

    def test_tables_are_isolated(self, db: TinyDB) -> None:
        FolderRepository(db).save(Folder(path="/lab"))
        assert DescriptorRepository(db).get("/lab") is None

    def test_exists_subtree_and_delete(self, db: TinyDB) -> None:
        repo = DescriptorRepository(db)
        d = Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
        repo.save(d)
        assert repo.exists("/lab/vm")
        assert [x.path for x in repo.subtree("/lab")] == ["/lab/vm"]
        repo.delete("/lab/vm")
        assert not repo.exists("/lab/vm")


class TestJobRepository:
    def test_save_and_get(self, db: TinyDB) -> None:
        repo = JobRepository(db)
        job = Job(operation=Operation.DEPLOY, target="/lab/vm")
        repo.save(job)
        got = repo.get(job.id)
        assert got is not None
        assert got.id == job.id
        assert got.operation == Operation.DEPLOY
        assert got.status == JobStatus.PENDING

    def test_get_absent_returns_none(self, db: TinyDB) -> None:
        assert JobRepository(db).get("nope") is None

    def test_save_is_upsert(self, db: TinyDB) -> None:
        repo = JobRepository(db)
        job = Job(operation=Operation.DEPLOY, target="/lab/vm")
        repo.save(job)
        job.status = JobStatus.COMPLETED
        repo.save(job)
        got = repo.get(job.id)
        assert got is not None and got.status == JobStatus.COMPLETED
        assert len(repo.find_by_target("/lab/vm")) == 1  # not duplicated

    def test_find_by_target(self, db: TinyDB) -> None:
        repo = JobRepository(db)
        repo.save(Job(operation=Operation.DEPLOY, target="/lab/vm"))
        repo.save(Job(operation=Operation.START, target="/lab/vm"))
        repo.save(Job(operation=Operation.DEPLOY, target="/lab/other"))
        assert len(repo.find_by_target("/lab/vm")) == 2

    def test_find_by_status_filters_and_orders(self, db: TinyDB) -> None:
        repo = JobRepository(db)
        # saved out of order to prove sorting by created_at, not insertion order
        repo.save(
            Job(
                operation=Operation.DEPLOY,
                target="/b",
                created_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
        repo.save(
            Job(
                operation=Operation.DEPLOY,
                target="/a",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        repo.save(
            Job(operation=Operation.DEPLOY, target="/done", status=JobStatus.COMPLETED)
        )
        pending = repo.find_by_status(JobStatus.PENDING)
        assert [j.target for j in pending] == ["/a", "/b"]  # filtered + FIFO
