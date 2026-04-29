from __future__ import annotations

import hashlib
import re


def normalize_org_name(name: str) -> str:
    name = re.sub(r"\s+", "", name)
    name = name.replace("（", "(").replace("）", ")")
    return name.strip()


def make_org_id(name: str) -> str:
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()[:12]
    return f"org_{digest}"


def make_doc_id(url: str) -> str:
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:16]
    return f"doc_{digest}"


def make_rel_id(src: str, dst: str, rel_type: str) -> str:
    digest = hashlib.md5(f"{src}|{dst}|{rel_type}".encode("utf-8")).hexdigest()[:16]
    return f"rel_{digest}"