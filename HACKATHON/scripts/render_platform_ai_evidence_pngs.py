#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evidence" / "platform_ai_engineering" / "raw"
OUT = ROOT / "evidence" / "platform_ai_engineering" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

W = 1800
PAD = 56
BG = "#07111f"
PANEL = "#0b1628"
PANEL_STROKE = "#27405f"
CYAN = "#67e8f9"
WHITE = "#f8fafc"
TEXT = "#dbeafe"
MUTED = "#9fb0c7"
GREEN = "#86efac"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for item in candidates:
        try:
            return ImageFont.truetype(item, size)
        except Exception:
            pass
    return ImageFont.load_default()


F_TITLE = font(44, True)
F_H = font(28, True)
F_BODY = font(24)
F_MONO = font(20)
F_SMALL = font(18)


def read(name: str, max_lines: int) -> list[str]:
    path = RAW / f"{name}.txt"
    lines = path.read_text(errors="replace").splitlines()
    return lines[:max_lines]


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], fnt, fill: str, width_chars: int, line_gap: int = 8) -> int:
    x, y = xy
    for para in text.split("\n"):
        wrapped = textwrap.wrap(para, width=width_chars) or [""]
        for line in wrapped:
            draw.text((x, y), line, font=fnt, fill=fill)
            y += fnt.size + line_gap
    return y


def render(name: str, title: str, subtitle: str, blocks: list[tuple[str, list[str]]]) -> None:
    block_heights = []
    for _, lines in blocks:
        block_heights.append(70 + len(lines) * 25)
    height = 170 + sum(block_heights) + len(blocks) * 34 + 90
    img = Image.new("RGB", (W, height), BG)
    d = ImageDraw.Draw(img)
    y = PAD
    d.text((PAD, y), title, font=F_TITLE, fill=WHITE)
    y += 60
    y = draw_wrapped(d, subtitle, (PAD, y), F_BODY, MUTED, 100)
    y += 28

    for heading, lines in blocks:
        d.rounded_rectangle((PAD, y, W - PAD, y + 54), radius=12, fill="#10243a", outline="#0ea5e9", width=2)
        d.text((PAD + 22, y + 12), heading, font=F_H, fill=CYAN)
        y += 72
        h = len(lines) * 25 + 30
        d.rounded_rectangle((PAD, y, W - PAD, y + h), radius=14, fill=PANEL, outline=PANEL_STROKE, width=2)
        yy = y + 18
        for line in lines:
            color = GREEN if "passed" in line.lower() or "ok=true" in line.lower() or "assert" in line else TEXT
            d.text((PAD + 22, yy), line[:170], font=F_MONO, fill=color)
            yy += 25
        y += h + 36

    out_path = OUT / f"{name}.png"
    img.save(out_path)
    print(out_path)


render(
    "01_backend_consumer_api_evidence",
    "Evidence 01 - Backend Consumes AI DecisionEvent",
    "This screenshot is rendered from real command output. It shows the canonical DecisionEvent schema and the Backend /api/v1/alerts boundary that consumes it.",
    [
        ("DecisionEvent schema", read("01_decision_event_schema", 55)),
        ("Backend API boundary", read("02_ai_backend_boundary_router", 90)),
    ],
)

render(
    "02_carsky_consumer_mapper_evidence",
    "Evidence 02 - CarSky Integration Consumes AI/DMS State",
    "This screenshot shows the mapper and scenario script that convert AI/DMS state into CarSky Vehicle.Speed speed-mux transport.",
    [
        ("CarSkySignalMapper", read("03_backend_to_carsky_mapper", 115)),
        ("carsky_phase05 scenario script", read("04_carsky_phase05_script", 80)),
    ],
)

render(
    "03_copilot_report_export_evidence",
    "Evidence 03 - Report User Consumes AI Explanation Artifact",
    "This screenshot shows /api/copilot/report and Word/DOC export source, proving report capability is consumed through API/artifact.",
    [
        ("Copilot report API", read("05_copilot_report_api", 95)),
        ("Word/DOC export", read("06_copilot_doc_export", 90)),
    ],
)

render(
    "04_tests_apk_artifact_evidence",
    "Evidence 04 - Tests And Android HMI Artifact",
    "This screenshot shows the contract/alerts/CarSky tests passing and APK artifact strings for Android CarProperty/HMI integration.",
    [
        ("Pytest result", read("10_pytest_contract_carsky_alerts", 45)),
        ("APK artifact and runtime strings", read("11_apk_hmi_artifact", 35)),
    ],
)
