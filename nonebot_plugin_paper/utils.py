from typing import Callable

from aioarxiv.models import Paper
from aioarxiv.utils import create_trace_config
from aiohttp import ClientError, ClientSession, ClientTimeout
from nonebot import logger

from nonebot_plugin_paper.config import plugin_config


def text_paper_info(paper: Paper) -> str:
    """
    Formats the paper information into a text message.

    Args:
        paper: The paper object to format.

    Returns:
        The formatted text message.
    """
    authors = ", ".join([author.name for author in paper.info.authors])
    published_date = paper.info.published.strftime("%Y-%m-%d")
    updated_date = paper.info.updated.strftime("%Y-%m-%d")
    summary = (
        f"{paper.info.summary[:250]}..."
        if len(paper.info.summary) > 200
        else paper.info.summary
    )

    template = (
        f"📄 Title: {paper.info.title}\n"
        f"👥 Authors: {authors}\n"
        f"🏷️ Categories: {paper.info.categories.primary.term}\n"
        f"📅 Published Date: {published_date}\n"
        f"🔄 Updated Date: {updated_date}\n"
        f"📝 Summary: {summary}\n"
    )

    if paper.doi:
        template += f"🔗 DOI: {paper.doi}\n"
    if paper.journal_ref:
        template += f"📚 Journal Reference: {paper.journal_ref}\n"
    if paper.pdf_url:
        template += f"📥 PDF Download Link: {paper.pdf_url}\n"
    if paper.comment:
        template += f"💬 Comment: {paper.comment}\n"

    return template


async def connection_verification() -> bool:
    """
    Verifies the proxy configuration by sending a request to the arXiv website.

    Returns:
        True if the proxy is working, False otherwise.
    """
    proxy = plugin_config.arxiv_config.proxy or None

    try:
        async with (
            ClientSession(
                timeout=ClientTimeout(total=10),
                trace_configs=[create_trace_config()],
            ) as session,
            session.request("GET", "https://arxiv.org/", proxy=proxy) as resp,
        ):
            if resp.status == 200:
                logger.info(
                    "Proxy verification successful"
                    if proxy
                    else "arXiv connection verification successful"
                )
                return True
            logger.warning(
                f"Conection verification failed with status code: {resp.status}"
            )
            return False
    except ClientError as e:
        logger.error(f"Conection verification failed with client error: {e}")
    except Exception as e:
        logger.error(f"Conection verification failed with exception: {e}")

    return False


async def get_llm_summary(func: Callable, paper: Paper) -> str:
    """
    Get the summary of the paper and pass it to the llm api function.

    Args:
        func: The function to pass the summary to.
        paper: The paper object to get the summary from.

    Returns:
        The result of the llm response.
    """
    return await func(
        paper.info.title,
        paper.info.summary,
        paper.info.authors,
    )
