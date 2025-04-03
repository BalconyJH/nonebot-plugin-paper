from nonebot import get_driver, require

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
require("nonebot_plugin_uninfo")
require("nonebot_plugin_apscheduler")
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from .command import paper_cmd  # noqa: F401
from .config import Config
from .utils import connection_verification

__plugin_meta__ = PluginMetadata(
    name="nonebot_plugin_paper",
    description="Nonebot plugin for arXiv.",
    usage="""\
    """,
    type="application",
    homepage="https://github.com/BalconyJH/nonebot-plugin-paper",
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    config=Config,
)

driver = get_driver()


@driver.on_startup
async def init():
    await connection_verification()
