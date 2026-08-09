"""週次noteの下書きメール送信+テーマ重複防止ログの更新だけを担う。

企画・リサーチ・執筆はこのスクリプトを呼び出すエージェント(routine実行時のClaude)が
事前に行い、その結果を JSON ファイルに書き出しておく。このスクリプトはその JSON を読み、
下書きメールの送信と themes_log.json への追記だけを行う。

JSON形式:
{
  "theme": "今回のテーマ",
  "rationale": "選定理由",
  "content": "企画〜執筆〜販売ページ〜集客文までの本文全体"
}
"""
import datetime
import json
import sys
from pathlib import Path

from common import send_mail

LOG_PATH = Path(__file__).parent / "themes_log.json"


def load_used_themes() -> list[dict]:
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return []


def save_used_themes(log: list[dict]) -> None:
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("使い方: python send_note_draft.py <content.json>")

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    theme = data["theme"]
    rationale = data["rationale"]
    content = data["content"]

    body = f"""今回のテーマ:{theme}
選定理由:{rationale}

{content}

---
⚠ これは自動生成された下書きです。内容を確認・事実確認・必要な手直しをしたうえで、ご自身の判断でnoteに投稿してください。
"""
    send_mail(f"【本質のAI活用術・新作下書き】{theme} ({datetime.date.today()})", body)

    used_themes = load_used_themes()
    used_themes.append({"theme": theme, "rationale": rationale, "date": str(datetime.date.today())})
    save_used_themes(used_themes)


if __name__ == "__main__":
    main()
