-- =========================
-- 1. crawl_frontier：爬虫调度队列
-- =========================

CREATE TABLE IF NOT EXISTS crawl_frontier (
    id VARCHAR(64) PRIMARY KEY,

    -- 原始 URL
    url TEXT NOT NULL,

    -- 规范化 URL，用于去重
    normalized_url TEXT NOT NULL UNIQUE,

    -- 域名，方便后续按站点统计
    domain TEXT NOT NULL,

    -- URL 状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending: 等待爬取
    -- success: 上次爬取成功
    -- failed: 上次爬取失败，可重试
    -- skipped: 被规则跳过
    -- dead: 多次失败后放弃

    -- URL 来源
    discovered_from TEXT,

    -- 爬取深度
    depth INTEGER NOT NULL DEFAULT 0,

    -- 优先级，数字越小越优先
    priority INTEGER NOT NULL DEFAULT 100,

    -- 下一次应该爬取的时间
    next_crawl_time TIMESTAMP NOT NULL DEFAULT NOW(),

    -- 统计信息
    fetch_count INTEGER NOT NULL DEFAULT 0,
    fail_count INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,

    -- 最近一次错误
    last_error TEXT,

    -- 最近一次尝试爬取时间，不管成功失败
    last_crawl_time TIMESTAMP,

    -- 最近一次成功爬取时间
    last_success_time TIMESTAMP,

    -- 最近一次页面内容变化时间
    last_change_time TIMESTAMP,

    -- 记录创建和更新时间
    created_time TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_time TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_crawl_frontier_status
    CHECK (status IN ('pending', 'success', 'failed', 'skipped', 'dead'))
);


-- =========================
-- 2. documents：存储所有抓取页面
-- =========================

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(64) PRIMARY KEY,

    -- 页面基础信息
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    page_type VARCHAR(50),             -- article / list / org_directory / unknown
    publish_time DATE,
    source TEXT,

    -- 页面内容
    content TEXT,                      -- 清洗后的正文或页面文本
    raw_html TEXT,                     -- 原始 HTML

    -- 扩链结果：列表页、机构目录页中发现的新链接
    discovered_urls JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- 去重和更新判断
    content_hash VARCHAR(64),

    -- 时间信息
    crawl_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);


-- =========================
-- 3. extraction_results：存实体关系抽取结果
-- =========================

CREATE TABLE IF NOT EXISTS extraction_results (
    id SERIAL PRIMARY KEY,

    -- 对应 documents.id
    doc_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- 抽取器信息，方便以后升级算法
    extractor_name TEXT NOT NULL,
    extractor_version TEXT NOT NULL,

    -- 抽取结果
    entities JSONB NOT NULL DEFAULT '[]'::jsonb,
    relations JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- 时间信息
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 同一篇文档、同一个抽取器、同一个版本，只保留一份结果
    UNIQUE (doc_id, extractor_name, extractor_version)
);
