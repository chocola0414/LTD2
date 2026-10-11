# Legion TD 2 戰術資料庫

Legion TD 2 的派兵計算機與資料庫，打開 `index.html` 就能使用，不需要安裝任何東西。

## 內容

- **派兵計算**：選波次、輸入對手陣容與秘晶預算，依屬性相剋算出最划算的傭兵與組合，可切換「破防（強力傭兵）」或「漲收入（收入型傭兵）」。
- **戰士**：146 隻戰士的攻擊／護甲類型、成本、能力（含 2025–2026 年新增的 13 隻）。
- **傭兵**：24 隻傭兵的成本、收入、屬性，能力說明對照至 v26.9。
- **波次怪物**：第 1–21 波的屬性與重點。
- **屬性相剋**：攻擊類型 × 護甲類型傷害倍率表。
- **對策筆記與強度比較**：選定波次後，可在戰士／傭兵圖鑑看屬性調整後的攻擊效率、存活效率，以及加入傭兵前後的差異；部分能力型對策（例如 Berserker 對高生命值單體）會另外標註。
- **對局復盤**：貼上對局 ID（或含 ID 的網址），從官方 API 撈資料，逐波顯示四位玩家的佈陣、戰士價值、工人、收入、淨值、送出／收到的傭兵、漏怪 % 與雙方王血。目前支援 2v2 排位；原則判斷的位置先留空。

資料對照至遊戲版本 v26.9（2026 年 9 月）。

## 復盤操作

- 右鍵點玩家佈陣（或聚焦佈陣後按 Enter），可把當波單位、數量及該玩家**收到**的傭兵秘晶總額載入派兵計算的本機草稿。沒有收到傭兵時保留 0。
- 強度比較與下方四位玩家使用同一個四欄版面；窄螢幕可一起左右捲動。
- 每位玩家只顯示「基礎波次」與「波次＋收到」兩個估計戰力，並顯示相對原始戰士價值的正負差額與百分比。
- 懸停、點擊或用 Tab 聚焦數字，可查看 HP／DPS、攻防倍率及計算公式。這是相剋修正值，不是守住機率；缺基本屬性時顯示「資料不足」，缺完整戰鬥數值時明示「屬性備援」。

修改後執行 `python3 src/build.py`，再執行 `node tests/replay-ui.cjs`，驗證復盤匯入與強度比較的離線回歸測試。

## 不需要 API key 的戰鬥數值更新

