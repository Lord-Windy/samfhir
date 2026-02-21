from abc import ABC, abstractmethod
from typing import Any


class CachePort(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 300) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def flush(self) -> None: ...

    @abstractmethod
    async def stats(self) -> dict[str, Any]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
