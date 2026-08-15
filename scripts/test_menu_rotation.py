#!/usr/bin/env python3
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FAROE_TZ = ZoneInfo("Atlantic/Faroe")
FRIDAY_NEXT_HOUR = 13

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "test-output"
CURRENT = TEST_DIR / "menu.json"
NEXT = TEST_DIR / "menu-next.json"


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
    # Fastar testtíðir í føroyskari tíð.
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


def make_payload(now_local: datetime, scenario: str) -> dict:
    return {
        "test": True,
        "scenario": scenario,
        "test_time": now_local.isoformat(),
        "days": [
            {"day": "Mánadag", "dish": "TEST mánadag"},
            {"day": "Týsdag", "dish": "TEST týsdag"},
            {"day": "Mikudag", "dish": "TEST mikudag"},
            {"day": "Hósdag", "dish": "TEST hósdag"},
            {"day": "Fríggjadag", "dish": "TEST fríggjadag"},
        ],
    }


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

    # Mánadag skal fyrst flyta menu-next.json til menu.json.
    promote_next_menu(now_local)

    payload = make_payload(now_local, args.scenario)
    output = output_path_for_time(now_local)

    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Skrivaði til:", output.relative_to(ROOT))

    print("\nStøða eftir test:")
    print("menu.json:", "FINST" if CURRENT.exists() else "MANGLAR")
    print("menu-next.json:", "FINST" if NEXT.exists() else "MANGLAR")


if __name__ == "__main__":
    main()
