from typing import Union

from aioarxiv.models import Paper
from nonebot_plugin_htmlrender import capture_element


class Render:
    pass


async def render_paper(paper_id: Union[str, Paper]):
    if isinstance(paper_id, Paper):
        paper_id = paper_id.info.id
    link = f"https://arxiv.org/abs/{paper_id}"
    return await capture_element(
        link,
        element="#abs-outer > div.leftcolumn",
    )
