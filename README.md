# Legion TD 2 戰術資料庫

Legion TD 2 的派兵計算機與資料庫，打開 `index.html` 就能使用，不需要安裝任何東西。

## 內容

- **派兵計算**：選波次、輸入對手陣容與秘晶預算，依屬性相剋算出最划算的傭兵與組合，可切換「破防（強力傭兵）」或「漲收入（收入型傭兵）」。
- **戰士**：146 隻戰士的攻擊／護甲類型、成本、能力（含 2025–2026 年新增的 13 隻）。
- **傭兵**：24 隻傭兵的成本、收入、屬性，能力說明對照至 v26.9。
- **波次怪物**：第 1–21 波的屬性與重點。
- **屬性相剋**：攻擊類型 × 護甲類型傷害倍率表。
- **對局復盤**：貼上對局 ID（或含 ID 的網址），從官方 API 撈資料，逐波顯示四位玩家的佈陣、戰士價值、工人、收入、淨值、送出／收到的傭兵、漏怪 % 與雙方王血。目前支援 2v2 排位；原則判斷的位置先留空。

資料對照至遊戲版本 v26.9（2026 年 9 月）。

## 放上 GitHub Pages

1. 在 GitHub 建立一個 **Public** 儲存庫，例如 `ltd2-db`。
2. 用 **Add file → Upload files** 上傳 `index.html`（檔名不要改），按 **Commit changes**。
3. 到 **Settings → Pages**，Source 選 **Deploy from a branch**，Branch 選 **main**、資料夾 **/(root)**，按 **Save**。
4. 等 1～2 分鐘，網址會是 `https://你的使用者名稱.github.io/ltd2-db/`。

更新時重新上傳同名的 `index.html` 覆蓋即可。

## 修改頁面

`index.html` 由腳本產生，不要直接改它：

1. 改 `src/ltd2-db.src.html`。
2. 執行 `python src/build.py`，產出新的 `index.html`。
3. 遊戲改版後，先設定環境變數 `LTD2_API_KEY`，執行 `python src/fetch_units.py 單位版本`（例如 `26.9.hf3`）更新 `data/units.json`，再跑第 2 步。

## 對局復盤的 API 代理

官方規定 API key 不能放在網頁裡，所以復盤分頁經 `worker/` 的 Cloudflare Worker 轉送。key 存在 Worker 的 secret，只接受本站網址與本機開啟的頁面。改 Worker 後在 `worker/` 執行 `npx wrangler deploy`；換 key 用 `npx wrangler secret put LTD2_API_KEY`。

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `index.html` | 網站本體，直接上傳到 GitHub 或用瀏覽器打開 |
| `data/fighters.json` | 戰士資料（146 隻） |
| `data/units.json` | 官方單位清單與波次賞金（復盤分頁用，由 `fetch_units.py` 產生） |
| `src/ltd2-db.src.html` | 頁面原始碼（戰士與單位資料以佔位符代替） |
| `src/fighters_wiki.json` | 取自 wiki 的 133 隻戰士原始資料 |
| `src/build.py` | 合併戰士資料與新單位、注入單位資料，產出 `index.html` 的建置腳本 |
| `src/fetch_units.py` | 從官方 API 抓單位與波次資料的腳本 |
| `worker/` | 對局復盤用的 Cloudflare Worker（API 代理） |

## 限制

- 計算只考慮屬性相剋，沒有模擬單位能力、站位與血量；同名光環不疊加已納入。
- 這個版本的陣容只存在各自的瀏覽器。claude.ai 上的版本另有「共用陣容」與「派兵紀錄」，需要共用資料，GitHub 版本沒有。
- 精確數值以遊戲內 `-info 波次` 指令為準。
- 對局復盤只查得到一年內的對局；官方 API key 每天上限 1,000 次，由所有使用者共用。

## 資料來源

- [Legion TD 2 Wiki](https://legiontd2.wiki.gg/)（CC BY-SA 3.0）
- [Legion TD 2 Steam 更新公告](https://store.steampowered.com/news/app/469600)
- [Legion TD 2 官方 API](https://swagger.legiontd2.com/)

Legion TD 2 為 AutoAttack Games 的作品，本專案為玩家自製的非官方工具。
