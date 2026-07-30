#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

SOURCE = "https://www.glasir.fo/um-skulan/kantinan-a-glasi/"
DAYS = ["Mánadag", "Týsdag", "Mikudag", "Hósdag", "Fríggjadag"]
OUTPUT = Path(__file__).resolve().parents[1] / "menu.json"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_day_heading(soup: BeautifulSoup, day: str):
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        if clean(heading.get_text(" ", strip=True)).casefold() == day.casefold():
            return heading
    return None


def extract_dish(heading: Tag) -> str:
    parts = []
    for node in heading.next_siblings:
        if isinstance(node, Tag) and re.fullmatch(r"h[1-6]", node.name or ""):
            break
        if isinstance(node, Tag) and node.name in {"script", "style", "noscript"}:
            continue
        text = clean(node.get_text(" ", strip=True) if isinstance(node, Tag) else str(node))
        if text:
            parts.append(text)
    text = clean(" ".join(parts))
    text = re.sub(r"\bDagsins rættur\b", "", text, flags=re.IGNORECASE)
    return clean(text)


def main() -> None:
    response = requests.get(
        SOURCE,
        timeout=30,
        headers={"User-Agent": "Glasir-Matskra-Skermur/1.0 (+https://www.glasir.fo/)"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    result = []
    for day in DAYS:
        heading = find_day_heading(soup, day)
        if heading is None:
            raise RuntimeError(f"Fann ikki yvirskriftina: {day}")
        dish = extract_dish(heading)
        if not dish:
            dish = "Eingin rættur er skrásettur"
        result.append({"day": day, "dish": dish})

    payload = {
        "source": SOURCE,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "days": result,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
