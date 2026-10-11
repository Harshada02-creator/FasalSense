"""Quick, dependency-light verification for the FasalSense handoff starter."""
from __future__ import annotations

import ast
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "app"
DATA = ROOT / "data"


def main() -> int:
    errors: list[str] = []

    for path in sorted(APP.glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"Python syntax error in {path.relative_to(ROOT)}: {exc}")

    json_path = DATA / "crop_catalogue_seed.json"
    csv_path = DATA / "crop_catalogue_seed.csv"
    try:
        catalogue = json.loads(json_path.read_text(encoding="utf-8"))
        if len(catalogue) != 16:
            errors.append(f"Expected 16 starter catalogue entries, found {len(catalogue)}")
        names = [entry.get("name") for entry in catalogue]
        if len(names) != len(set(names)):
            errors.append("Duplicate crop names in JSON seed catalogue")
    except Exception as exc:  # report as a friendly preflight issue
        errors.append(f"Could not validate JSON crop catalogue: {exc}")

    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 16:
            errors.append(f"Expected 16 CSV starter catalogue entries, found {len(rows)}")
    except Exception as exc:
        errors.append(f"Could not validate CSV crop catalogue: {exc}")

    if errors:
        print("FasalSense verification found problems:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("FasalSense handoff preflight passed.")
    print(" - Python files parse successfully.")
    print(" - JSON and CSV seed catalogues each contain 16 entries.")
    print(" - This check does not prove routes, business logic, deployment, or security are correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
