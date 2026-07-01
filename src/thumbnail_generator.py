"""
YouTube Revenge Factory - Thumbnail Generator

Professional YouTube-style thumbnail generator with multiple styles,
Arabic text support, and high-quality output.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np


@dataclass
class ThumbnailConfig:
    """Configuration for thumbnail generation."""
    width: int = 1280
    height: int = 720
    quality: int = 95
    output_format: str = "JPEG"
    font_size_title: int = 72
    font_size_text: int = 48
    shadow_offset: int = 3
    glow_radius: int = 5


class ThumbnailGenerator:
    """YouTube-style thumbnail generator with multiple artistic styles."""

    def __init__(self, config: Optional[ThumbnailConfig] = None):
        """
        Initialize the thumbnail generator.

        Args:
            config: Thumbnail configuration options
        """
        self.config = config or ThumbnailConfig()
        self._load_fonts()

    def _load_fonts(self) -> None:
        """Load fonts for text rendering with Arabic support."""
        self.fonts = {}
        
        # Try to load Arabic-friendly fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "C:/Windows/Fonts/arial.ttf",  # Windows
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    self.fonts["regular"] = ImageFont.truetype(font_path, self.config.font_size_title)
                    self.fonts["small"] = ImageFont.truetype(font_path, self.config.font_size_text)
                    break
                except (IOError, OSError):
                    continue
        
        # Fallback to default font
        if "regular" not in self.fonts:
            self.fonts["regular"] = ImageFont.load_default()
            self.fonts["small"] = ImageFont.load_default()

    def generate_thumbnail(
        self,
        story_data: Dict,
        style: str = "dramatic",
        output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """
        Generate a YouTube-style thumbnail from story data.

        Args:
            story_data: Story JSON data containing title and mood
            style: Thumbnail style (dramatic, reaction, minimalist, cinematic)
            output_path: Output file path (auto-generated if None)

        Returns:
            Path to the generated thumbnail
        """
        # Create base image
        image = self._create_background(story_data["mood"], style)
        
        # Add title text
        self._add_title_text(image, story_data["title"], style)
        
        # Add style-specific elements
        if style == "dramatic":
            self._add_dramatic_elements(image, story_data)
        elif style == "reaction":
            self._add_reaction_elements(image, story_data)
        elif style == "minimalist":
            self._add_minimalist_elements(image, story_data)
        elif style == "cinematic":
            self._add_cinematic_elements(image, story_data)
        
        # Save the thumbnail
        if output_path is None:
            output_path = self._generate_output_path(story_data, style)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        image.save(
            output_path,
            format=self.config.output_format,
            quality=self.config.quality,
            optimize=True
        )
        
        return str(output_path)

    def _create_background(self, mood: str, style: str) -> Image.Image:
        """
        Create gradient background based on mood and style.

        Args:
            mood: Story mood (e.g., 'exciting', 'mysterious', 'dramatic')
            style: Thumbnail style

        Returns:
            PIL Image with gradient background
        """
        # Create gradient based on mood
        colors = self._get_mood_colors(mood)
        
        image = Image.new("RGB", (self.config.width, self.config.height))
        draw = ImageDraw.Draw(image)
        
        # Create gradient effect
        for y in range(self.config.height):
            ratio = y / self.config.height
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.line([(0, y), (self.config.width, y)], fill=(r, g, b))
        
        # Add style-specific overlays
        if style == "dramatic":
            self._add_dramatic_overlay(image)
        elif style == "cinematic":
            self._add_cinematic_overlay(image)
        
        return image

    def _get_mood_colors(self, mood: str) -> List[tuple]:
        """
        Get color palette based on mood.

        Args:
            mood: Story mood

        Returns:
            List of RGB color tuples for gradient
        """
        mood_palettes = {
            "exciting": [(255, 69, 58), (255, 149, 0)],  # Red to Orange
            "mysterious": [(28, 28, 28), (142, 68, 173)],  # Dark to Purple
            "dramatic": [(0, 0, 0), (220, 20, 60)],  # Black to Red
            "cinematic": [(40, 40, 40), (255, 215, 0)],  # Dark to Gold
            "minimalist": [(245, 245, 245), (200, 200, 200)],  # Light gray gradient
            "reaction": [(50, 50, 50), (100, 255, 100)],  # Dark to Green
        }
        
        return mood_palettes.get(mood.lower(), mood_palettes["dramatic"])

    def _add_title_text(self, image: Image.Image, title: str, style: str) -> None:
        """
        Add title text to the thumbnail with appropriate styling.

        Args:
            image: PIL Image to modify
            title: Title text (supports Arabic)
            style: Thumbnail style
        """
        draw = ImageDraw.Draw(image)
        
        # Calculate text dimensions
        try:
            font = self.fonts["regular"]
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Fallback for text measurement
            text_width = len(title) * self.config.font_size_title // 2
            text_height = self.config.font_size_title
        
        # Position based on style
        if style == "minimalist":
            # Centered at top
            x = (self.config.width - text_width) // 2
            y = 100
        elif style == "reaction":
            # Left-aligned with space for reaction face
            x = 100
            y = 150
        else:
            # Centered at top for dramatic and cinematic
            x = (self.config.width - text_width) // 2
            y = 150
        
        # Add text with effects
        self._draw_text_with_effects(image, title, x, y, font=self.fonts["regular"])

    def _draw_text_with_effects(
        self,
        image: Image.Image,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont
    ) -> None:
        """
        Draw text with shadow and glow effects.

        Args:
            image: PIL Image to modify
            text: Text to draw
            x: X coordinate
            y: Y coordinate
            font: Font to use
        """
        draw = ImageDraw.Draw(image)
        
        # Draw shadow
        for offset_x in range(-self.config.shadow_offset, self.config.shadow_offset + 1):
            for offset_y in range(-self.config.shadow_offset, self.config.shadow_offset + 1):
                if offset_x == 0 and offset_y == 0:
                    continue
                draw.text((x + offset_x, y + offset_y), text, fill="black", font=font)
        
        # Draw main text
        draw.text((x, y), text, fill="white", font=font)
        
        # Add glow effect
        if self.config.glow_radius > 0:
            self._add_glow_effect(image, text, x, y, font)

    def _add_glow_effect(
        self,
        image: Image.Image,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont
    ) -> None:
        """
        Add glow effect to text.

        Args:
            image: PIL Image to modify
            text: Text to glow
            x: X coordinate
            y: Y coordinate
            font: Font to use
        """
        # Create a temporary image for glow
        glow_image = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_image)
        
        # Draw text multiple times with increasing sizes for glow
        for radius in range(1, self.config.glow_radius + 1):
            glow_size = radius * 2
            try:
                glow_font = ImageFont.truetype(
                    self.fonts["regular"].path if hasattr(self.fonts["regular"], "path") else "",
                    self.config.font_size_title + glow_size
                )
            except:
                glow_font = self.fonts["regular"]
            
            glow_draw.text(
                (x - radius, y - radius),
                text,
                fill=(255, 255, 255, 128 - radius * 20),
                font=glow_font
            )
        
        # Composite glow onto main image
        image.paste(glow_image, (0, 0), glow_image)

    def _add_dramatic_elements(self, image: Image.Image, story_data: Dict) -> None:
        """
        Add dramatic elements to the thumbnail.

        Args:
            image: PIL Image to modify
            story_data: Story data
        """
        draw = ImageDraw.Draw(image)
        
        # Add dramatic overlay
        overlay = Image.new("RGBA", image.size, (255, 0, 0, 30))
        image.paste(overlay, (0, 0), overlay)
        
        # Add corner brackets
        bracket_size = 60
        # Top-left
        draw.rectangle([10, 10, 10 + bracket_size, 10], fill="red", width=3)
        draw.rectangle([10, 10, 10, 10 + bracket_size], fill="red", width=3)
        # Top-right
        draw.rectangle([self.config.width - 10 - bracket_size, 10, self.config.width - 10, 10], fill="red", width=3)
        draw.rectangle([self.config.width - 10, 10, self.config.width - 10, 10 + bracket_size], fill="red", width=3)

    def _add_reaction_elements(self, image: Image.Image, story_data: Dict) -> None:
        """
        Add reaction face and elements to the thumbnail.

        Args:
            image: PIL Image to modify
            story_data: Story data
        """
        # Add reaction face placeholder
        face_size = 200
        face_x = 50
        face_y = self.config.height - face_size - 50
        
        # Draw a simple face
        face_img = Image.new("RGB", (face_size, face_size), (255, 255, 255))
        face_draw = ImageDraw.Draw(face_img)
        
        # Simple emoji-like face
        eye_size = 20
        face_draw.ellipse([50, 80, 70, 100], fill="black")
        face_draw.ellipse([90, 80, 110, 100], fill="black")
        face_draw.arc([60, 110, 100, 140], 0, 180, fill="black")
        
        image.paste(face_img, (face_x, face_y), face_img)
        
        # Add reaction text
        reaction_text = "REACTION"
        try:
            small_font = self.fonts["small"]
            bbox = draw.textbbox((0, 0), reaction_text, font=small_font)
            text_width = bbox[2] - bbox[0]
            x = face_x + (face_size - text_width) // 2
            y = face_y - 30
            draw.text((x, y), reaction_text, fill="yellow", font=small_font)
        except:
            pass

    def _add_minimalist_elements(self, image: Image.Image, story_data: Dict) -> None:
        """
        Add minimalist elements to the thumbnail.

        Args:
            image: PIL Image to modify
            story_data: Story data
        """
        # Add subtle grid pattern
        grid_size = 30
        draw = ImageDraw.Draw(image)
        
        for x in range(0, self.config.width, grid_size):
            draw.line([(x, 0), (x, self.config.height)], fill=(255, 255, 255, 30), width=1)
        
        for y in range(0, self.config.height, grid_size):
            draw.line([(0, y), (self.config.width, y)], fill=(255, 255, 255, 30), width=1)
        
        # Add corner accent
        accent_size = 40
        draw.rectangle(
            [self.config.width - accent_size, self.config.height - accent_size,
             self.config.width, self.config.height],
            fill="white", opacity=50
        )

    def _add_cinematic_elements(self, image: Image.Image, story_data: Dict) -> None:
        """
        Add cinematic elements to the thumbnail.

        Args:
            image: PIL Image to modify
            story_data: Story data
        """
        # Add film strip effect
        film_size = 80
        film_x = self.config.width - film_size - 20
        
        for i in range(3):
            y = 50 + i * (film_size + 10)
            draw = ImageDraw.Draw(image)
            draw.rectangle([film_x, y, film_x + film_size, y + film_size], fill="gray", outline="white", width=2)
            
            # Add sprocket holes
            hole_size = 8
            draw.ellipse([film_x - hole_size, y, film_x, y + hole_size], fill="white")
            draw.ellipse([film_x - hole_size, y + film_size - hole_size, film_x, y + film_size], fill="white")

    def _add_dramatic_overlay(self, image: Image.Image) -> None:
        """
        Add dramatic overlay to image.

        Args:
            image: PIL Image to modify
        """
        overlay = Image.new("RGBA", image.size, (20, 0, 0, 50))
        image.paste(overlay, (0, 0), overlay)

    def _add_cinematic_overlay(self, image: Image.Image) -> None:
        """
        Add cinematic overlay to image.

        Args:
            image: PIL Image to modify
        """
        # Add film grain effect
        noise = np.random.normal(0, 10, (self.config.height, self.config.width, 3)).astype(np.uint8)
        noise_image = Image.fromarray(noise, "RGB")
        
        # Blend noise with original
        image = Image.composite(
            image.convert("RGB"),
            noise_image,
            Image.new("RGB", image.size, (128, 128, 128))
        )

    def _generate_output_path(self, story_data: Dict, style: str) -> str:
        """
        Generate output file path.

        Args:
            story_data: Story data
            style: Thumbnail style

        Returns:
            Output file path
        """
        title_slug = "".join(c for c in story_data["title"] if c.isalnum()).lower()
        timestamp = int(__import__("time").time())
        
        return f"thumbnails/{title_slug}_{style}_{timestamp}.jpg"


def generate_thumbnail_from_json(
    json_path: Union[str, Path],
    style: str = "dramatic",
    output_dir: Optional[Union[str, Path]] = None
) -> str:
    """
    Convenience function to generate thumbnail from JSON file.

    Args:
        json_path: Path to story JSON file
        style: Thumbnail style
        output_dir: Output directory (uses thumbnails/ if None)

    Returns:
        Path to generated thumbnail
    """
    json_path = Path(json_path)
    
    with open(json_path, "r", encoding="utf-8") as f:
        story_data = json.load(f)
    
    if output_dir is None:
        output_dir = Path("thumbnails")
    
    generator = ThumbnailGenerator()
    return generator.generate_thumbnail(story_data, style, output_dir / f"{json_path.stem}_{style}.jpg")


def batch_generate_thumbnails(
    json_files: List[Union[str, Path]],
    styles: Optional[List[str]] = None,
    output_dir: Optional[Union[str, Path]] = None
) -> List[str]:
    """
    Generate thumbnails for multiple JSON files.

    Args:
        json_files: List of JSON file paths
        styles: List of styles to generate (all if None)
        output_dir: Output directory

    Returns:
        List of generated thumbnail paths
    """
    if styles is None:
        styles = ["dramatic", "reaction", "minimalist", "cinematic"]
    
    generated_paths = []
    
    for json_file in json_files:
        for style in styles:
            try:
                path = generate_thumbnail_from_json(json_file, style, output_dir)
                generated_paths.append(path)
                print(f"Generated: {path}")
            except Exception as e:
                print(f"Error generating thumbnail for {json_file} with style {style}: {e}")
    
    return generated_paths


if __name__ == "__main__":
    # Example usage
    example_story = {
        "title": "The Mystery of the Vanishing Stars",
        "mood": "mysterious"
    }
    
    generator = ThumbnailGenerator()
    thumbnail_path = generator.generate_thumbnail(example_story, "dramatic")
    print(f"Generated thumbnail: {thumbnail_path}")

    # Generate multiple styles
    styles = ["dramatic", "reaction", "minimalist", "cinematic"]
    for style in styles:
        path = generator.generate_thumbnail(example_story, style)
        print(f"Generated {style} thumbnail: {path}")