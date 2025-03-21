from aioarxiv.client.arxiv_client import ArxivClient
from arclet.alconna import Alconna, Args, Subcommand
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot_plugin_alconna import Image, UniMessage, UniMsg, on_alconna
from nonebot_plugin_htmlrender import capture_element
from nonebot_plugin_uninfo import Uninfo

from nonebot_plugin_paper.utils import text_paper_info

paper_cmd = on_alconna(
    Alconna(
        "paper",
        Subcommand(
            "-s|--search",
            Args["keyword", str],
        ),
        Subcommand(
            "-id",
            Args["id", str],
        ),
    ),
    priority=5,
    block=True,
)


@paper_cmd.assign("search")
async def handle_search(keyword: str, state: T_State, uninfo: Uninfo, unimsg: UniMsg):
    logger.debug(f"Searching for {keyword} by {uninfo.user.id}")
    async with ArxivClient() as client:
        result = await client.search(
            keyword,
            max_results=1,
        )
        await paper_cmd.send(
            f"Search result for {keyword} and get {result.total_result} papers"
        )
        for paper in result.papers:
            await paper_cmd.send(text_paper_info(paper))


@paper_cmd.assign("id")
async def handle_id(paper_id: str, state: T_State, uninfo: Uninfo, unimsg: UniMsg):
    logger.debug(f"Searching for {paper_id} by {uninfo.user.id}")
    img = await capture_element(
        f"https://arxiv.org/abs/{paper_id}",
        element="#abs-outer > div.leftcolumn",
    )
    await UniMessage(Image(raw=img)).finish(reply_to=True)
