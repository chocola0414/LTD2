"""從官方 API 抓單位與波次資料，精簡成 data/units.json，給復盤分頁對照單位 ID、圖示、賞金用。

API key 不能進 repo：執行前設環境變數 LTD2_API_KEY。
用法：python src/fetch_units.py [單位版本]   # 版本格式如 26.9.hf3（用 v26.9 會 502）
改版後重跑一次，再跑 build.py。
"""
import json, os, pathlib, sys, urllib.request

API = "https://apiv2.legiontd2.com"
KEY = os.environ.get("LTD2_API_KEY") or sys.exit("請先設定環境變數 LTD2_API_KEY")
VERSION = sys.argv[1] if len(sys.argv) > 1 else "26.9.hf3"
OUT = pathlib.Path(__file__).parent.parent / "data" / "units.json"


def get(path):
    req = urllib.request.Request(API + path, headers={"x-api-key": KEY, "User-Agent": "ltd2-db"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def num(s):
    try:
        return float(s) if "." in str(s) else int(s)
    except (TypeError, ValueError):
        return 0


# 不加 enabled=true：遊戲內實際會出現的單位有些被標成 disabled
units = get(f"/units/byVersion/{VERSION}?limit=300")
keep = {"Fighter", "Mercenary", "Creature"}
slim = {}
for u in units:
    if u.get("unitClass") not in keep:
        continue
    slim[u["unitId"]] = {
        "n": u["name"],
        "i": pathlib.PurePosixPath(u.get("iconPath") or "").name,
        "c": u["unitClass"],
        "v": num(u.get("totalValue")),
        "m": num(u.get("mythiumCost")),
        "b": num(u.get("goldBounty")),
    }

waves = sorted(get("/info/waves/0/30"), key=lambda w: int(w["levelNum"]))
reward = [num(w["totalReward"]) for w in waves if int(w["levelNum"]) > 0]

OUT.write_text(json.dumps({"version": VERSION, "units": slim, "waveReward": reward},
                          ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(len(slim), "units,", len(reward), "waves ->", OUT)
