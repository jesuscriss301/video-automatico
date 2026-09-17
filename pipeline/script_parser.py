"""Carga y valida el guion desde un archivo JSON."""
from __future__ import annotations

import json
from pathlib import Path

from pipeline.models import Script


def load_script(path: str | Path) -> Script:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el guion: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    script = Script.model_validate(data)

    if not script.scenes:
        raise ValueError("El guion no tiene escenas.")

    base_dir = path.parent
    for scene in script.scenes:
        img = Path(scene.image_path)
        if not img.is_absolute():
            scene.image_path = str((base_dir / img).resolve())

    if script.background_music:
        music = Path(script.background_music)
        if not music.is_absolute():
            script.background_music = str((base_dir / music).resolve())

    return script
