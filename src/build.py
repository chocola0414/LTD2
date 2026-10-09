import json, pathlib
d = pathlib.Path(__file__).parent
rows = json.loads((d / "fighters_wiki.json").read_text(encoding="utf-8"))
NEW = "新單位"
rows += [
 ["Pulsebot",NEW,185,0,"5","Off-tank","Skybot","Impact","Fortified","EMP: Each attack splits its damage among enemies near the target, +10% damage per enemy hit; applies -1% defense (3s, up to 15 stacks).","Melee. Added v12.02 (2025-03)."],
 ["Skybot",NEW,355,540,"5","Off-tank","","Impact","Fortified","EMP: Same as Pulsebot but applies 3 debuff stacks per hit.","Melee. Added v12.02 (2025-03)."],
 ["Crawling Catapult",NEW,265,0,"6","DPS","Wandering Trebuchet","Impact","Fortified","Artillery: Up to +100% damage the further away the target is. Stone Legs: Moves 80% slower.","Long-ranged. Added Season 2025."],
 ["Wandering Trebuchet",NEW,425,690,"6","DPS","","Impact","Fortified","Artillery: Up to +100% damage the further away the target is. Stone Legs: Moves 80% slower.","Long-ranged. Added Season 2025."],
 ["Nucleus","Element",175,265,"1","DPS","","Pure","Immaterial","Ionic Force: +30% attack speed per 10% current mana. Atomic Acceleration: At full mana, every Proton/Atom gains 50% attack speed. Only 1 per board.","Upgrades from Atom. Added v12.04 (2025-05)."],
 ["Pipsqueak",NEW,155,0,"4","DPS","Lumerian","Magic","Swift","","Ranged. Straightforward magic DPS. Added v12.08 (2025-09)."],
 ["Lumerian",NEW,260,415,"4","DPS Carry","","Magic","Swift","Trium of Power: Every 3rd attack deals 0.3% max health magic damage and gains 50 max HP, 1.5% damage reduction and 5% attack speed for the wave. Stacks indefinitely.","Ranged hypercarry. Added v12.08 (2025-09)."],
 ["Scrappy",NEW,90,0,"","DPS","Heroic Scrappy","Impact","Swift","Wind Up (active): Pay 50 gold for +25% attack speed and 15% splash damage this wave. HP 700, DPS 54, range 650.","Long-ranged. Added Season 2026."],
 ["Heroic Scrappy",NEW,190,280,"","DPS","","Impact","Swift","Wind Up (active). HP 2170, DPS 163, range 650.","Added Season 2026."],
 ["Mr. Brewpot",NEW,285,0,"6","Support","Heroic Mr. Brewpot","Impact","Fortified","Alchemy: Throws potions to allies in turn: +50% attack speed, heal 500, +20 mana over 5s. HP 2700, DPS 99, melee.","Added v26.4 (2026-04)."],
 ["Heroic Mr. Brewpot",NEW,415,700,"6","Support","","Impact","Fortified","Grand Alchemy: Throws potions rapidly. HP 6630, DPS 244, melee.","Added v26.4 (2026-04)."],
 ["Rift Trader",NEW,55,0,"","DPS","Heroic Rift Trader","Impact","Swift","Portal of Trash: Attacks cycle 25 / 45 / 65 / 85 damage.","Added v26.8 (2026-08)."],
 ["Heroic Rift Trader",NEW,130,185,"","DPS","","Impact","Swift","Cycle 75 / 140 (+1 gold) / 205 / 265 (stun 1.5s to 0.6s by wave).","Added v26.8 (2026-08)."],
]
for r in rows:
    if r[0] == "Atom": r[6] = "Nucleus"
out = [{"n":r[0],"leg":r[1],"cost":r[2],"val":r[3] or r[2],"tier":r[4],"role":r[5],"up":r[6],"atk":r[7],"def":r[8],"ab":r[9],"note":r[10]} for r in rows]
units = (d.parent / "data" / "units.json").read_text(encoding="utf-8")  # 由 fetch_units.py 產生
html = (d / "ltd2-db.src.html").read_text(encoding="utf-8")
html = html.replace("/*__FIGHTERS__*/[]", json.dumps(out, ensure_ascii=False))
html = html.replace("/*__UNITS__*/{}", units)
# GitHub 版沒有 claude.ai 的共用資料，提示改寫成對應的說法
html = html.replace("本機草稿（共用資料未連線）", "本機草稿（陣容只存在你的瀏覽器）")
html = html.replace("共用資料未連線，派兵紀錄需要登入 claude.ai 開啟這個頁面才能使用。",
                    "這個版本沒有共用資料，派兵紀錄只在 claude.ai 上的版本可以使用。")
HEAD = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
page = HEAD + html.rstrip("\n") + "\n</body></html>"
(d.parent / "index.html").write_text(page, encoding="utf-8", newline="\n")
print(len(out), "fighters", len(page), "bytes -> index.html")
