"""PDF compression logic."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class CompressionProfile:
    name: str
    image_quality: int
    dpi_threshold: int
    dpi_target: int


PROFILES: dict[str, CompressionProfile] = {
    "low": CompressionProfile(
        name="Низкое сжатие",
        image_quality=85,
        dpi_threshold=200,
        dpi_target=150,
    ),
    "medium": CompressionProfile(
        name="Среднее сжатие",
        image_quality=65,
        dpi_threshold=150,
        dpi_target=120,
    ),
    "high": CompressionProfile(
        name="Высокое сжатие",
        image_quality=45,
        dpi_threshold=120,
        dpi_target=96,
    ),
}


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_compressed{input_path.suffix}")


def compress_pdf(
    input_path: Path,
    output_path: Path,
    profile: CompressionProfile,
) -> tuple[int, int]:
    """Compress a PDF and return (original_size, compressed_size) in bytes."""
    input_path = input_path.resolve()
    output_path = output_path.resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    if input_path.suffix.lower() != ".pdf":
        raise ValueError("Поддерживаются только PDF-файлы.")

    original_size = input_path.stat().st_size

    doc = fitz.open(input_path)
    try:
        doc.rewrite_images(
            dpi_threshold=profile.dpi_threshold,
            dpi_target=profile.dpi_target,
            quality=profile.image_quality,
        )
        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True,
        )
    finally:
        doc.close()

    compressed_size = output_path.stat().st_size
    return original_size, compressed_size
