"""Storage provider base interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageProvider(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    async def upload(self, file: BinaryIO, path: str) -> str:
        """Upload file and return URL."""
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """Download file."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file."""
        pass

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Get public URL for file."""
        pass