# -*- coding: utf-8 -*-
"""
Stop hook 驗證 gate（FABLE-PROTOCOL 組件3，soft 模式）。

行為：解析 transcript，若「最後一個真實 user prompt 之後」有 Edit/Write/NotebookEdit
修改程式碼檔，卻沒有任何測試執行命令，輸出 {"decision":"block","reason":...} 擋回一次；
stop_hook_active=true（模型第二次結束）時放行，避免純討論 session 被無限卡死。
任何解析錯誤一律 fail-open（exit 0 無輸出）——gate 絕不可弄壞 session。

介面：stdin 收 hook JSON（transcript_path / stop_hook_active），stdout 輸出 block JSON 或無輸出。
失效遙測：fail-open 吞例外前 append 一行（timestamp + repr）到同目錄 .gate_fail（gitignored；
巢狀 try，遙測寫入失敗亦不得阻斷）——沒有屍檢紀錄的 fail-open 會靜默死亡數日無人察覺。
解譯器層死亡（python 沒起來）本檔看不見：由 stop_gate.sh 在 gate 成功返回後寫
.last_stopgate marker——解譯器死亡＝marker 停止更新（對照 .last_promptsubmit 判定）。
測試：tests/test_verify_gate.py（十三案例，fail-then-pass 已驗證；T9 多生態識別、T10 假放行防護、
T11 --test 自測入口、T12 cp950 stdout 回歸、T13 失效遙測）。
"""
import json
import re
import sys
from pathlib import Path, PurePath

CODE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".sh", ".ps1", ".psm1", ".vbs",
    ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".sql", ".php",
}

TEST_CMD_RE = re.compile(
    r"(pytest"
    r"|python[3]?(\.exe)?\s+(-m\s+unittest|(\S*[/\\])?(test\S*\.py|\S*_test\.py))"
    r"|npm\s+(run\s+)?test\b|yarn\s+test\b|pnpm\s+(run\s+)?test\b|bun\s+test\b|node\s+--test"
    r"|go\s+test|cargo\s+test|\bvitest\b|\bjest\b"
    r"|mvnw?(\.cmd)?\s+(\S+\s+)*test(\s|$)|gradlew?(\.bat)?\s+(\S+\s+)*test(\s|$)|dotnet\s+test(\s|$)"
    r"|\brspec\b|\bphpunit\b|\bctest\b|make\s+test\b|rake\s+(\S+\s+)*test\b|mix\s+test\b"
    r"|(^|[;&|]\s*)(tox|nox)\b|deno\s+test|rails\s+test"
    # shell 測試/檢查 runner（2026-07-21 T14：vault-check.sh 這類自訂 .sh runner
    # 本在 CODE_EXTS 卻無對應測試分支，改 .sh 後跑它驗證仍被誤攔實證）；前導邊界
    # (?:^|[\s;&|/\\]) + 尾 \b，並用 test([-_]…)? 防 latest.sh/testing.sh 假放行
    r"|(?:^|[\s;&|/\\])(test([-_][\w-]*)?|[\w-]*_test|[\w-]*check)\.sh\b"
    # 腳本自帶 --test 自測入口（2026-07-05 T11：zh_convert_safe.py --test 真實
    # session 連續誤攔實證）；(\s|$) 錨定使 --tests/--testing/--test-pypi 不假放行
    r"|\s--test(\s|$))",
    re.IGNORECASE,
)

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}
LOCAL_COMMAND_PREFIXES = (
    "<command-name>", "<local-command-stdout>",
    "<local-command-stderr>", "<local-command-caveat>",
)


def is_real_user_prompt(entry):
    if entry.get("type") != "user":
        return False
    content = entry.get("message", {}).get("content")
    if not isinstance(content, str):
        return False  # tool_result 列表不是真實 prompt
    return not content.lstrip().startswith(LOCAL_COMMAND_PREFIXES)


def iter_tool_uses(entries):
    for entry in entries:
        if entry.get("type") != "assistant":
            continue
        content = entry.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield block.get("name", ""), block.get("input", {}) or {}


def analyze(entries):
    """回傳 (本輪修改的程式碼檔名列表, 是否偵測到測試執行)。"""
    last_prompt_idx = -1
    for i, entry in enumerate(entries):
        if is_real_user_prompt(entry):
            last_prompt_idx = i
    current_turn = entries[last_prompt_idx + 1:]

    edited, test_seen = [], False
    for name, tool_input in iter_tool_uses(current_turn):
        if name in EDIT_TOOLS:
            path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
            if PurePath(path).suffix.lower() in CODE_EXTS:
                edited.append(PurePath(path).name)
        elif name in SHELL_TOOLS:
            if TEST_CMD_RE.search(tool_input.get("command", "")):
                test_seen = True
    return edited, test_seen


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        data = json.loads(sys.stdin.read() or "{}")
        if data.get("stop_hook_active"):
            return 0
        entries = []
        with open(data["transcript_path"], encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        edited, test_seen = analyze(entries)
        if edited and not test_seen:
            files = "、".join(dict.fromkeys(edited))
            print(json.dumps({
                "decision": "block",
                "reason": (
                    f"⛔ FABLE-PROTOCOL 驗證 gate：本輪修改了程式碼（{files}）"
                    "但未偵測到自動化測試執行。請補跑對應測試並附 fail-then-pass 證據後再結束；"
                    "若本輪確實不需測試（中途暫停、實驗性修改），請向用戶說明原因後再次結束即可放行。"
                ),
            }, ensure_ascii=False))
    except Exception as exc:
        # fail-open：gate 自身故障不得阻斷 session；但留一行屍檢紀錄，
        # 否則靜默死亡無從察覺（遙測本身再包一層 try，寫入失敗照樣放行）
        try:
            from datetime import datetime
            with open(Path(__file__).resolve().parent / ".gate_fail",
                      "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} {exc!r}\n")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
