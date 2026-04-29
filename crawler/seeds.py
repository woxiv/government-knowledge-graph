from urllib.parse import urlparse

from config import ALLOWED_BASE_DOMAINS


def normalize_host(host: str) -> str:
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False

    host = normalize_host(parsed.netloc)
    for base_domain in ALLOWED_BASE_DOMAINS:
        if host == base_domain or host.endswith("." + base_domain):
            return True
    return False


def is_probably_useful(url: str) -> bool:
    # 先保守一些，优先留下正文页、栏目页
    blocked_suffixes = (
        ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"
    )
    if url.lower().endswith(blocked_suffixes):
        return False
    return True
