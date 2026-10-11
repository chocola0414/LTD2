"""Synthetic HTML fixtures test parsing, not game balance values."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("public_stats", Path(__file__).resolve().parents[1] / "src/fetch_public_stats.py")
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


def guide():
    tables = []
    for kind, count in (("Fighter", 100), ("Creature", 21), ("Mercenary", 20)):
        columns = [kind, "HP", "DPS", "Range", "Dmg Type", "Def Type", "Ability 1"]
        if kind == "Creature":
            columns += ["Wave", "Amount"]
        rows = ["<tr>" + "".join(f"<td>{c}</td>" for c in columns) + "</tr>"]
        for i in range(1, count + 1):
            cells = [f'<a href="/units/{kind.lower()}-{i}">{kind} {i}</a>', "1,870", "0" if i == 1 else "53.33",
                     "100", "Pierce", "Swift", "Test &amp; ability"]
            if kind == "Creature":
                cells += [str(i), "8x + Miniboss" if i == 5 else "6x"]
            rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        tables.append("<table><tbody>" + "".join(rows) + "</tbody></table>")
    return "<p>Last updated: <b>26.9</b> (a month ago)</p>" + "".join(tables)


class ImportTests(unittest.TestCase):
    def test_fields_and_zero_dps(self):
        data = stats.parse_guide(guide())
        self.assertEqual(data["version"], "26.9")
        self.assertEqual(len(data["units"]), 141)
        unit = data["units"]["Fighter:fighter 1"]
        self.assertEqual((unit["hp"], unit["dps"], unit["range"]), (1870, 0, 100))
        self.assertEqual(unit["abilityNames"], ["Test & ability"])
        self.assertEqual(data["units"]["Mercenary:mercenary 2"]["dps"], 53.33)

    def test_mixed_wave_not_guessed(self):
        waves = stats.parse_guide(guide())["waves"]
        self.assertIsNone(waves[4]["count"])
        self.assertEqual(waves[4]["countText"], "8x + Miniboss")
        self.assertEqual(waves[12]["count"], 6)

    def test_missing_version_rejected(self):
        with self.assertRaisesRegex(ValueError, "version"):
            stats.parse_guide(guide().replace("Last updated:", "Old page:"))

    def test_invalid_number_or_type_rejected(self):
        for old, new in (("1,870", "NaN"), ("1,870", "-1"), ("53.33", ""), ("Pierce", "Siege")):
            with self.subTest(new=new), self.assertRaises(ValueError):
                stats.parse_guide(guide().replace(f">{old}<", f">{new}<", 1))

    def test_missing_table_and_duplicate_names_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            stats.parse_guide(guide().replace("Mercenary</td>", "Unknown</td>"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            stats.parse_guide(guide().replace("Fighter 2</a>", "Fighter 1</a>"))

    def test_atomic_write_and_no_overwrite_on_serialization_error(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "stats.json"
            stats.write_snapshot({"version": "test"}, target)
            with self.assertRaises(ValueError):
                stats.write_snapshot({"hp": float("nan")}, target)
            self.assertEqual(json.loads(target.read_text()), {"version": "test"})
            self.assertEqual([p.name for p in Path(directory).iterdir()], ["stats.json"])


if __name__ == "__main__":
    unittest.main()
