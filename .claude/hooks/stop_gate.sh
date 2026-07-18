#!/usr/bin/env bash
# Stop hook wrapper：呼叫 python gate，「成功返回後」才寫 .last_stopgate marker。
# marker 語意＝gate 這次真的跑完了。解譯器沒起來（py/python3 雙亡、升版斷路徑）
# 或 gate 中途死亡 → marker 不更新；對照 .last_promptsubmit 仍新鮮即可判定 gate 斷線。
# 先寫 marker 的版本在解譯器死亡時與健康狀態不可區分——語意是反的，不得回退。
# py -3 為版本無關 launcher；py 不存在時退回 PATH 上的 python3。
HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"
py -3 "$HOOKS_DIR/verify_gate.py" 2>/dev/null || python3 "$HOOKS_DIR/verify_gate.py"
rc=$?
[ "$rc" -eq 0 ] && date +"%Y-%m-%dT%H:%M:%S%z" > "$HOOKS_DIR/.last_stopgate" 2>/dev/null
# rc 鉗制：Stop hook 的 exit 2 = blocking error（阻止結束，且 gate 沒起來時
# JSON 層防迴圈保護到不了→每次 Stop 都被卡）。python 對「檔案不存在/不可讀」
# 正是 exit 2——部分佈署失敗會踩中。gate 自身故障絕不可阻斷 session：
# 非零一律降為 1（stderr 照樣可見、不阻斷），fail-open 是底線。
[ "$rc" -ne 0 ] && rc=1
exit "$rc"
