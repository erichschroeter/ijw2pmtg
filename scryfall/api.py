import logging
import requests
import os
import json
import time
from dataclasses import dataclass

from scryfall.cache import BinaryCacheStrategy, CacheManager, JsonCacheStrategy
from scryfall import IMAGE_FILENAME_FORMAT


def sanitize_card_name(name: str) -> str:
    """Convert a card name into a safe filename."""
    # Define character replacements for invalid filename characters
    replacements = {
        "<": "__LT__",
        ">": "__GT__",
        ":": "__COLON__",
        '"': "__QUOTE__",
        "/": "__SLASH__",
        "\\": "__BSLASH__",
        "|": "__PIPE__",
        "?": "__QUEST__",
        "*": "__STAR__",
    }

    # Replace each special character with its safe sequence
    sanitized = name
    for char, replacement in replacements.items():
        sanitized = sanitized.replace(char, replacement)

    return sanitized


def unsanitize_card_name(filename: str) -> str:
    """Convert a sanitized filename back to the original card name."""
    # Restore special sequences
    replacements = {
        "__LT__": "<",
        "__GT__": ">",
        "__COLON__": ":",
        "__QUOTE__": '"',
        "__SLASH__": "/",
        "__BSLASH__": "\\",
        "__PIPE__": "|",
        "__QUEST__": "?",
        "__STAR__": "*",
    }

    unsanitized = filename
    for replacement, char in replacements.items():
        unsanitized = unsanitized.replace(replacement, char)
    return unsanitized


@dataclass
class Card:
    name: str
    uuid: str = None
    block: str = None
    set_name: str = None
    collector_number: str = None
    is_double_faced: bool = False
    quantity: int = 1

    @classmethod
    def from_json(cls, data: dict) -> "Card":
        is_double_faced = "card_faces" in data and len(data["card_faces"]) > 1
        return cls(
            name=data["name"],
            uuid=data["id"] if "id" in data else None,
            block=data["set"] if "set" in data else None,
            set_name=data["set_name"] if "set_name" in data else None,
            collector_number=(
                data["collector_number"] if "collector_number" in data else None
            ),
            is_double_faced=is_double_faced,
        )


class RateLimiter:
    def __init__(self, requests_per_burst=4, burst_delay=2.0, request_delay=0.1):
        self.requests_per_burst = requests_per_burst
        self.burst_delay = burst_delay
        self.request_delay = request_delay
        self.request_count = 0

    def throttle(self):
        """Throttle API requests according to rate limits"""
        self.request_count += 1
        time.sleep(self.request_delay)  # Base delay between requests

        if self.request_count >= self.requests_per_burst:
            time.sleep(self.burst_delay)  # Additional delay after burst
            self.request_count = 0


class Scryfall:
    def __init__(self, server_url="https://api.scryfall.com", cache_dir="cache"):
        self.server_url = server_url
        self.cache_manager = CacheManager(cache_dir)
        self.json_cache = JsonCacheStrategy()
        self.binary_cache = BinaryCacheStrategy()
        self._rate_limiter = RateLimiter()

    def cards_named(self, card_name: str, **kwargs) -> Card:
        sanitized_name = sanitize_card_name(card_name)
        set_code = kwargs.get("set", "")
        set_code = (
            set_code.upper() if set_code else ""
        )  # Handle None value and normalize to uppercase

        # Try both with and without set code to handle existing cached files
        cache_paths = [
            self.cache_manager.get_card_cache_path(sanitized_name),
            (
                self.cache_manager.get_card_cache_path(sanitized_name, set_code)
                if set_code
                else None
            ),
        ]

        # Check all possible cache paths
        for cache_path in cache_paths:
            if cache_path and os.path.exists(cache_path):
                card_data = self.json_cache.read(cache_path)
                # Verify the cached card matches the requested set if specified
                if not set_code or card_data.get("set", "").upper() == set_code:
                    return Card.from_json(card_data)

        response = self._endpoint_get("cards/named", fuzzy=card_name, **kwargs)
        card_json = response.json()
        card = Card.from_json(card_json)

        # Always use the card's actual block/set for caching
        cache_path = self.cache_manager.get_card_cache_path(
            sanitize_card_name(card.name), card.block.upper() if card.block else None
        )
        self.json_cache.write(cache_path, card_json)
        return card

    def cards_image(
        self,
        card: Card,
        format: str = "image",
        version: str = "png",
        face: str = None,
        **kwargs,
    ) -> bytes:
        sanitized_name = sanitize_card_name(card.name)
        # Use card's block if no set specified in kwargs
        set_code = kwargs.get("set", card.block or "").upper()
        cache_path = self.cache_manager.get_image_cache_path(
            sanitized_name, set_code, face or "front"
        )

        if os.path.exists(cache_path):
            return self.binary_cache.read(cache_path)

        if face:
            kwargs["face"] = face

        response = self._endpoint_get(
            f"cards/{card.uuid}", format=format, version=version, **kwargs
        )

        if not response.headers.get("content-type", "").startswith("image/"):
            raise ValueError(
                f"Expected image response, got {response.headers.get('content-type')}"
            )

        self.binary_cache.write(cache_path, response.content)
        return response.content

    def cards_search(self, query, format="json") -> list[Card]:
        response = self._endpoint_get(f"cards/search", format=format, q=query)
        if response.ok:
            data = response.json()
            return [Card.from_json(card_data) for card_data in data["data"]]
        return []

    def _endpoint_get_url(self, endpoint, **kwargs):
        req = requests.Request(
            "GET", f"{self.server_url}/{endpoint}", params=kwargs
        ).prepare()
        return req.url

    def _endpoint_get(self, endpoint, **kwargs):
        url = self._endpoint_get_url(endpoint, **kwargs)
        self._rate_limiter.throttle()
        response = requests.get(url)
        # logging.debug(f"RESPONSE {url} ->\n{response}")
        response.raise_for_status()
        return response
