# Legion TD 2 戰術資料庫

Legion TD 2 的派兵計算機與資料庫，打開 `index.html` 就能使用，不需要安裝任何東西。

## 內容

- **派兵計算**：選波次、輸入對手陣容與秘晶預算，依屬性相剋算出最划算的傭兵與組合，可切換「破防（強力傭兵）」或「漲收入（收入型傭兵）」。
- **戰士**：146 隻戰士的攻擊／護甲類型、成本、能力（含 2025–2026 年新增的 13 隻）。
- **傭兵**：24 隻傭兵的成本、收入、屬性，能力說明對照至 v26.9。
- **波次怪物**：第 1–21 波的屬性與重點。
- **屬性相剋**：攻擊類型 × 護甲類型傷害倍率表。

資料對照至遊戲版本 v26.9（2026 年 9 月）。

## 放上 GitHub Pages

1. 在 GitHub 建立一個 **Public** 儲存庫，例如 `ltd2-db`。
2. 用 **Add file → Upload files** 上傳 `index.html`（檔名不要改），按 **Commit changes**。
3. 到 **Settings → Pages**，Source 選 **Deploy from a branch**，Branch 選 **main**、資料夾 **/(root)**，按 **Save**。
4. 等 1～2 分鐘，網址會是 `https://你的使用者名稱.github.io/ltd2-db/`。

更新時重新上傳同名的 `index.html` 覆蓋即可。

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `index.html` | 網站本體，直接上傳到 GitHub 或用瀏覽器打開 |
| `data/fighters.json` | 戰士資料（146 隻） |
| `src/ltd2-db.src.html` | 頁面原始碼（戰士資料以佔位符代替） |
| `src/fighters_wiki.json` | 取自 wiki 的 133 隻戰士原始資料 |
| `src/build.py` | 把戰士資料與新單位合併、寫入頁面的建置腳本 |

## 限制

- 計算只考慮屬性相剋，沒有模擬單位能力、站位與血量；同名光環不疊加已納入。
- 這個版本的陣容只存在各自的瀏覽器。claude.ai 上的版本另有「共用陣容」與「派兵紀錄」，需要共用資料，GitHub 版本沒有。
- 精確數值以遊戲內 `-info 波次` 指令為準。

## 資料來源

- [Legion TD 2 Wiki](https://legiontd2.wiki.gg/)（CC BY-SA 3.0）
- [Legion TD 2 Steam 更新公告](https://store.steampowered.com/news/app/469600)

Legion TD 2 為 AutoAttack Games 的作品，本專案為玩家自製的非官方工具。
