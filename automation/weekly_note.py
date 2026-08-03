import datetime
import json
from pathlib import Path

from common import generate_with_search, send_mail, BRAND_CONTEXT

LOG_PATH = Path(__file__).parent / "themes_log.json"


def load_used_themes() -> list[dict]:
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return []


def save_used_themes(log: list[dict]) -> None:
    LOG_PATH.write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def propose_theme(used_themes: list[dict]) -> tuple[str, str]:
    used_list = "\n".join(f"- {t['theme']}" for t in used_themes) or "(まだありません)"

    prompt = f"""あなたは「本質のAI活用術」ブランドの企画担当です。

{BRAND_CONTEXT}

# これまでに扱ったテーマ(重複させないこと)
{used_list}

# 依頼
web_searchで、AI活用・生成AI関連で発信している複数のインフルエンサー・実践者(note、X、ブログなど)が
最近どんなテーマ・切り口で発信しているかを調べてください。
その傾向からインスパイアされた、かつ上記の既出テーマとは重ならない新しいテーマを1つ提案してください。
分身メソッド(言語化→権限設計→仕組み化→検証ループ)という自社の型に当てはめられる、
「〜を分身化する完全ガイド」のような、具体的な業務領域・シーンのテーマにしてください。
特定個人の主張をそのまま模倣・引用するのではなく、業界的な傾向として一般化して着想に使ってください。

# 出力形式(この2行だけを出力すること。他の文章は書かないこと)
THEME: (テーマ名を1行で)
RATIONALE: (なぜ今このテーマが良いと考えたか、リサーチで見えた傾向を踏まえて1〜2文で)
"""
    text = generate_with_search(prompt, max_tokens=1000)

    theme = ""
    rationale = ""
    for line in text.splitlines():
        if line.startswith("THEME:"):
            theme = line.replace("THEME:", "", 1).strip()
        elif line.startswith("RATIONALE:"):
            rationale = line.replace("RATIONALE:", "", 1).strip()

    if not theme:
        # フォールバック:形式が崩れた場合は先頭行をテーマ扱いにする
        theme = text.strip().splitlines()[0][:60] if text.strip() else "AI活用の分身化ガイド"

    return theme, rationale


def main() -> None:
    used_themes = load_used_themes()
    theme, rationale = propose_theme(used_themes)

    prompt = f"""あなたは「本質のAI活用術」ブランドのnote新作コンテンツを企画・執筆する担当です。

{BRAND_CONTEXT}

# 今回のテーマ
{theme}

# このテーマを選んだ理由(リサーチ結果)
{rationale}

# 作業
1. ①企画:タイトル案5つ、ターゲット読者、差別化ポイント、構成案(5〜8章)、想定価格(3,000〜10,000円)
2. ②執筆:リード文(無料)→本文(有料部分、各章に分身メソッドの4ステップを絡めて解説。実務っぽい具体例を添えるが、実在しない数字の実績は捏造しない)→まとめ→今日からの3ステップ。6,000〜9,000字程度
3. ③販売ページ:キャッチコピー、共感パート、ベネフィット5〜7個、目次、おすすめ/おすすめしない人、Q&A3〜4個、価格
4. ④集客:X用単発ポスト3案、ハッシュタグ案

本家「本質のAI活用術」との内容重複を避け、独立して購入しても読める内容にしてください。
誇張・煽り表現は禁止。①〜④の見出しで分けて出力してください。
"""
    content = generate_with_search(prompt, max_tokens=16000, timeout=600.0)

    body = f"""今回のテーマ:{theme}
選定理由:{rationale}

{content}

---
⚠ これは自動生成された下書きです。内容を確認・事実確認・必要な手直しをしたうえで、ご自身の判断でnoteに投稿してください。
"""
    send_mail(f"【本質のAI活用術・新作下書き】{theme} ({datetime.date.today()})", body)

    used_themes.append(
        {"theme": theme, "rationale": rationale, "date": str(datetime.date.today())}
    )
    save_used_themes(used_themes)


if __name__ == "__main__":
    main()
