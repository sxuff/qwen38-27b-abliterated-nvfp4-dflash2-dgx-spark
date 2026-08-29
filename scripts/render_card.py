#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
summary = json.loads((ROOT / "results/summary.json").read_text())
base = summary["arms"]["no-spec"]["median_end_to_end_completion_tokens_per_second"]
fast = summary["arms"]["dflash2"]["median_end_to_end_completion_tokens_per_second"]
ratio = summary["paired"]["aggregate_median_speed_ratio"]
rows = summary["paired"]["performance_rows"]

W, H = 1600, 900
img = Image.new("RGB", (W, H), "#07111f")
draw = ImageDraw.Draw(img)
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(path: str, size: int):
    return ImageFont.truetype(path, size)

def text(x: int, y: int, value: str, face, fill: str):
    draw.text((x, y), value, font=face, fill=fill)

draw.rounded_rectangle((90, 80, 1510, 820), radius=28, fill="#0b1829", outline="#21344c", width=2)
draw.rectangle((90, 80, 106, 820), fill="#55e6a5")
text(150, 130, "Qwen3.8-27B · ARA ABLITERATED · NVFP4", font(bold, 45), "#f5f8fc")
text(150, 194, "1× NVIDIA DGX Spark · SGLang", font(regular, 30), "#9fb0c6")
draw.line((150, 260, 1450, 260), fill="#263b55", width=2)
text(180, 330, "NO SPEC", font(bold, 26), "#8294aa")
text(180, 382, f"{base:.2f}", font(bold, 116), "#f5f8fc")
text(190, 510, "TOK/S", font(bold, 30), "#8294aa")
text(885, 330, "DFLASH2", font(bold, 26), "#55e6a5")
text(885, 382, f"{fast:.2f}", font(bold, 116), "#55e6a5")
text(895, 510, "TOK/S", font(bold, 30), "#55e6a5")
draw.line((800, 320, 800, 570), fill="#263b55", width=2)
text(595, 610, f"{ratio:.2f}×", font(bold, 76), "#f5f8fc")
text(495, 690, "FROZEN QUALIFICATION: NO-GO", font(bold, 30), "#ff9b85")
text(150, 755, f"{rows} paired performance rows · 3 reps × 6 fixtures · whole-request completion rate", font(regular, 25), "#9fb0c6")
out = ROOT / "assets/qwen38-abliterated-dflash2-result.png"
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out, optimize=True)
print(out, img.size)
