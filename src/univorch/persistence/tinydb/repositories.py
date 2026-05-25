"""TinyDB repositories (DEC-030).

One repository per aggregate (folders, descriptors). Each receives the TinyDB
instance and uses its own table. The tree is keyed by materialized path, so a
subtree is a path-prefix query.
"""

from tinydb import Query, TinyDB

from univorch.models import Descriptor, Folder, Job, JobStatus


def _in_subtree(prefix: str, path: str) -> bool:
    """True if ``path`` is ``prefix`` itself or sits below it (segment-aware).

    ``/lab`` matches ``/lab`` and ``/lab/...`` but not ``/lab2``; the root ``/``
    contains everything.
    """
    if prefix == "/":
        return True
    return path == prefix or path.startswith(prefix + "/")


class FolderRepository:
    """Stores folders, keyed by path."""

    def __init__(self, db: TinyDB) -> None:
        self._table = db.table("folders")

    def save(self, folder: Folder) -> None:
        # mode="json" turns enums/dates into JSON-native types TinyDB can store
        data = folder.model_dump(mode="json")
        # Query().path == x builds a TinyDB match condition, not a boolean
        self._table.upsert(data, Query().path == data["path"])

    def get(self, path: str) -> Folder | None:
        doc = self._table.get(Query().path == path)
        return Folder.model_validate(doc) if doc else None

    def exists(self, path: str) -> bool:
        return self._table.contains(Query().path == path)

    def subtree(self, prefix: str) -> list[Folder]:
        # TinyDB has no native prefix query; for the PoC's small data we filter
        # in Python (a server DB like MongoDB would push this into the query)
        return [
            Folder.model_validate(doc)
            for doc in self._table.all()
            if _in_subtree(prefix, doc["path"])
        ]

    def delete(self, path: str) -> None:
        self._table.remove(Query().path == path)


class JobRepository:
    """Stores jobs, keyed by id (a job is not a tree node, so not by path)."""

    def __init__(self, db: TinyDB) -> None:
        self._table = db.table("jobs")

    def save(self, job: Job) -> None:
        data = job.model_dump(mode="json")
        self._table.upsert(data, Query().id == data["id"])

    def get(self, job_id: str) -> Job | None:
        doc = self._table.get(Query().id == job_id)
        return Job.model_validate(doc) if doc else None

    def find_by_target(self, target: str) -> list[Job]:
        docs = self._table.search(Query().target == target)
        return [Job.model_validate(doc) for doc in docs]

    def find_by_status(self, status: JobStatus) -> list[Job]:
        # Full table scan: TinyDB has no indexes. Fine for the PoC's small,
        # retention-capped table; production (MongoDB) would index status and
        # created_at to avoid the scan (DEC-030). The Repository hides this.
        docs = self._table.search(Query().status == status)
        jobs = [Job.model_validate(doc) for doc in docs]
        return sorted(jobs, key=lambda job: job.created_at)  # FIFO by creation


class DescriptorRepository:
    """Stores descriptors, keyed by path."""

    def __init__(self, db: TinyDB) -> None:
        self._table = db.table("descriptors")

    def save(self, descriptor: Descriptor) -> None:
        data = descriptor.model_dump(mode="json")
        self._table.upsert(data, Query().path == data["path"])

    def get(self, path: str) -> Descriptor | None:
        doc = self._table.get(Query().path == path)
        return Descriptor.model_validate(doc) if doc else None

    def exists(self, path: str) -> bool:
        return self._table.contains(Query().path == path)

    def subtree(self, prefix: str) -> list[Descriptor]:
        return [
            Descriptor.model_validate(doc)
            for doc in self._table.all()
            if _in_subtree(prefix, doc["path"])
        ]

    def delete(self, path: str) -> None:
        self._table.remove(Query().path == path)
