from nonebot import logger

from nonebot_plugin_paper.libs.render.plain_render import (
    render_paper as render_plain_paper,
)


def render_selector(render_type: str):
    """Render a complete paper with title and summary."""
    if render_type == "playwright":
        logger.debug("Playwright render triggered")
        from nonebot_plugin_paper.libs.render.html_render import (
            render_paper,
        )

        return render_paper

    if render_type == "pillow":
        logger.debug("Pillow render triggered")
        from nonebot_plugin_paper.libs.render.pillow_render import (
            render_paper,
        )

        return render_paper

    if render_type == "skia":
        logger.debug("Skia render triggered")
        from nonebot_plugin_paper.libs.render.skia_render import (
            render_paper,
        )

        return render_paper

    if render_type == "plaintext":
        logger.debug("Plaintext render triggered")
        return render_plain_paper

    raise ValueError(f"Unsupported render type: {render_type}")
