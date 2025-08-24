from collections.abc import Callable, Generator
from importlib.util import find_spec
import sys
from typing import Any, ClassVar

from aioarxiv.config import ArxivConfig
from nonebot import get_driver, get_plugin_config, logger, require
from nonebot.compat import custom_validation
from nonebot_plugin_localstore import (
    get_plugin_cache_dir,
    get_plugin_data_dir,
)
from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from strenum import StrEnum

from nonebot_plugin_paper.libs.render.dependency_manager import dependency_manager

DATA_DIR = get_plugin_data_dir()
CACHE_DIR = get_plugin_cache_dir()


class RenderTypeEnum(StrEnum):
    PLAYWRIGHT = "playwright"
    PILLOW = "pillow"
    PLAINTEXT = "plaintext"
    SKIA = "skia"


@dependency_manager.requires(
    RenderTypeEnum.PLAYWRIGHT,
    "nonebot-plugin-htmlrender",
    component="playwright_render",
)
def check_playwright():
    pass


@dependency_manager.requires(
    RenderTypeEnum.PILLOW,
    component="pillow_render",
)
def check_pillow():
    pass


@dependency_manager.requires(
    "skia_python", "matplotlib", "numpy", component="skia_render"
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

    ALLOWED_VALUES: ClassVar = [e.value for e in RenderTypeEnum]

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
        if value.lower() == RenderTypeEnum.PILLOW:
            raise NotImplementedError("Pillow render is not implemented yet")

        try:
            if value.lower() == RenderTypeEnum.PLAYWRIGHT:
                check_playwright()
            if value.lower() == RenderTypeEnum.SKIA:
                check_skia()
        except RuntimeError as e:
            logger.error(f"Dependency error for render type '{value}': {e}")

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

if plugin_config.arxiv_paper_render is RenderTypeEnum.PLAYWRIGHT and find_spec(
    "nonebot_plugin_htmlrender"
):
    require("nonebot_plugin_htmlrender")
