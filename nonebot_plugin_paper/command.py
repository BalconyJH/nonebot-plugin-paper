from typing import Annotated, Optional

from aioarxiv.client.arxiv_client import ArxivClient, SortCriterion, SortOrder
from aioarxiv.config import ArxivConfig
from arclet.alconna import Alconna, Args, MultiVar, Subcommand
from nonebot import on_regex
from nonebot.log import logger
from nonebot.params import RegexDict
from nonebot_plugin_alconna import (
    AlconnaQuery,
    Image,
    Match,
    Option,
    Query,
    UniMessage,
    on_alconna,
)
from nonebot_plugin_uninfo import Uninfo

from nonebot_plugin_paper.config import plugin_config
from nonebot_plugin_paper.libs.arxiv import ARXIV_LINK_PATTERN
from nonebot_plugin_paper.libs.render import render_selector

# Single instance to ensure that rate limiting measures takes effect.
arxiv_client = ArxivClient(
    config=ArxivConfig(
        **plugin_config.arxiv_config.model_dump(),
    )
)
render_func = render_selector(plugin_config.arxiv_paper_render)

paper_cmd = on_alconna(
    Alconna(
        "paper",
        Subcommand(
            "-s|--search",
            Args["keyword", MultiVar("str")],
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
            Args["paper_id", str],
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
async def handle_link(match_group: Annotated[dict, RegexDict()]):
    if plugin_config.arxiv_paper_render == "playwright":
        data = await render_func(match_group["article_id"])
        if not isinstance(data, str):
            await UniMessage(Image(raw=data)).finish(reply_to=True)
        else:
            await UniMessage("Unhandled error").finish(reply_to=True)

    async with ArxivClient() as client:
        result = await client.search(
            id_list=[match_group["article_id"]],
        )
        if result.total_result == 0:
            await paper.finish("No such paper found")

        data = await render_func(result.papers[0])

        if not isinstance(data, str):
            await UniMessage(Image(raw=data)).finish(reply_to=True)
        else:
            await UniMessage(data).finish(reply_to=True)


@paper_cmd.assign("search")
async def handle_search(
    keyword: Match[tuple[str, ...]],
    uninfo: Uninfo,
    number: Query[int] = AlconnaQuery("number", 1),
    sort: Query[Optional[SortCriterion]] = AlconnaQuery("sort", None),
    order: Query[Optional[SortOrder]] = AlconnaQuery("order", None),
    start: Query[Optional[int]] = AlconnaQuery("start", None),
):
    logger.debug(f"Searching for {keyword} by {uninfo.user.id}")

    if not keyword.available:
        await paper_cmd.finish("No keyword provided")

    _keyword = " ".join(keyword.result) if keyword.available else ""

    async with arxiv_client:
        result = await arxiv_client.search(
            _keyword,
            max_results=number.result,
            sort_by=sort.result,
            sort_order=order.result,
            start=start.result,
        )
        await paper_cmd.send(
            f"Search result for {_keyword} and get {result.total_result} papers"
        )
        for _ in result.papers:
            data = await render_func(_)
            if not isinstance(data, str):
                await UniMessage(Image(raw=data)).finish(reply_to=True)
            else:
                await UniMessage(data).finish(reply_to=True)


@paper_cmd.assign("id")
async def handle_id(paper_id: str):
    if plugin_config.arxiv_paper_render == "playwright":
        data = await render_func(paper_id)  # type: ignore
        if not isinstance(data, str):
            await UniMessage(Image(raw=data)).finish(reply_to=True)
        else:
            await UniMessage("Unhandled error").finish(reply_to=True)
    async with arxiv_client:
        result = await arxiv_client.search(
            id_list=[paper_id],
        )

        if result.total_result == 0:
            await paper.finish("No such paper found")

        data = await render_func(result.papers[0])

        if not isinstance(data, str):
            await UniMessage(Image(raw=data)).finish(reply_to=True)
        else:
            await UniMessage(data).finish(reply_to=True)
