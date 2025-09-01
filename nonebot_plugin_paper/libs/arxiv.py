ARXIV_LINK_REGEX = r"arxiv\.org"
ARXIV_LINK_PATTERN = (
    rf"https?://{ARXIV_LINK_REGEX}/(abs|pdf)/"
    r"(?P<article_id>"
    r"(\d{4}\.\d{4,5}(v\d+)?)"  # 新格式: YYMM.NNNNN[vV]
    r"|"
    r"([a-z\-]+(\.[A-Z]{2})?/\d{7}(v\d+)?)"  # 旧格式: category/NNNNNNN[vV]
    r")"
    r"(?:\?.*)?$"  # 仅允许URL参数或结束，不允许其他字符
)
