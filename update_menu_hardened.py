#!/usr/bin/env python3
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup, Tag

SOURCE = "https://www.glasir.fo/um-skulan/kantinan-a-glasi/"
DAYS = ["Mánadag", "Týsdag", "Mikudag", "Hósdag", "Fríggjadag"]

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "menu.json"
NEXT = ROOT / "menu-next.json"

FAROE_TZ = ZoneInfo("Atlantic/Faroe")
FRIDAY_NEXT_HOUR = 13


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

        text = clean(
            node.get_text(" ", strip=True)
            if isinstance(node, Tag)
            else str(node)
        )

        if text:
            parts.append(text)

    text = clean(" ".join(parts))
    text = re.sub(r"\bDagsins rættur\b", "", text, flags=re.IGNORECASE)
    return clean(text)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def promote_next_menu(now_local: datetime) -> None:
    if now_local.weekday() != 0:
        return

    if not NEXT.exists():
        return

    shutil.copyfile(NEXT, CURRENT)
    NEXT.unlink()

    print("Mánadagur: menu-next.json er flutt til menu.json.")


def output_path_for_time(now_local: datetime) -> Path:
    weekday = now_local.weekday()

    if weekday == 4 and now_local.hour >= FRIDAY_NEXT_HOUR:
        return NEXT

    if weekday in (5, 6):
        return NEXT

    return CURRENT


def fetch_menu() -> dict:
    response = requests.get(
        SOURCE,
        timeout=30,
        headers={
            "User-Agent":
                "Glasir-Matskra-Skermur/1.1 (+https://www.glasir.fo/)"
        },
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

    return {
        "source": SOURCE,
        "updated_at": (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        ),
        "days": result,
    }


def main() -> None:
    now_local = datetime.now(FAROE_TZ)

    print("Føroysk tíð:", now_local.isoformat(timespec="seconds"))

    promote_next_menu(now_local)

    payload = fetch_menu()
    output = output_path_for_time(now_local)

    write_json(output, payload)

    if output == NEXT:
        print("Goymir crawlaðu matskránna sum KOMANDI viku:", NEXT.name)
    else:
        print("Goymir crawlaðu matskránna sum VERANDI viku:", CURRENT.name)

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
