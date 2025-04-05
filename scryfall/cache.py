import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from scryfall import IMAGE_FILENAME_FORMAT


class CacheStrategy(ABC):
    @abstractmethod
    def read(self, path: str) -> Any:
        pass

    @abstractmethod
    def write(self, path: str, data: Any) -> None:
        pass


class JsonCacheStrategy(CacheStrategy):
    def read(self, path: str) -> dict:
        with open(path, "r") as f:
            logging.debug(f"[cache] READ {path}")
            return json.load(f)

    def write(self, path: str, data: dict) -> None:
        with open(path, "w") as f:
            logging.debug(f"[cache] CREATE {path}")
            json.dump(data, f)


class BinaryCacheStrategy(CacheStrategy):
    def read(self, path: str) -> bytes:
        with open(path, "rb") as f:
            logging.debug(f"[cache] READ {path}")
            return f.read()

    def write(self, path: str, data: bytes) -> None:
        with open(path, "wb") as f:
            logging.debug(f"[cache] CREATE {path}")
            f.write(data)


class CacheManager:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        self.images_dir = os.path.join(base_dir, "images")
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        for directory in [self.base_dir, self.data_dir, self.images_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def get_card_cache_path(self, name: str, set_code: Optional[str] = None) -> str:
        if set_code:
            filename = f"{name}.{set_code.upper()}.json"
        else:
            filename = f"{name}.json"
        return os.path.join(self.data_dir, filename)

    def get_image_cache_path(
        self, name: str, set_code: str = "", face: str = "front"
    ) -> str:
        set_suffix = f".{set_code.upper()}" if set_code else ""
        filename_format = IMAGE_FILENAME_FORMAT[face].format(set_suffix)
        return os.path.join(self.images_dir, f"{name}{filename_format}")
