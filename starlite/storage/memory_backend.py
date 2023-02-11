from __future__ import annotations

from datetime import datetime, timedelta

from anyio import Lock

from .base import StorageBackend, StorageObject


class MemoryStorageBackend(StorageBackend):
    __slots__ = ("_store", "_lock")

    def __init__(self) -> None:
        self._store: dict[str, StorageObject] = {}
        self._lock = Lock()

    async def get(self, key: str, renew: int | None = None) -> bytes | None:
        async with self._lock:
            storage_obj = self._store.get(key)

            if storage_obj:
                if storage_obj.expired:
                    self._store.pop(key)
                    return None

                if renew and storage_obj.expires:
                    storage_obj.expires = datetime.now() + timedelta(seconds=renew)

                return storage_obj.data

        return None

    async def set(self, key: str, value: bytes, expires: int | None = None) -> None:
        expiration: datetime | None = None
        if expires:
            expiration = datetime.now() + timedelta(seconds=expires)

        async with self._lock:
            self._store[key] = StorageObject(data=value, expires=expiration)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def delete_all(self) -> None:
        async with self._lock:
            self._store.clear()
