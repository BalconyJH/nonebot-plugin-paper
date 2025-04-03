from dataclasses import dataclass
from io import BytesIO
import re
from typing import Literal

from aioarxiv.models import Paper
import matplotlib.pyplot as plt
import numpy as np
import skia


@dataclass
class TextElement:
    content: str
    type: Literal["text", "formula"]
    block: bool = False


@dataclass
class RenderConfig:
    width: int = 1080
    title_height: int = 42
    content_height: int = 38
    title_font_size: int = 26
    content_font_size: int = 24
    margin: int = 20
    spacing: int = 30


class TextRenderer:
    def __init__(
        self, canvas: skia.Canvas, font: skia.Font, offset: int, margin: int, width: int
    ):
        self.canvas = canvas
        self.font = font
        self.current_offset = offset
        self.margin = margin
        self.width = width
        self.y_position = self._calculate_y_position()

    def _calculate_y_position(self) -> float:
        """Calculate the vertical position for text rendering."""
        metrics = self.font.getMetrics()
        base_height = self.canvas.getBaseLayerSize().height() / 2
        return base_height + (metrics.fDescent + metrics.fAscent) / 2 - 8

    async def render_words(self, words: list[str]) -> tuple[bool, int]:
        """Render a list of words.

        Returns:
            tuple[bool, int]: (needs_new_line, last_processed_word_index)
        """
        word_index = 0
        while word_index < len(words):
            word = f"{words[word_index]} "
            text_width = self.font.measureText(word)

            if self._needs_new_line(text_width):
                result = await self._handle_line_break(word, word_index)
                if result is not None:
                    return result

            await self._render_word(word)
            word_index += 1

        return False, len(words)

    def _needs_new_line(self, text_width: float) -> bool:
        """Check if text needs to start a new line."""
        space_width = self.font.measureText(" ")
        return self.current_offset + text_width - space_width > self.width

    async def _handle_line_break(self, word: str, word_index: int) -> tuple[bool, int]:
        """Handle line break cases.

        Returns:
            tuple[bool, int]: Return values if line break needed, None otherwise
        """
        if self.current_offset == self.margin:
            # Force render long word at start of line
            await self._render_word(word)
            self.current_offset += self.font.measureText(word)
            return True, word_index + 1

        return True, word_index

    async def _render_word(self, word: str) -> None:
        """Render a single word to the canvas."""
        blob = skia.TextBlob.MakeFromShapedText(word, self.font)
        self.canvas.drawTextBlob(
            blob,
            self.current_offset,
            self.y_position,
            skia.Paint(AntiAlias=True, Color=skia.ColorBLACK),
        )
        self.current_offset += self.font.measureText(word)


class FormulaRenderer:
    def __init__(self, config: RenderConfig):
        self.config = config

    async def render_formula(self, formula: str, *, is_title: bool) -> skia.Image:
        """Render a mathematical formula to an image using matplotlib."""
        fig = plt.figure(figsize=(0.1, 0.1))
        font_size = (
            self.config.title_font_size if is_title else self.config.content_font_size
        )

        fig.text(
            0,
            0,
            f"${formula}$",
            fontsize=font_size,
            color="black",
            verticalalignment="bottom",
        )

        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=90, bbox_inches="tight", pad_inches=0)
        plt.close(fig)

        buffer.seek(0)
        return skia.Image.open(buffer)


class TextParser:
    @staticmethod
    async def parse_scientific_text(raw_text: str) -> list[TextElement]:
        """Parse text containing both normal text and mathematical formulas."""
        elements = []
        raw_text = raw_text.replace("\n", "")
        parts = re.split(r"(\$+.*?\$+)", raw_text)

        for part in parts:
            if not part.strip():
                continue

            if part.startswith("$") and part.endswith("$"):
                # TODO)) 有可能是单行公式(留待以后处理)
                is_block = part.startswith("$$")
                formula = part.strip("$").strip()
                elements.append(
                    TextElement(content=formula, type="formula", block=is_block)
                )
            else:
                elements.append(TextElement(content=part.strip(), type="text"))

        return elements


