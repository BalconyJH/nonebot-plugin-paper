ARXIV_LINK_REGEX = r"arxiv\.org"
ARXIV_LINK_PATTERN = (
    rf"https?://{ARXIV_LINK_REGEX}/(abs|pdf)/(?P<article_id>[0-9]+\.[0-9]+(v[0-9]+)?)"
)
