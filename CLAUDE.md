# Fable Protocol Kit — 專案指示

本專案是「讓 Opus/Sonnet/Haiku 以 Fable 5 的操作模式工作」的行為協議套件（hooks + skill + agents）。
行為協議本體由 SessionStart hook 注入（`.claude/hooks/fable_protocol.md`），此處只放模型分工、不可妥協守則、治理文件路由與專案守則。

## 模型分工（Model Routing）— 委派子代理時強制遵守

模型分工表**以 `.claude/hooks/fable_protocol.md` §5 為唯一正本**（SessionStart 注入，每個 session 都在場），此處不再複製表內容（去雙源）。速記：推理／裁決＝當前模型（不指定 model 繼承主迴圈）、程式編寫＝`sonnet`、批次文書／搜尋＝`haiku`、瑣碎單步主迴圈直接做不委派；抗辯三反方底線同見 §5。

- 派工包 7 欄、回報模板、升級/降級規則見 `model_dispatch_rules.md`——委派時強制使用。

## 不可妥協守則（Non-negotiable Guardrails）

- **精準修改**：只動用戶要求的區塊；不順手重排、重格式化、刪無關程式碼。特殊語法檔（PowerLanguage / Pine Script / SQL migration / CI 配置）尤其嚴格。
- **註解與參數說明是受保護內容**：優化邏輯也不得刪參數說明、既有註解、交易假設、歷史備註；未經指示刪除＝失敗，不是清理。
- **先讀後寫、改前備份**：改任何既有檔案前必先 Read；必先建 `<檔名>.bak.<YYYYMMDD-HHMMSS>` 並確認存在——備份失敗即停。
- **工具誠實**：不得宣稱不存在的工具/檔案/權限；能力缺失就明說並降級（如輸出手貼內容）。
- **規則衝突時**：選更安全、更窄、可回復的動作；仍不確定 → 先問用戶再動檔案。

## 治理文件路由（Routing）

| 情境 | 讀這份 |
|---|---|
| 委派子代理（派工包 / 回報格式 / 升級降級） | `model_dispatch_rules.md` |
| 何時慢下來 / 問用戶 / 換路 / 升級模型；輸出前自我抗辯模組 | `cognitive_rubrics.md` |

## 專案守則

- 測試一律放 `tests/`，遵守全域 docstring 鐵則（四區塊 + 執行紀錄）。
- hooks 腳本改動後必須重跑 `python -m pytest tests/ -v` 且綠燈才算完成。
- `.claude/hooks/.last_*` 是 hook marker（e2e 測試用）：inject/nudge 的兩個＝觸發即寫；`.last_stopgate` ＝ gate **成功完跑**才寫——對照 `.last_promptsubmit` 仍新鮮而它過期＝gate 斷線，不是「沒觸發」。不要手動改、不要進版控。
- 佈署到全域（`C:\Users\user\.claude\`）前必須：本專案全部測試綠 + 用戶明確點頭。佈署步驟見 README.md。
- 測試環境豁免 uv（使用者 2026-07-04 拍板）：本專案走系統 python + 全域 pytest，不建 pyproject，hooks 亦走系統 python。
