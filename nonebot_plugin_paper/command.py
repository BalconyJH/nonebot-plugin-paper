from typing import Annotated, Optional

from aioarxiv.client.arxiv_client import ArxivClient, SortCriterion, SortOrder
from arclet.alconna import Alconna, Args, Subcommand
from nonebot import on_regex
from nonebot.log import logger
from nonebot.params import RegexStr
from nonebot.typing import T_State
from nonebot_plugin_alconna import (
    AlconnaQuery,
    Image,
    Option,
    Query,
    UniMessage,
    UniMsg,
    on_alconna,
)
from nonebot_plugin_htmlrender import capture_element
from nonebot_plugin_uninfo import Uninfo

from nonebot_plugin_paper.libs.arxiv import ARXIV_LINK_PATTERN
from nonebot_plugin_paper.utils import text_paper_info

paper_cmd = on_alconna(
    Alconna(
        "paper",
        Subcommand(
            "-s|--search",
            Args["keyword", str],
            Option("--number", Args["number", int]),
            Option(
                "--sort",
                Args["sort", ["relevance", "lastUpdatedDate", "submittedDate"]],
            ),
            Option("--order", Args["order", ["ascending", "descending"]]),
            Option("--start", Args["start", int]),
        ),
        Subcommand(
            "-id",
            Args["id", str],
        ),
    ),
    priority=5,
    block=True,
)

paper = on_regex(
    rf"{ARXIV_LINK_PATTERN}",
    priority=5,
)


@paper.handle()
async def handle_link(
    state: T_State, uninfo: Uninfo, unimsg: UniMsg, link: Annotated[str, RegexStr()]
):
    logger.debug(f"Trigger paper web screenshot by {uninfo.user.id}")

    # replace pdf with abs to the abstract page
    link = link.replace("pdf", "abs")

    logger.debug(f"Capturing {link}")

    await UniMessage(
        Image(
            raw=await capture_element(
                link,
                element="#abs-outer > div.leftcolumn",
            )
        )
    ).finish(reply_to=True)


@paper_cmd.assign("search")
async def handle_search(
    keyword: str,
    state: T_State,
    uninfo: Uninfo,
    unimsg: UniMsg,
    number: Query[int] = AlconnaQuery("number", 1),
    sort: Query[Optional[SortCriterion]] = AlconnaQuery("sort", None),
    order: Query[Optional[SortOrder]] = AlconnaQuery("order", None),
    start: Query[Optional[int]] = AlconnaQuery("start", None),
):
    logger.debug(f"Searching for {keyword} by {uninfo.user.id}")
    async with ArxivClient() as client:
        result = await client.search(
            keyword,
            max_results=number.result,
            sort_by=sort.result,
            sort_order=order.result,
            start=start.result,
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
