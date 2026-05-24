"""TinyDB repositories (DEC-030).

One repository per aggregate (folders, descriptors). Each receives the TinyDB
instance and uses its own table. The tree is keyed by materialized path, so a
subtree is a path-prefix query.
"""

from collections.abc import Callable

from tinydb import Query, TinyDB

from univorch.models import Descriptor, Folder


def _in_subtree(prefix: str) -> Callable[[str], bool]:
    """Match a path that is ``prefix`` itself or sits below it (segment-aware).

    ``/lab`` matches ``/lab`` and ``/lab/...`` but not ``/lab2``.
    """
    return lambda path: path == prefix or path.startswith(prefix + "/")


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
        # .test(fn) filters with a custom predicate; a simple == can't express it
        docs = self._table.search(Query().path.test(_in_subtree(prefix)))
        return [Folder.model_validate(doc) for doc in docs]

    def delete(self, path: str) -> None:
        self._table.remove(Query().path == path)


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
        docs = self._table.search(Query().path.test(_in_subtree(prefix)))
        return [Descriptor.model_validate(doc) for doc in docs]

    def delete(self, path: str) -> None:
        self._table.remove(Query().path == path)
