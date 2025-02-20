from collections.abc import Generator
from typing import Any, Callable, ClassVar, Optional

from nonebot import get_driver, get_plugin_config
from nonebot.compat import custom_validation
from nonebot_plugin_localstore import get_data_dir
from pydantic import BaseModel, Field

DATA_DIR = get_data_dir("nonebot_plugin_paper")


@custom_validation
class RenderType(str):
    ALLOWED_VALUES: ClassVar = ["playwright", "pillow", "plaintext", "skia"]

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if value.lower() == "pillow":
            raise NotImplementedError("Pillow render is not implemented yet")
        if value.lower() == "skia":
            raise NotImplementedError("Skia render is not implemented yet")
        if value.lower() not in cls.ALLOWED_VALUES:
            raise ValueError(
                f"Invalid type: {value!r}, must be one of {cls.ALLOWED_VALUES}"
            )
        return value


class Config(BaseModel):
    paper_render: RenderType = Field(
        RenderType("plaintext"), description="paper render type"
    )
    arxiv_proxy: Optional[str] = Field(None, description="HTTP/HTTPS proxy URL")
    arxiv_timeout: float = Field(default=30.0, description="request timeout", gt=0)


global_config = get_driver().config
plugin_config = get_plugin_config(Config)