class Render:
    def __init__(self, config: RenderConfig = RenderConfig()):
        self.config = config
        self.formula_renderer = FormulaRenderer(config)
        self.text_parser = TextParser()
        self.font_style = {
            "normal": skia.FontStyle().Normal(),
            "bold": skia.FontStyle().Bold(),
            "italic": skia.FontStyle().Italic(),
            "bold_italic": skia.FontStyle().BoldItalic(),
        }
        self.reset()

    def reset(self):
        """Reset renderer state"""
        self.offset = self.config.margin
        self.imgs = []

    async def create_surface(
        self, *, is_title: bool
    ) -> tuple[skia.Surface, skia.Canvas]:
        """Create a new surface and canvas for rendering."""
        height = self.config.title_height if is_title else self.config.content_height
        surface = skia.Surface(self.config.width, height)
        canvas = surface.getCanvas()
        canvas.clear(skia.ColorWHITE)
        return surface, canvas

    async def setup_font(
        self, font_name: str, style: str = "normal", *, is_title: bool = False
    ) -> skia.Font:
        """Set up the font with specified parameters."""
        try:
            typeface = skia.Typeface.MakeFromName(font_name, self.font_style[style])
        except Exception:
            typeface = skia.FontMgr().matchFamilyStyleCharacter(
                "Arial", self.font_style["normal"], ["zh", "en"], ord("a")
            )

        if is_title:
            typeface = skia.Typeface.MakeFromName(
                typeface.getFamilyName(), self.font_style["bold"]
            )

        font_size = (
            self.config.title_font_size if is_title else self.config.content_font_size
        )
        return skia.Font(typeface, font_size)

    async def render_text(
        self, element: TextElement, canvas: skia.Canvas, font: skia.Font
    ) -> tuple[bool, int]:
        """Render text element and return whether new line is needed and the last processed word index.

        Args:
            element: The text element to render
            canvas: The canvas to draw on
            font: The font to use for rendering

        Returns:
            tuple[bool, int]: (needs_new_line, last_processed_word_index)
        """
        text_renderer = TextRenderer(
            canvas=canvas,
            font=font,
            offset=self.offset,
            margin=self.config.margin,
            width=self.config.width,
        )

        words = element.content.split(" ")
        result = await text_renderer.render_words(words)
        self.offset = text_renderer.current_offset
        return result

    async def render_section(self, text: str, *, is_title: bool = False) -> np.ndarray:
        """Render a complete section of text (title or content)."""
        self.reset()
        await self._init_rendering_context(text, is_title=is_title)
        await self._render_elements()
        self.imgs.append(self._get_current_canvas_image())
        return await self.merge_images(self.imgs)

    async def _init_rendering_context(self, text: str, *, is_title: bool) -> None:
        """Initialize the rendering context with required components."""
        self.elements = await self.text_parser.parse_scientific_text(text)
        self.surface, self.canvas = await self.create_surface(is_title=is_title)
        self.font = await self.setup_font(
            "Arial", "bold" if is_title else "normal", is_title=is_title
        )
        self.offset = self.config.margin if is_title else 60
        self.is_title = is_title
        self.current_element_index = 0

    async def _render_elements(self) -> None:
        """Render all elements in the current context."""
        while self.current_element_index < len(self.elements):
            element = self.elements[self.current_element_index]
            if element.type == "formula":
                await self._render_formula_element(element)
            else:
                await self._render_text_element(element)

            if self.current_element_index < len(self.elements):
                await self._check_next_element()

    async def _render_formula_element(self, element: TextElement) -> None:
        """Render a formula element."""
        formula_img = await self.formula_renderer.render_formula(
            element.content, is_title=self.is_title
        )
        width, height = formula_img.width(), formula_img.height()

        if not await self._ensure_space_for_width(width):
            return  # Will retry this element

        await self._draw_formula_image(formula_img, width, height)
        self.offset += width + self.font.measureText(" ")
        self.current_element_index += 1

    async def _render_text_element(self, element: TextElement) -> None:
        """Render a text element."""
        current_words = element.content.split(" ")
        while current_words:
            needs_new_line, processed_index = await self.render_text(
                TextElement(content=" ".join(current_words), type="text"),
                self.canvas,
                self.font,
            )

            if needs_new_line:
                await self._create_new_canvas_line()
                if processed_index > 0:
                    current_words = current_words[processed_index:]
                continue

            current_words = []

        self.current_element_index += 1

    async def _ensure_space_for_width(self, width: int) -> bool:
        """Ensure there's enough space for the given width, create new line if needed."""
        if self.offset + width > self.config.width:
            await self._create_new_canvas_line()
            return False
        return True

    async def _create_new_canvas_line(self) -> None:
        """Create a new canvas line and reset rendering context."""
        self.canvas.saveLayer()
        self.imgs.append(self._get_current_canvas_image())
        self.canvas.restore()
        self.surface, self.canvas = await self.create_surface(is_title=self.is_title)
        self.offset = self.config.margin

    async def _draw_formula_image(
        self, formula_img: skia.Image, width: int, height: int
    ) -> None:
        """Draw formula image on the canvas."""
        rec = skia.Rect.MakeXYWH(
            self.offset,
            self.canvas.getBaseLayerSize().height() / 2 - height // 2,
            width,
            height,
        )
        self.canvas.drawImageRect(formula_img, skia.Rect(0, 0, width, height), rec)

    async def _check_next_element(self) -> None:
        """Check if the next element needs a new line."""
        element = self.elements[self.current_element_index]
        if element.type == "formula" and self.current_element_index + 1 < len(
            self.elements
        ):
            next_element = self.elements[self.current_element_index + 1]
            if next_element.type == "text":
                next_word = next_element.content.split(" ")[0]
                if self.offset + self.font.measureText(next_word) > self.config.width:
                    await self._create_new_canvas_line()

    def _get_current_canvas_image(self) -> np.ndarray:
        """Get the current canvas as an image array."""
        return self.canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)

    @staticmethod
    async def merge_images(images: list[np.ndarray]) -> np.ndarray:
        """Merge multiple images vertically."""
        if len(images) == 1:
            return images[0]

        result = np.zeros([0, 1080, 4], np.uint8)
        for img in images:
            if img is None:
                continue
            if img.shape[1] != 1080:
                raise ValueError("Image width must be 1080")
            result = np.vstack((result, img))

        return result


async def render_paper(paper: Paper) -> bytes:
    """Render a complete paper with title and summary."""
    config = RenderConfig()
    renderer = Render(config)

    # Render title and summary
    title_img = await renderer.render_section(paper.info.title, is_title=True)
    summary_img = await renderer.render_section(paper.info.summary, is_title=False)

    # Merge all components with correct spacing
    final_image = await renderer.merge_images(
        [title_img, np.full((30, 1080, 4), 255, dtype=np.uint8), summary_img]
    )

    return (
        skia.Image.fromarray(
            array=final_image, colorType=skia.ColorType.kRGBA_8888_ColorType
        )
        .encodeToData()
        .bytes()
    )
