#!/usr/bin/env python3
import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup, Tag

SOURCE = "https://www.glasir.fo/um-skulan/kantinan-a-glasi/"
DAYS = ["Mánadag", "Týsdag", "Mikudag", "Hósdag", "Fríggjadag"]

FAROE_TZ = ZoneInfo("Atlantic/Faroe")
FRIDAY_NEXT_HOUR = 13

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "test-output"
CURRENT = TEST_DIR / "menu.json"
NEXT = TEST_DIR / "menu-next.json"


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


def fetch_real_menu(now_local: datetime, scenario: str) -> dict:
    response = requests.get(
        SOURCE,
        timeout=30,
        headers={
            "User-Agent":
                "Glasir-Matskra-Test/1.0 (+https://www.glasir.fo/)"
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

        result.append({
            "day": day,
            "dish": dish,
        })

    return {
        "test": True,
        "scenario": scenario,
        "test_time": now_local.isoformat(),
        "source": SOURCE,
        "days": result,
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def output_path_for_time(now_local: datetime) -> Path:
    weekday = now_local.weekday()

    if weekday == 4 and now_local.hour >= FRIDAY_NEXT_HOUR:
        return NEXT

    if weekday in (5, 6):
        return NEXT

    return CURRENT


def promote_next_menu(now_local: datetime) -> None:
    if now_local.weekday() != 0:
        return

    if not NEXT.exists():
        print("Mánadagur: eingin menu-next.json at flyta.")
        return

    shutil.copyfile(NEXT, CURRENT)
    NEXT.unlink()

    print("Mánadagur: menu-next.json varð flutt til menu.json.")


def scenario_time(name: str) -> datetime:
    scenarios = {
        "friday_before_13": "2026-08-14T12:00:00+01:00",
        "friday_after_13": "2026-08-14T14:00:00+01:00",
        "saturday": "2026-08-15T12:00:00+01:00",
        "sunday": "2026-08-16T12:00:00+01:00",
        "monday": "2026-08-17T08:00:00+01:00",
    }

    if name == "real_now":
        return datetime.now(FAROE_TZ)

    return datetime.fromisoformat(scenarios[name]).astimezone(FAROE_TZ)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=[
            "real_now",
            "friday_before_13",
            "friday_after_13",
            "saturday",
            "sunday",
            "monday",
        ],
        required=True,
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Slettir test-output áðrenn testið.",
    )
    args = parser.parse_args()

    if args.reset and TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)

    TEST_DIR.mkdir(parents=True, exist_ok=True)

    now_local = scenario_time(args.scenario)

    print("Scenario:", args.scenario)
    print("Føroysk tíð:", now_local.isoformat())

    # Mánadag: flyt fyrst komandi viku til menu.json.
    promote_next_menu(now_local)

    # Crawla veruligu matskránna frá Glasir.
    payload = fetch_real_menu(now_local, args.scenario)
    output = output_path_for_time(now_local)

    write_json(output, payload)

    print("Veruliga Glasir-matskráin varð skrivað til:")
    print(output.relative_to(ROOT))

    print("\nStøða eftir test:")
    print("menu.json:", "FINST" if CURRENT.exists() else "MANGLAR")
    print("menu-next.json:", "FINST" if NEXT.exists() else "MANGLAR")


if __name__ == "__main__":
    main()
