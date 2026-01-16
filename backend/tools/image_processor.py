"""
Image processing tool for resizing, cropping, and converting image formats.
"""

import io
import base64
import logging
from pathlib import Path
from typing import Optional

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageProcessorTool(BaseTool):
    """Tool for image processing operations."""

    @property
    def name(self) -> str:
        return "image_processor"

    @property
    def description(self) -> str:
        return "Process images: resize, crop, convert format, rotate, apply filters, adjust brightness/contrast"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input_path": {
                    "type": "string",
                    "description": "Path to the input image file"
                },
                "output_path": {
                    "type": "string",
                    "description": "Path for the output image file"
                },
                "operation": {
                    "type": "string",
                    "enum": ["resize", "crop", "rotate", "convert", "blur", "sharpen", "brightness", "contrast", "grayscale", "thumbnail"],
                    "description": "The image operation to perform"
                },
                "width": {
                    "type": "integer",
                    "description": "Target width for resize/thumbnail operations"
                },
                "height": {
                    "type": "integer",
                    "description": "Target height for resize/thumbnail operations"
                },
                "crop_box": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Crop coordinates: [left, top, right, bottom]"
                },
                "angle": {
                    "type": "number",
                    "description": "Rotation angle in degrees"
                },
                "format": {
                    "type": "string",
                    "enum": ["PNG", "JPEG", "GIF", "WEBP", "BMP", "TIFF"],
                    "description": "Output image format"
                },
                "factor": {
                    "type": "number",
                    "description": "Factor for brightness/contrast adjustment (1.0 = no change)"
                },
                "quality": {
                    "type": "integer",
                    "description": "JPEG quality (1-95)",
                    "minimum": 1,
                    "maximum": 95
                }
            },
            "required": ["input_path", "operation"]
        }

    async def execute(
        self,
        input_path: str,
        operation: str,
        output_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop_box: Optional[list] = None,
        angle: Optional[float] = None,
        format: Optional[str] = None,
        factor: Optional[float] = None,
        quality: int = 85,
        **kwargs
    ) -> ToolResult:
        """Execute image processing operation."""

        if not PIL_AVAILABLE:
            return ToolResult(
                success=False,
                output="",
                error="Pillow (PIL) is not installed. Please install it with: pip install pillow"
            )

        try:
            # Load image
            input_file = Path(input_path)
            if not input_file.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Input file not found: {input_path}"
                )

            img = Image.open(input_file)
            original_format = img.format

            # Perform operation
            if operation == "resize":
                if not width or not height:
                    return ToolResult(
                        success=False,
                        output="",
                        error="Width and height required for resize operation"
                    )
                img = img.resize((width, height), Image.Resampling.LANCZOS)

            elif operation == "thumbnail":
                if not width or not height:
                    return ToolResult(
                        success=False,
                        output="",
                        error="Width and height required for thumbnail operation"
                    )
                img.thumbnail((width, height), Image.Resampling.LANCZOS)

            elif operation == "crop":
                if not crop_box or len(crop_box) != 4:
                    return ToolResult(
                        success=False,
                        output="",
                        error="crop_box with [left, top, right, bottom] required for crop operation"
                    )
                img = img.crop(tuple(crop_box))

            elif operation == "rotate":
                if angle is None:
                    return ToolResult(
                        success=False,
                        output="",
                        error="Angle required for rotate operation"
                    )
                img = img.rotate(angle, expand=True)

            elif operation == "convert":
                # Format conversion happens during save
                pass

            elif operation == "blur":
                img = img.filter(ImageFilter.GaussianBlur(radius=2))

            elif operation == "sharpen":
                img = img.filter(ImageFilter.SHARPEN)

            elif operation == "brightness":
                if factor is None:
                    factor = 1.0
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(factor)

            elif operation == "contrast":
                if factor is None:
                    factor = 1.0
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(factor)

            elif operation == "grayscale":
                img = img.convert("L")

            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown operation: {operation}"
                )

            # Determine output path and format
            if not output_path:
                output_path = str(input_file.with_suffix(
                    f".{format.lower()}" if format else input_file.suffix
                ).with_stem(f"{input_file.stem}_processed"))

            output_file = Path(output_path)
            save_format = format or original_format or "PNG"

            # Handle RGBA to RGB conversion for JPEG
            if save_format.upper() == "JPEG" and img.mode == "RGBA":
                img = img.convert("RGB")

            # Save image
            save_kwargs = {}
            if save_format.upper() == "JPEG":
                save_kwargs["quality"] = quality

            img.save(output_file, format=save_format, **save_kwargs)

            logger.info(f"Image processed: {operation} on {input_path} -> {output_path}")

            return ToolResult(
                success=True,
                output=f"Image processed successfully. Operation: {operation}. Output: {output_path}. Size: {img.size[0]}x{img.size[1]}"
            )

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Image processing failed: {str(e)}"
            )
