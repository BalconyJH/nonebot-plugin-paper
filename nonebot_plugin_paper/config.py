from collections.abc import Generator
from importlib.util import find_spec
from typing import Any, Callable, ClassVar

from aioarxiv.config import ArxivConfig
from nonebot import get_driver, get_plugin_config, logger, require
from nonebot.compat import custom_validation
from nonebot_plugin_localstore import get_cache_dir, get_data_dir
from pydantic import BaseModel, Field

from nonebot_plugin_paper.libs.render.dependency_manager import dependency_manager

if find_spec("nonebot_plugin_htmlrender"):
    require("nonebot_plugin_htmlrender")

DATA_DIR = get_data_dir("nonebot_plugin_paper")
CACHE_DIR = get_cache_dir("nonebot_plugin_paper")


@dependency_manager.requires(
    "playwright",
    "nonebot-plugin-htmlrender",
    component="playwright_render",
)
def check_playwright():
    pass


@dependency_manager.requires(
    "pillow",
    component="pillow_render",
)
def check_pillow():
    pass


@dependency_manager.requires(
    "skia-python", "matplotlib", "numpy", component="skia_render"
)
def check_skia():
    pass


@custom_validation
class RenderType(str):
    """A custom string-based type for specifying the rendering method.

    This class extends the built-in str type to provide validation for rendering method types.

    Attributes:
        ALLOWED_VALUES (ClassVar): A list of allowed rendering method values:
            "playwright", "pillow", "plaintext", and "skia".
            Note: Pillow is not currently implemented.
    """

    ALLOWED_VALUES: ClassVar = ["playwright", "pillow", "plaintext", "skia"]

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate the rendering method type.
        Args:
            value (str): The value to validate.

        Returns:
            str: The validated rendering method type.

        """
        if value.lower() == "pillow":
            raise NotImplementedError("Pillow render is not implemented yet")

        if value.lower() == "playwright":
            check_playwright()

        if value.lower() == "skia":
            check_skia()

        if value.lower() not in cls.ALLOWED_VALUES:
            raise ValueError(
                f"Invalid type: {value!r}, must be one of {cls.ALLOWED_VALUES}"
            )
        logger.opt(colors=True).info(
            f"Render is <g>available</g> and <y>{value}</y> is set as render type"
        )
        return value


class Config(BaseModel):
    """Configuration model for the nonebot_plugin_paper plugin.

    This class defines the configuration settings for the nonebot_plugin_paper plugin,
    including render type settings, proxy configuration, and timeout values.

    Attributes:
        arxiv_paper_render (RenderType): Type of rendering method to use for papers.
            Defaults to "plaintext". Valid values are defined in RenderType.
        arxiv_config (ArxivConfig): Configuration for the aioarxiv client.
            Defaults to ArxivConfig(). Config model can be passed from nonebot.init '
            method.

    Raises:
        ValueError: If arxiv_timeout is less than or equal to 0.
        ValidationError: If paper_render is not one of the allowed values.

    Note:
        - The paper_render setting affects how papers are displayed to users.
        - The arxiv_config setting allows customization of the aioarxiv client,
            including proxy settings, timeout values, and more. Plugin proxy parms
            will be used to set aioarxiv proxy.

    See Also:
        RenderType: For available rendering method options.
        ArxivConfig: For aioarxiv client configuration options.
    """

    arxiv_paper_render: RenderType = Field(
        RenderType("plaintext"), description="paper render type"
    )
    arxiv_config: ArxivConfig = Field(
        ArxivConfig(), description="aioarxiv client config"
    )


global_config = get_driver().config
plugin_config = get_plugin_config(Config)
