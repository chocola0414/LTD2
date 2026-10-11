"""Import factual combat stats from the public official guide, without an API key.

python3 src/fetch_public_stats.py
python3 src/fetch_public_stats.py --html /path/to/downloaded-guide.html
The separate snapshot does not relabel/overwrite versioned API replay metadata.
"""
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import tempfile
import urllib.request

URL = "https://beta.legiontd2.com/guide/units/"
OUT = Path(__file__).resolve().parent.parent / "data" / "combat_stats.json"
ATTACKS = {"Pierce", "Impact", "Magic", "Pure"}
ARMORS = {"Swift", "Natural", "Fortified", "Arcane", "Immaterial"}


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.text = [], []
        self.table = self.row = self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = {"text": "", "links": []}
        elif tag == "a" and self.cell is not None and attrs.get("href", "").startswith("/units/"):
            self.cell["links"].append(attrs["href"])

    def handle_data(self, data):
        self.text.append(data)
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.cell["text"] = " ".join(self.cell["text"].split())
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def numeric(text, field, name):
    try:
        value = float(text.replace(",", ""))
    except ValueError:
        raise ValueError(f"Invalid {field} for {name}: {text!r}") from None
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid {field} for {name}")
    return int(value) if value.is_integer() else value


def parse_guide(html):
    parser = Tables()
    parser.feed(html)
    version = re.search(r"Last updated:\s*(\d+\.\d+(?:\.[A-Za-z0-9]+)*)", " ".join(parser.text))
    if not version:
        raise ValueError("Official guide version label missing")
    units, waves = {}, []
    for table in parser.tables:
        if not table:
            continue
        headers = [cell["text"] for cell in table[0]]
        kind = next((k for k in ("Fighter", "Creature", "Mercenary") if k in headers), None)
        if not kind:
            continue
        for cells in table[1:]:
            if len(cells) != len(headers):
                raise ValueError("Unexpected guide table shape")
            row = dict(zip(headers, cells))
            name = row[kind]["text"]
            key = f"{kind}:{name.casefold()}"
            if key in units:
                raise ValueError(f"Ambiguous duplicate unit: {key}")
            stats = {field: numeric(row[column]["text"], field, name)
                     for field, column in (("hp", "HP"), ("dps", "DPS"), ("range", "Range"))}
            if stats["hp"] <= 0:
                raise ValueError(f"Nonpositive HP: {name}")
            attack, armor = row["Dmg Type"]["text"], row["Def Type"]["text"]
            if attack not in ATTACKS or armor not in ARMORS:
                raise ValueError(f"Unknown attack/armor type: {name}")
            links = row[kind]["links"]
            if len(links) != 1:
                raise ValueError(f"Missing/ambiguous unit source link: {name}")
            unit = {"name": name, "class": kind, **stats, "atk": attack, "def": armor,
                    "url": "https://beta.legiontd2.com" + links[0],
                    "abilityNames": [row[col]["text"] for col in headers
                                     if col.startswith("Ability ") and row[col]["text"]]}
            units[key] = unit
            if kind == "Creature":
                amount = row["Amount"]["text"]
                match = re.fullmatch(r"(\d+)x", amount)
                # Mixed spawns must not be silently reduced to the first count.
                count = int(match[1]) if match else None
                waves.append({"wave": numeric(row["Wave"]["text"], "wave", name),
                              "unitKey": key, "count": count, "countText": amount})
    counts = {kind: sum(u["class"] == kind for u in units.values())
              for kind in ("Fighter", "Creature", "Mercenary")}
    if counts["Fighter"] < 100 or counts["Mercenary"] < 20 or counts["Creature"] < 21:
        raise ValueError(f"Guide appears incomplete: {counts}")
    if sorted(w["wave"] for w in waves) != list(range(1, 22)):
        raise ValueError("Expected exactly waves 1–21")
    return {"version": version[1], "source": URL,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "precision": "DPS as displayed in guide (rounded); not inferred from attack speed",
            "limitations": "Base stats; no skills, buffs, positioning or hotfix-version guarantee",
            "units": units, "waves": sorted(waves, key=lambda w: w["wave"]), "counts": counts}


def write_snapshot(data, output=OUT):
    content = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    output = Path(output)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                         prefix=".combat-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        temporary.replace(output)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="Parse an already downloaded official guide")
    args = parser.parse_args()
    try:
        if args.html:
            html = args.html.read_text(encoding="utf-8")
        else:
            req = urllib.request.Request(URL, headers={"User-Agent": "ltd2-db-stats-importer"})
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode("utf-8")
        data = parse_guide(html)
        write_snapshot(data)
        print(f"Official guide {data['version']}: {data['counts']} -> {OUT}")
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Import failed; existing snapshot unchanged: {exc}\n")


if __name__ == "__main__":
    main()
