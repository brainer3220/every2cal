"""Client for fetching public timetables from Everytime."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class EverytimeError(RuntimeError):
    """Raised when the Everytime API cannot be reached or returns an error."""


@dataclass(frozen=True)
class _RequestConfig:
    url: str = "https://api.everytime.kr/find/timetable/table/friend"
    timeout: int = 10
    headers: tuple[tuple[str, str], ...] = (
        ("Accept", "*/*"),
        ("Connection", "keep-alive"),
        ("Pragma", "no-cache"),
        ("Cache-Control", "no-cache"),
        ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
        ("Host", "api.everytime.kr"),
        ("Origin", "https://everytime.kr"),
        ("Referer", "https://everytime.kr/"),
        (
            "User-Agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
        ),
    )

    def as_dict(self) -> dict[str, str]:
        return dict(self.headers)


class Everytime:
    """Small wrapper around the Everytime timetable API."""

    _config = _RequestConfig()

    def __init__(self, identifier: str, session: Optional[requests.Session] = None):
        if not identifier:
            raise ValueError("An Everytime identifier or URL must be provided.")

        self.identifier = self._normalise_identifier(identifier)
        self._session = session or requests.Session()

    @staticmethod
    def _normalise_identifier(identifier: str) -> str:
        parsed = urlparse(identifier)
        if parsed.scheme and parsed.netloc:
            candidate = parsed.path
        else:
            candidate = identifier

        candidate = candidate.replace("/@", "").lstrip("/@")
        candidate = candidate.strip()
        if not candidate:
            raise ValueError("Could not determine an Everytime identifier from the supplied value.")
        return candidate

    def get_timetable(self) -> str:
        payload = {"identifier": self.identifier, "friendInfo": "true"}
        logger.debug("Requesting timetable for identifier '%s'", self.identifier)

        try:
            response = self._session.post(
                self._config.url,
                data=payload,
                headers=self._config.as_dict(),
                timeout=self._config.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EverytimeError("Failed to download timetable from Everytime.") from exc

        text = response.text.strip()
        if not text:
            raise EverytimeError("Received an empty timetable response from Everytime.")

        return text
