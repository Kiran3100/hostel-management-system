"""Local file storage provider."""

import os
import aiofiles
from typing import BinaryIO

from app.config import settings
from app.adapters.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Local file system storage provider."""

    def __init__(self):
        self.base_path = settings.storage_path
        os.makedirs(self.base_path, exist_ok=True)

    def _get_full_path(self, path: str) -> str:
        """Get full file system path."""
        return os.path.join(self.base_path, path.lstrip("/"))

    async def upload(self, file: BinaryIO, path: str) -> str:
        """Upload file to local storage."""
        full_path = self._get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            content = file.read()
            await f.write(content)

        return path

    async def download(self, path: str) -> bytes:
        """Download file from local storage."""
        full_path = self._get_full_path(path)

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        """Delete file from local storage."""
        full_path = self._get_full_path(path)

        try:
            os.remove(full_path)
            return True
        except FileNotFoundError:
            return False

    async def get_url(self, path: str) -> str:
        """Get URL for local file."""
        # In production, this would be served by Nginx or CDN
        return f"/storage/{path}"