ALLOWED_BASE_DOMAINS = {
    # 大同市主站及其子域名
    "dt.gov.cn",

    # 大同市县区政府网站
    "pingcheng.gov.cn",
    "yungang.gov.cn",
    "xr.gov.cn",
    "yunzhou.gov.cn",
    "dtyg.gov.cn",
    "dttz.gov.cn",
    "sx-guangling.gov.cn",
    "lingqiu.gov.cn",
    "hunyuan.gov.cn",
    "zuoyun.gov.cn",
}

SEED_URLS = [
    # 大同市人民政府主站
    "https://www.dt.gov.cn/",

    # 市级部门 / 重点站点
    "https://fgw.dt.gov.cn/",       # 大同市发展和改革委员会
    "https://yjj.dt.gov.cn/",       # 大同市应急管理局
    "https://zrzy.dt.gov.cn/",      # 大同市规划和自然资源局
    "https://sthjj.dt.gov.cn/",     # 大同市生态环境局
    "https://gaj.dt.gov.cn/",       # 大同市公安局
    "https://ggzyjy.dt.gov.cn/",    # 大同市公共资源交易
    "https://kfq.dt.gov.cn/",       # 大同经济技术开发区
    "https://credit.dt.gov.cn/",    # 信用大同

    # 县区政府网站
    "https://www.pingcheng.gov.cn/",       # 平城区
    "https://www.yungang.gov.cn/",         # 云冈区
    "https://www.xr.gov.cn/",              # 新荣区
    "https://www.yunzhou.gov.cn/",         # 云州区
    "https://www.dtyg.gov.cn/",            # 阳高县
    "https://www.dttz.gov.cn/",            # 天镇县
    "https://www.sx-guangling.gov.cn/",    # 广灵县
    "https://www.lingqiu.gov.cn/",         # 灵丘县
    "https://www.hunyuan.gov.cn/",         # 浑源县
    "https://www.zuoyun.gov.cn/",          # 左云县
]

MAX_PAGES = 300
REQUEST_TIMEOUT = 20
CRAWL_DELAY_SECONDS = 0.8

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

# Frontier scheduling policy
MAX_RETRY_COUNT = 5

SUCCESS_CRAWL_INTERVAL_DAYS = {
    "list": 1,
    "org_directory": 14,
    "article_changed": 7,
    "article_unchanged": 60,
    "unknown": 30,
    "default": 30,
}

# Retry index => next delay minutes.
# 0: first failure, 1: second failure, ...
FAILED_RETRY_DELAY_MINUTES = {
    0: 10,
    1: 60,
    2: 360,
    3: 1440,
    "default": 10080,
}
