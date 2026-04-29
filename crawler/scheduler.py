from datetime import datetime, timedelta

from config import FAILED_RETRY_DELAY_MINUTES, MAX_RETRY_COUNT, SUCCESS_CRAWL_INTERVAL_DAYS



def get_success_next_crawl_time(page_type: str, changed: bool) -> datetime:
    now = datetime.now()

    if page_type == "list":
        return now + timedelta(days=SUCCESS_CRAWL_INTERVAL_DAYS["list"])

    if page_type == "org_directory":
        return now + timedelta(days=SUCCESS_CRAWL_INTERVAL_DAYS["org_directory"])

    if page_type == "article":
        if changed:
            return now + timedelta(days=SUCCESS_CRAWL_INTERVAL_DAYS["article_changed"])
        return now + timedelta(days=SUCCESS_CRAWL_INTERVAL_DAYS["article_unchanged"])

    if page_type == "unknown":
        return now + timedelta(days=SUCCESS_CRAWL_INTERVAL_DAYS["unknown"])

    return now + timedelta(days=SUCCESS_CRAWL_INTERVAL_DAYS["default"])


def get_failed_next_crawl_time(retry_count: int) -> datetime:
    now = datetime.now()
    minutes = FAILED_RETRY_DELAY_MINUTES.get(retry_count, FAILED_RETRY_DELAY_MINUTES["default"])
    return now + timedelta(minutes=minutes)
