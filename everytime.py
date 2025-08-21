"""Small client to fetch Everytime timetable XML."""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse
import requests


API_URL = "https://api.everytime.kr/find/timetable/table/friend"
DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Host": "api.everytime.kr",
    "Origin": "https://everytime.kr",
    "Referer": "https://everytime.kr/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/93.0.4577.63 Safari/537.36"
    ),
}


class Everytime:
    def __init__(self, path: str) -> None:
        url = urlparse(path)
        if url.netloc == "everytime.kr":
            self.path = url.path.replace("/@", "")
        else:
            self.path = path

    def get_timetable(self, timeout: float = 10.0) -> str:
        """Fetch timetable XML as a string. Raises for HTTP errors."""
        resp = requests.post(
            API_URL,
            data={"identifier": self.path, "friendInfo": "true"},
            headers=DEFAULT_HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.text
