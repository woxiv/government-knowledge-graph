from __future__ import annotations

import time
from typing import Optional
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import REQUEST_TIMEOUT, USER_AGENT, CRAWL_DELAY_SECONDS


class Fetcher:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT
        })

    @retry(
        reraise=True,
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=8),
    )
    def get(self, url: str) -> Optional[str]:
        time.sleep(CRAWL_DELAY_SECONDS)
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        if "text/html" not in resp.headers.get("Content-Type", ""):
            return None
        return resp.text
