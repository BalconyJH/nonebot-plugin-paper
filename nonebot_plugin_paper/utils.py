from typing import Callable

from aioarxiv.models import Paper
from aioarxiv.utils import create_trace_config
from aiohttp import ClientError, ClientSession, ClientTimeout
from nonebot import logger

from nonebot_plugin_paper.config import plugin_config


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
