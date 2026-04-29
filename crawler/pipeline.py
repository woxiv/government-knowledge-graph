from __future__ import annotations

import os

from dotenv import load_dotenv

from config import MAX_PAGES, SEED_URLS
from crawler.classifier import guess_page_type
from crawler.fetcher import Fetcher
from crawler.parser import parse_page
from crawler.seeds import is_allowed_url, is_probably_useful
from extractor.article_extractor import extract_article
from extractor.org_extractor import extract_org_directory
from storage.postgres import PostgresStorage


class CrawlPipeline:
    def __init__(self, storage: PostgresStorage, fetcher: Fetcher | None = None):
        self.storage = storage
        self.fetcher = fetcher or Fetcher()

    def run_url(self, url: str) -> tuple[list[str], bool, str]:
        html = self.fetcher.get(url)
        if not html:
            return [], False, "unknown"

        page_type = guess_page_type(url, html)
        doc = parse_page(url, html, page_type)
        doc_id, changed = self.storage.upsert_document(doc)

        # list 页只负责发现链接
        if page_type == "list":
            return doc.discovered_urls, changed, page_type

        # 内容不变则跳过重抽
        if not changed:
            return doc.discovered_urls, changed, page_type

        if page_type == "org_directory":
            result = extract_org_directory(doc_id, html)
            self.storage.upsert_extraction_result(result)
            return doc.discovered_urls, changed, page_type

        if page_type == "article":
            result = extract_article(
                doc_id=doc_id,
                title=doc.title or "",
                content=doc.content or "",
                source=doc.source,
            )
            self.storage.upsert_extraction_result(result)
            return doc.discovered_urls, changed, page_type

        return doc.discovered_urls, changed, page_type


def run_pipeline() -> None:
    load_dotenv()

    dsn = os.getenv("DATABASE_DSN")
    if not dsn:
        raise RuntimeError("Missing DATABASE_DSN environment variable")

    storage = PostgresStorage(dsn)
    pipeline = CrawlPipeline(storage=storage)
    storage.init_frontier(SEED_URLS)

    processed = 0
    while processed < MAX_PAGES:
        task = storage.get_next_frontier_url()
        if not task:
            break

        frontier_id = task["id"]
        url = task["url"]
        depth = int(task["depth"])

        if not is_allowed_url(url) or not is_probably_useful(url):
            storage.mark_frontier_skipped(frontier_id, "blocked by allow/useful rules")
            continue

        processed += 1
        print(f"[crawl] {processed}/{MAX_PAGES} {url}")

        try:
            discovered_urls, changed, page_type = pipeline.run_url(url)
            for link in discovered_urls:
                if is_allowed_url(link) and is_probably_useful(link):
                    storage.upsert_frontier_url(
                        url=link,
                        discovered_from=url,
                        depth=depth + 1,
                        priority=100 + depth,
                    )
            storage.mark_frontier_success(frontier_id, page_type=page_type, changed=changed)
        except Exception as exc:
            storage.mark_frontier_failed(frontier_id, f"{type(exc).__name__}: {exc}")
            print(f"[warn] pipeline failed: {url} ({type(exc).__name__}: {exc})")

    print(f"done: processed={processed}")
