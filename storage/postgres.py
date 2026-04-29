import json
import psycopg
from dataclasses import asdict
from urllib.parse import urlparse

from crawler.scheduler import (
    MAX_RETRY_COUNT,
    get_failed_next_crawl_time,
    get_success_next_crawl_time,
)
from models import ParsedDocument, ExtractionResult
from utils.hash import md5_text
from utils.url import normalize_url


class PostgresStorage:

    def __init__(self, dsn: str):
        self.dsn = dsn

    def get_conn(self):
        return psycopg.connect(self.dsn)

    # Frontier: init / enqueue
    def init_frontier(self, seed_urls: list[str]) -> None:
        for url in seed_urls:
            self.upsert_frontier_url(url=url, discovered_from=None, depth=0, priority=10)

    def upsert_frontier_url(
        self,
        url: str,
        discovered_from: str | None,
        depth: int,
        priority: int = 100,
    ) -> None:
        normalized = normalize_url(url)
        frontier_id = md5_text(normalized)
        domain = urlparse(normalized).netloc

        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO crawl_frontier (
                        id, url, normalized_url, domain, status,
                        discovered_from, depth, priority, next_crawl_time,
                        created_time, updated_time
                    )
                    VALUES (
                        %s, %s, %s, %s, 'pending',
                        %s, %s, %s, NOW(),
                        NOW(), NOW()
                    )
                    ON CONFLICT (normalized_url) DO UPDATE SET
                        url = EXCLUDED.url,
                        priority = LEAST(crawl_frontier.priority, EXCLUDED.priority),
                        depth = LEAST(crawl_frontier.depth, EXCLUDED.depth),
                        updated_time = NOW()
                    """,
                    (
                        frontier_id,
                        url,
                        normalized,
                        domain,
                        discovered_from,
                        depth,
                        priority,
                    ),
                )

    # Frontier: scheduler select
    def get_next_frontier_url(self) -> dict | None:
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, url, depth
                    FROM crawl_frontier
                    WHERE status IN ('pending', 'success', 'failed')
                      AND next_crawl_time <= NOW()
                    ORDER BY priority ASC, next_crawl_time ASC, created_time ASC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {"id": row[0], "url": row[1], "depth": row[2]}

    # Frontier: status update
    def mark_frontier_success(self, frontier_id: str, page_type: str, changed: bool) -> None:
        next_crawl_time = get_success_next_crawl_time(page_type=page_type, changed=changed)
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE crawl_frontier
                    SET status = 'success',
                        fetch_count = fetch_count + 1,
                        last_error = NULL,
                        last_crawl_time = NOW(),
                        last_success_time = NOW(),
                        last_change_time = CASE WHEN %s THEN NOW() ELSE last_change_time END,
                        next_crawl_time = %s,
                        updated_time = NOW()
                    WHERE id = %s
                    """,
                    (changed, next_crawl_time, frontier_id),
                )

    def mark_frontier_failed(self, frontier_id: str, error: str) -> None:
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT retry_count
                    FROM crawl_frontier
                    WHERE id = %s
                    """,
                    (frontier_id,),
                )
                row = cur.fetchone()
                current_retry_count = int(row[0]) if row else 0

        next_crawl_time = get_failed_next_crawl_time(current_retry_count)

        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE crawl_frontier
                    SET fetch_count = fetch_count + 1,
                        fail_count = fail_count + 1,
                        retry_count = retry_count + 1,
                        last_error = %s,
                        last_crawl_time = NOW(),
                        status = CASE WHEN retry_count + 1 >= %s THEN 'dead' ELSE 'failed' END,
                        next_crawl_time = %s,
                        updated_time = NOW()
                    WHERE id = %s
                    """,
                    (error[:2000], MAX_RETRY_COUNT, next_crawl_time, frontier_id),
                )

    def mark_frontier_skipped(self, frontier_id: str, reason: str) -> None:
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE crawl_frontier
                    SET status = 'skipped',
                        fetch_count = fetch_count + 1,
                        last_error = %s,
                        last_crawl_time = NOW(),
                        next_crawl_time = NOW() + INTERVAL '30 days',
                        updated_time = NOW()
                    WHERE id = %s
                    """,
                    (reason[:500], frontier_id),
                )

    # Document flow
    def upsert_document(self, doc: ParsedDocument) -> tuple[str, bool]:
        """
        杩斿洖锛?
        doc_id: 鏂囨。ID
        changed: 鍐呭鏄惁鍙樺寲
        """
        doc_id = md5_text(doc.url)
        discovered_urls_json = json.dumps(doc.discovered_urls, ensure_ascii=False, sort_keys=True)
        content_hash = md5_text((doc.title or "") + (doc.content or "") + discovered_urls_json)

        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT content_hash
                    FROM documents
                    WHERE id = %s
                    """,
                    (doc_id,)
                )
                row = cur.fetchone()

                old_hash = row[0] if row else None
                changed = old_hash != content_hash

                cur.execute(
                    """
                    INSERT INTO documents (
                        id, url, title, page_type, publish_time,
                        source, content, raw_html, discovered_urls, content_hash,
                        crawl_time, update_time
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s::jsonb, %s,
                        NOW(), NOW()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        page_type = EXCLUDED.page_type,
                        publish_time = EXCLUDED.publish_time,
                        source = EXCLUDED.source,
                        content = EXCLUDED.content,
                        raw_html = EXCLUDED.raw_html,
                        discovered_urls = EXCLUDED.discovered_urls,
                        content_hash = EXCLUDED.content_hash,
                        update_time = NOW()
                    """,
                    (
                        doc_id,
                        doc.url,
                        doc.title,
                        doc.page_type,
                        doc.publish_time,
                        doc.source,
                        doc.content,
                        doc.raw_html,
                        discovered_urls_json,
                        content_hash,
                    )
                )

        return doc_id, changed

    # Extraction flow
    def upsert_extraction_result(self, result: ExtractionResult) -> None:
        entities = [asdict(entity) for entity in result.entities]
        relations = [asdict(relation) for relation in result.relations]

        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO extraction_results (
                        doc_id, extractor_name, extractor_version,
                        entities, relations, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, NOW(), NOW())
                    ON CONFLICT (doc_id, extractor_name, extractor_version)
                    DO UPDATE SET
                        entities = EXCLUDED.entities,
                        relations = EXCLUDED.relations,
                        updated_at = NOW()
                    """,
                    (
                        result.doc_id,
                        result.extractor_name,
                        result.extractor_version,
                        json.dumps(entities, ensure_ascii=False),
                        json.dumps(relations, ensure_ascii=False),
                    )
                )

    def get_extraction_results(self):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT doc_id, entities, relations
                    FROM extraction_results
                    """
                )
                return cur.fetchall()