`data/combat_stats.json` 取自[官方公開單位表](https://beta.legiontd2.com/guide/units/)，目前包含 147 戰士、21 波次怪物、25 傭兵的 HP、表列 DPS、射程、攻擊／護甲與技能名稱。表列 DPS 已四捨五入，不自行猜測攻速或每擊傷害。圖鑑可直接查看 HP／DPS／射程及來源連結。

```sh
python3 src/fetch_public_stats.py
python3 src/build.py
node tests/replay-ui.cjs
python3 -B -m unittest discover -s tests -p 'test_*.py'
```

也可用 `python3 src/fetch_public_stats.py --html /path/to/downloaded-guide.html` 匯入已下載的官方表。匯入會檢查欄位、數量與版本標籤；失敗不覆蓋原快照。

- 來源標示 **26.9**；原 `data/units.json` 是 **26.9.hf3** 的單位 ID／賞金資料，兩份分開保留。公開表不保證符合該 hotfix 或較舊對局。
- 復盤資料完整時，每個戰士的攻擊倍率依敵方總 HP 加權，承傷倍率依敵方總 DPS 加權；全隊以各自 DPS／HP 計算有效 DPS／有效 HP。相剋係數 = `√[(有效 DPS / 原始 DPS) × (有效 HP / 原始 HP)]`，主數字仍為原始戰士價值乘此係數。
- Tooltip 另列 `√(有效 HP × 有效 DPS / 敵方總 HP / 敵方總 DPS)` 的靜態比值，以區分增加同屬性傭兵造成的總量壓力。**不是漏怪率、勝率或戰鬥模擬**。
- 缺資料不猜值：目前 Heroic Scrappy、Mr. Brewpot、Heroic Mr. Brewpot、Heroic Rift Trader 沒有精確名稱匹配；W5／15／21 的公開表沒有完整小王數值，這些情境退回明示的舊屬性估計。
- 技能附加傷害、光環、召喚、變身與站位仍未數值模擬；例如 Berserker 的魔法疊傷不包含在基礎 DPS 指數中。派兵計算的組合排序及圖鑑的屬性百分比仍使用原有屬性模型。

## 放上 GitHub Pages

1. 在 GitHub 建立一個 **Public** 儲存庫，例如 `ltd2-db`。
2. 用 **Add file → Upload files** 上傳 `index.html`（檔名不要改），按 **Commit changes**。
3. 到 **Settings → Pages**，Source 選 **Deploy from a branch**，Branch 選 **main**、資料夾 **/(root)**，按 **Save**。
4. 等 1～2 分鐘，網址會是 `https://你的使用者名稱.github.io/ltd2-db/`。

更新時重新上傳同名的 `index.html` 覆蓋即可。

## 修改頁面

`index.html` 由腳本產生，不要直接改它：

1. 改 `src/ltd2-db.src.html`。
2. 執行 `python3 src/build.py`，產出新的 `index.html`。
3. 更新公開戰鬥數值不需 key，見上節。要更新 API 的 ID／賞金資料，設定環境變數 `LTD2_API_KEY`，執行 `python3 src/fetch_units.py 單位版本`（例如 `26.9.hf3`）更新 `data/units.json`，再跑第 2 步。

## 對局復盤的 API 代理

官方規定 API key 不能放在網頁裡，所以復盤分頁經 `worker/` 的 Cloudflare Worker 轉送。key 存在 Worker 的 secret，只接受本站網址與本機開啟的頁面。改 Worker 後在 `worker/` 執行 `npx wrangler deploy`；換 key 用 `npx wrangler secret put LTD2_API_KEY`。

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `index.html` | 網站本體，直接上傳到 GitHub 或用瀏覽器打開 |
| `data/fighters.json` | 戰士資料（146 隻） |
| `data/units.json` | 官方單位清單與波次賞金（復盤分頁用，由 `fetch_units.py` 產生） |
| `data/combat_stats.json` | 無 key 的官方公開表戰鬥數值快照，含版本、來源、時間與波次数量 |
| `data/matchup_notes.json` | 能力型對策筆記，供圖鑑、波次與復盤分析共用 |
| `src/ltd2-db.src.html` | 頁面原始碼（戰士與單位資料以佔位符代替） |
| `src/fighters_wiki.json` | 取自 wiki 的 133 隻戰士原始資料 |
| `src/build.py` | 合併戰士資料與新單位、注入單位資料，產出 `index.html` 的建置腳本 |
| `src/fetch_units.py` | 從官方 API 抓單位與波次資料的腳本 |
| `src/fetch_public_stats.py` | 不需 API key，擷取及驗證官方公開表的 HP／DPS／射程 |
| `worker/` | 對局復盤用的 Cloudflare Worker（API 代理） |

## 限制

- 派兵組合排序只考慮屬性相剋，沒有戰鬥模擬；同名光環不疊加僅為組合限制。
- 復盤納入公開 HP／DPS 作相剋權重，但仍不是完整戰鬥模擬；技能對策以筆記顯示，不能把普攻 DPS 當成技能型單位的完整輸出。
- 這個版本的陣容只存在各自的瀏覽器。claude.ai 上的版本另有「共用陣容」與「派兵紀錄」，需要共用資料，GitHub 版本沒有。
- 精確數值以遊戲內 `-info 波次` 指令為準。
- 對局復盤只查得到一年內的對局；官方 API key 每天上限 1,000 次，由所有使用者共用。

## 資料來源

- [Legion TD 2 Wiki](https://legiontd2.wiki.gg/)（CC BY-SA 3.0）
- [Legion TD 2 Steam 更新公告](https://store.steampowered.com/news/app/469600)
- [Legion TD 2 官方 API](https://swagger.legiontd2.com/)

Legion TD 2 為 AutoAttack Games 的作品，本專案為玩家自製的非官方工具。
