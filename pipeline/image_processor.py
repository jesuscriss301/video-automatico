"""
Valida y prepara las imágenes de cada escena.

Lo importante aquí: si vas a aplicar Ken Burns (zoom lento), la imagen fuente
necesita más resolución que la de salida, si no el zoom la pixela. Este
módulo revisa eso y, si la imagen es muy pequeña, aplica un upscaling básico
(Lanczos, con Pillow) como red de seguridad — no es tan bueno como un
upscaler con IA, pero evita que el video salga notoriamente borroso.

Hay un "hook" (`upscale_with_real_esrgan`) listo para conectar Real-ESRGAN
más adelante si se necesita mejor calidad en imágenes realmente pequeñas.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

from config.settings import DEFAULTS


class ImageProcessorError(RuntimeError):
    pass


def ensure_quality(image_path: str | Path, work_dir: Path, scene_id: str) -> Path:
    src = Path(image_path)
    if not src.exists():
        raise ImageProcessorError(f"No existe la imagen: {src}")

    with Image.open(src) as img:
        width, height = img.size

    target_w = DEFAULTS.video.width
    target_h = DEFAULTS.video.height
    min_scale = DEFAULTS.min_source_scale

    needed_w = int(target_w * min_scale)
    needed_h = int(target_h * min_scale)

    if width >= needed_w and height >= needed_h:
        # Ya tiene resolución de sobra, se usa tal cual.
        return src

    upscaled_path = work_dir / f"{scene_id}.upscaled.png"
    work_dir.mkdir(parents=True, exist_ok=True)

    if _real_esrgan_available():
        return upscale_with_real_esrgan(src, upscaled_path, needed_w, needed_h)

    return _upscale_lanczos(src, upscaled_path, needed_w, needed_h)


def _upscale_lanczos(src: Path, dst: Path, needed_w: int, needed_h: int) -> Path:
    with Image.open(src) as img:
        img = img.convert("RGB")
        scale = max(needed_w / img.width, needed_h / img.height)
        new_size = (int(img.width * scale) + 1, int(img.height * scale) + 1)
        resized = img.resize(new_size, Image.LANCZOS)
        resized.save(dst)
    return dst


def _real_esrgan_available() -> bool:
    # Hook para el futuro: si el binario/paquete de Real-ESRGAN está instalado,
    # se usa automáticamente en vez del fallback simple de Pillow.
    return shutil.which("realesrgan-ncnn-vulkan") is not None


def upscale_with_real_esrgan(src: Path, dst: Path, needed_w: int, needed_h: int) -> Path:  # pragma: no cover
    import subprocess

    cmd = ["realesrgan-ncnn-vulkan", "-i", str(src), "-o", str(dst)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Si falla, no se rompe el pipeline: se cae al método simple.
        return _upscale_lanczos(src, dst, needed_w, needed_h)
    return dst


def crop_to_aspect(src: Path, dst: Path, target_w: int, target_h: int) -> Path:
    """Recorta al centro para que la imagen tenga exactamente el aspect ratio
    de salida antes de aplicar Ken Burns (evita franjas negras o deformación)."""
    with Image.open(src) as img:
        img = img.convert("RGB")
        target_ratio = target_w / target_h
        w, h = img.size
        current_ratio = w / h

        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            box = (left, 0, left + new_w, h)
        else:
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            box = (0, top, w, top + new_h)

        cropped = img.crop(box)
        cropped.save(dst)
    return dst
