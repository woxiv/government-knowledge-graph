import re
from datetime import date
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from models import ParsedDocument


DATE_PATTERN = re.compile(r"(20\d{2})[./\-年](\d{1,2})[./\-月](\d{1,2})")
PUBLISH_LINE_PATTERN = re.compile(
    r"(?:发布时间|发布日期|发文日期|成文日期|公开日期)\s*[:：]?\s*(.+)"
)

PUBLISH_META_NAMES = ("pubdate", "publishdate", "publish_time", "publishdatecn")
SOURCE_META_NAMES = ("contentsource", "source", "article_source", "sourceorg")


def _to_iso_date(year: str, month: str, day: str) -> str | None:
    try:
        value = date(int(year), int(month), int(day))
    except ValueError:
        return None
    return value.isoformat()


def _extract_date_from_text(value: str | None) -> str | None:
    if not value:
        return None
    match = DATE_PATTERN.search(value)
    if not match:
        return None
    return _to_iso_date(*match.groups())


def _extract_title(soup: BeautifulSoup) -> str | None:
    if not soup.title:
        return None
    # Normalize line breaks and repeated spaces in <title>.
    return re.sub(r"\s+", " ", soup.title.get_text()).strip()


def _extract_publish_time(soup: BeautifulSoup, text: str) -> str | None:
    # Publish time is extracted only from top meta fields by design.
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").strip().lower()
        if name in PUBLISH_META_NAMES:
            parsed = _extract_date_from_text(meta.get("content"))
            if parsed:
                return parsed

    return None


def _extract_source(soup: BeautifulSoup) -> str | None:
    # Source is extracted only from top meta fields by design.
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").strip().lower()
        if name in SOURCE_META_NAMES:
            value = (meta.get("content") or "").strip()
            return value or None
    return None


def extract_discovered_urls(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()

    for a in soup.find_all("a"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith("javascript:"):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if full_url in seen:
            continue
        seen.add(full_url)
        urls.append(full_url)

    return urls


def parse_page(url: str, html: str, page_type: str) -> ParsedDocument:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    publish_time = _extract_publish_time(soup, text)
    source = _extract_source(soup)

    if page_type == "article":
        return parse_article_page(url=url, html=html, publish_time=publish_time, source=source)

    if page_type == "list":
        return parse_list_page(url, html)

    if page_type == "org_directory":
        return parse_org_directory_page(url, html)

    return ParsedDocument(
        url=url,
        page_type="unknown",
        title=_extract_title(soup),
        publish_time=publish_time,
        source=source,
        raw_html=html,
        content=text,
        discovered_urls=extract_discovered_urls(url, html),
    )


def parse_article_page(
    url: str,
    html: str,
    publish_time: str | None = None,
    source: str | None = None,
) -> ParsedDocument:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    return ParsedDocument(
        url=url,
        page_type="article",
        title=_extract_title(soup),
        publish_time=publish_time,
        source=source,
        content=text,
        raw_html=html,
        discovered_urls=extract_discovered_urls(url, html),
    )


def parse_list_page(url: str, html: str) -> ParsedDocument:
    soup = BeautifulSoup(html, "html.parser")
    discovered_urls = extract_discovered_urls(url, html)

    links_preview: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a"):
        title = a.get_text(strip=True)
        href = (a.get("href") or "").strip()
        if not title or not href:
            continue
        full_url = urljoin(url, href)
        if full_url not in discovered_urls or full_url in seen:
            continue
        seen.add(full_url)
        links_preview.append(f"{title}\t{full_url}")

    return ParsedDocument(
        url=url,
        page_type="list",
        title=_extract_title(soup),
        content="\n".join(links_preview),
        raw_html=html,
        discovered_urls=discovered_urls,
    )


def parse_org_directory_page(url: str, html: str) -> ParsedDocument:
    soup = BeautifulSoup(html, "html.parser")

    return ParsedDocument(
        url=url,
        page_type="org_directory",
        title=_extract_title(soup) or "机构目录页",
        content=soup.get_text("\n", strip=True),
        raw_html=html,
        discovered_urls=extract_discovered_urls(url, html),
    )
