from bs4 import BeautifulSoup


def guess_page_type(url: str, html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    # 机构目录页
    if "政府部门" in text and "乡镇街道" in text:
        return "org_directory"

    # 列表页：链接多，正文弱，通常包含多条标题
    link_count = len(soup.find_all("a"))
    if link_count >= 30 and ("list" in url or "下一页" in text or "上一页" in text):
        return "list"

    # 文章页：有发布时间、来源、正文等特征
    if "发布时间" in text or "发布日期" in text or "来源" in text:
        return "article"

    return "unknown"