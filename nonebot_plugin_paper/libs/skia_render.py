from io import BytesIO
import re

from aioarxiv.models import Paper
from aioarxiv.utils import logger
import matplotlib.pyplot as plt
import numpy as np
import skia


class TexRender:
    def __init__(self):
        self.font_style = {
            "normal": skia.FontStyle().Normal(),
            "bold": skia.FontStyle().Bold(),
            "italic": skia.FontStyle().Italic(),
            "bold_italic": skia.FontStyle().BoldItalic(),
        }

    async def set_attr(self, font_name, font_style="normal", is_title: bool = True):
        self.offset = 20
        self.imgs = []
        try:
            self.typeface = skia.Typeface.MakeFromName(
                font_name, self.font_style[font_style]
            )
        except Exception:
            logger.warning(
                "Failed to make the typeface. A suitable font will be automatically sought within the system."
            )
            self.typeface = None
        if is_title:
            surface = skia.Surface(1080, 42)
        surface = skia.Surface(1080, 38)
        self.canvas = surface.getCanvas()
        self.canvas.clear(skia.ColorWHITE)

    async def make(self, raw_text, is_title: bool = True):
        if not is_title:
            self.offset = 60
        elements = await self.scientific_parser(raw_text)
        for elem in elements:
            if elem["type"] == "formula":
                await self.draw_formula(elem, is_title)
            else:
                await self.draw_text(elem, is_title)
        self.imgs.append(
            self.canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        )

        return await self.merge_pictures(self.imgs)

    async def draw_formula(self, elem: dict, is_title):
        formula_img = await self.formula_img_maker(elem["content"], is_title)
        width = formula_img.width()
        height = formula_img.height()
        if self.offset + width > 1080:
            self.offset = 20
            self.canvas.saveLayer()
            self.canvas.clear(skia.ColorWHITE)
            self.imgs.append(
                self.canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
            )
            self.canvas.restore()
        rec = skia.Rect.MakeXYWH(
            self.offset,
            (self.canvas.getBaseLayerSize().height() / 2) - int(height / 2),
            width,
            height,
        )
        self.canvas.drawImageRect(formula_img, skia.Rect(0, 0, width, height), rec)
        self.offset += width + self.font.measureText(" ")

    async def draw_text(self, elem, is_title: bool):
        content_list = elem["content"].split(" ")
        if self.typeface is None:
            self.typeface = skia.FontMgr().matchFamilyStyleCharacter(
                "Aria",
                skia.FontStyle().Normal(),
                ["zh", "en"],
                ord(content_list[0][0]),
            )

        if is_title is True:
            self.typeface = skia.Typeface.MakeFromName(
                self.typeface.getFamilyName(), skia.FontStyle().Bold()
            )
            self.font = skia.Font(self.typeface, 26)
        else:
            self.font = skia.Font(self.typeface, 24)

        for content in content_list:
            metrics = self.font.getMetrics()
            y = (self.canvas.getBaseLayerSize().height() / 2) + (
                metrics.fDescent + metrics.fAscent
            ) / 2
            content += " "
            text_len = self.font.measureText(content)
            if self.offset + text_len - self.font.measureText(" ") > 1080:
                self.offset = 20
                self.canvas.saveLayer()
                self.canvas.clear(skia.ColorWHITE)
                self.imgs.append(
                    self.canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
                )
                self.canvas.restore()
            blob = skia.TextBlob.MakeFromShapedText(content, self.font)
            self.canvas.drawTextBlob(
                blob,
                self.offset,
                y - 8,
                skia.Paint(AntiAlias=True, Color=skia.ColorBLACK),
            )
            self.offset += text_len

    @staticmethod
    async def scientific_parser(raw_text: str) -> list:
        """分离文本与公式

        Args:
            raw_text (str): 源文本

        Returns:
            list: 含有文本属性的list
        """
        elements = []
        raw_text = raw_text.replace("\n", "")
        parts = re.split(r"(\$+.*?\$+)", raw_text)
        for part in parts:
            if not part.strip():
                continue
            if part.startswith("$") and part.endswith("$"):
                # 有可能是单行公式(留待以后处理)
                is_block = part.startswith("$$")
                formula = part.strip("$").strip()
                elements.append(
                    {
                        "type": "formula",
                        "content": formula,
                        "block": is_block,
                    }
                )

            else:
                part = part.strip()
                elements.append({"type": "text", "content": part})

        return elements

    @staticmethod
    async def formula_img_maker(formula, is_title: bool) -> skia.Image:
        """渲染公式图片

        Args:
            formula (str): 公式文本

        Returns:
            skia.Image: skia.Image
        """

        fig = plt.figure(figsize=(0.1, 0.1))
        if is_title is True:
            fig.text(
                0,
                0,
                f"${formula}$",
                fontsize=18,
                color="black",
                verticalalignment="bottom",
            )
        else:
            fig.text(
                0,
                0,
                f"${formula}$",
                fontsize=16,
                color="black",
                verticalalignment="bottom",
            )
        buffer = BytesIO()
        fig.savefig("2.png", format="png", dpi=90, bbox_inches="tight", pad_inches=0)
        fig.savefig(buffer, format="png", dpi=90, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        buffer.seek(0)
        return skia.Image.open(buffer)

    @staticmethod
    async def merge_pictures(img_list: list[np.ndarray]) -> np.ndarray:
        """
        Merge multiple images into a single image by stacking them vertically.

        This function takes a list of images as input and merges them into a single image by stacking them
        vertically. The width of each image must be 1080 pixels.

        Usage:
        ```python
        img1 = np.zeros([100, 1080, 4], np.uint8)
        img2 = np.zeros([200, 1080, 4], np.uint8)
        img3 = np.zeros([150, 1080, 4], np.uint8)
        img_list = [img1, img2, img3]
        merged_img = await merge_pictures(img_list)
        ```

        Args:
            img_list (list[ndarray]): A list of images to be merged.

        Returns:
            ndarray: A single image created by stacking the input images vertically.
        """
        img_top = np.zeros([0, 1080, 4], np.uint8)
        if len(img_list) == 1 and img_list[0] is not None:
            return img_list[0]
        for img in img_list:
            if img is None:
                continue
            if img.shape[1] != 1080:
                raise ValueError("The width of the image must be 1080")
            img_top = np.vstack((img_top, img))
        return img_top


async def main(paper: Paper) -> skia.Image:
    title_elemt = paper.info.title
    summary = paper.info.summary

    render = TexRender()
    await render.set_attr("Arial", "bold")
    title_img = await render.make(title_elemt, True)

    await render.set_attr("Arial", "normal", False)
    summary_img = await render.make(summary, False)

    sp = await TexRender.merge_pictures(
        [title_img, np.full((30, 1080, 4), 255, dtype=np.uint8), summary_img]
    )

    return skia.Image.fromarray(
        array=sp,
        colorType=skia.ColorType.kRGBA_8888_ColorType,
    )
