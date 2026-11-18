"""Watermark style defaults and persistence."""

import json
import os
import re
import sys
import tempfile
from copy import deepcopy
from pathlib import Path


if getattr(sys, "frozen", False):
    WATERMARK_STYLE_PATH = (
        Path(os.environ.get("APPDATA") or Path.home())
        / "webcamSnapshot"
        / "watermark.json"
    )
else:
    WATERMARK_STYLE_PATH = (
        Path(__file__).resolve().parent.parent / "config" / "watermark.json"
    )

DEFAULT_WATERMARK_STYLE = {
    "text": "{filename}",
    "font": "FONT_HERSHEY_SIMPLEX",
    "font_scale": 1.0,
    "color": "#FFFFFF",
    "outline_color": "#000000",
    "position": "top_left",
    "margin": 2,
}

FONT_OPTIONS = {
    "简单": "FONT_HERSHEY_SIMPLEX",
    "普通": "FONT_HERSHEY_PLAIN",
    "复杂": "FONT_HERSHEY_COMPLEX",
    "手写": "FONT_HERSHEY_SCRIPT_SIMPLEX",
}

POSITION_OPTIONS = {
    "左上": "top_left",
    "居中上": "top_center",
    "右上": "top_right",
    "左侧居中": "middle_left",
    "居中": "middle_center",
    "右侧居中": "middle_right",
    "左下": "bottom_left",
    "居中下": "bottom_center",
    "右下": "bottom_right",
}


def normalize_watermark_style(style=None):
    """Return a validated watermark style with defaults filled in."""
    if style is None:
        return deepcopy(DEFAULT_WATERMARK_STYLE)
    if not isinstance(style, dict):
        raise ValueError("水印样式必须是对象")

    result = deepcopy(DEFAULT_WATERMARK_STYLE)
    result.update({
        key: value
        for key, value in style.items()
        if key in result
    })
    if result["position"] == "center":
        result["position"] = "middle_center"

    if not isinstance(result["text"], str) or len(result["text"]) > 300:
        raise ValueError("水印文字长度不能超过 300 个字符")
    if result["font"] not in FONT_OPTIONS.values():
        raise ValueError("水印字体无效")
    if (
        isinstance(result["font_scale"], bool)
        or not isinstance(result["font_scale"], (int, float))
        or not 0.1 <= result["font_scale"] <= 5
    ):
        raise ValueError("水印字号比例必须在 0.1 到 5 之间")
    for key in ("color", "outline_color"):
        if not isinstance(result[key], str) or not re.fullmatch(
            r"#[0-9a-fA-F]{6}", result[key]
        ):
            raise ValueError(f"{key} 必须是 #RRGGBB 格式的颜色")
    if result["position"] not in POSITION_OPTIONS.values():
        raise ValueError("水印位置无效")
    if (
        isinstance(result["margin"], bool)
        or not isinstance(result["margin"], int)
        or not 0 <= result["margin"] <= 20
    ):
        raise ValueError("水印边距必须在 0 到 20 之间")
    return result


def load_watermark_style(path=WATERMARK_STYLE_PATH):
    """Load persisted style, or return defaults when no settings exist."""
    if not path.exists():
        return normalize_watermark_style()
    with path.open("r", encoding="utf-8") as settings_file:
        return normalize_watermark_style(json.load(settings_file))


def save_watermark_style(style, path=WATERMARK_STYLE_PATH):
    """Atomically save a validated watermark style."""
    validated_style = normalize_watermark_style(style)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as settings_file:
            temporary_path = Path(settings_file.name)
            json.dump(validated_style, settings_file, ensure_ascii=False, indent=2)
            settings_file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return validated_style
