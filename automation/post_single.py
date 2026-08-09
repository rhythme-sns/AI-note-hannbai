"""単発ポスト(朝/夜)の機械的な実行部分だけを担う。

文章の生成(リサーチ・企画・執筆)はこのスクリプトを呼び出すエージェント(routine実行時のClaude)が
事前に行い、その結果を JSON ファイルに書き出しておく。このスクリプトはその JSON を読み、
X・Threadsへの投稿と結果報告メールの送信だけを行う。

JSON形式:
{
  "slot_label": "朝" または "夜",
  "angle": "今回の切り口",
  "key_point": "伝えたい核心",
  "x_post": "X用本文",
  "threads_post": "Threads用本文"
}
"""
import datetime
import json
import os
import sys
from pathlib import Path

from common import send_mail
from social_post import post_thread_to_x, post_thread_to_threads

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("使い方: python post_single.py <content.json>")

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    slot_label = data["slot_label"]
    angle = data["angle"]
    key_point = data["key_point"]
    x_post = data["x_post"]
    threads_post = data["threads_post"]

    results: list[str] = []
    errors: list[str] = []

    if DRY_RUN:
        results.append("🧪 DRY RUN: 実際の投稿はスキップしました(生成内容のみ確認できます)")
    else:
        try:
            ids = post_thread_to_x([x_post])
            results.append(f"X: 単発ポスト(id={ids[0]})を投稿しました")
        except Exception as e:  # noqa: BLE001
            errors.append(f"X投稿でエラー: {type(e).__name__}: {e}")

        try:
            ids = post_thread_to_threads([threads_post])
            results.append(f"Threads: 単発ポスト(id={ids[0]})を投稿しました")
        except Exception as e:  # noqa: BLE001
            errors.append(f"Threads投稿でエラー: {type(e).__name__}: {e}")

    status = "🧪 DRY RUN 完了" if DRY_RUN else ("✅ 自動投稿 完了" if not errors else "⚠ 自動投稿 一部エラーあり")
    body = f"""{status}

【今回の切り口】
{angle}
(核心:{key_point})

【X 単発ポスト({slot_label})】
{x_post}

【Threads 単発ポスト({slot_label})】
{threads_post}

【結果】
{chr(10).join(results + errors)}
"""
    subject_prefix = "【DRY RUN】" if DRY_RUN else "【本質のAI活用術】"
    send_mail(
        f"{subject_prefix}{slot_label}の単発ポスト自動投稿結果 ({datetime.date.today()})",
        body,
    )

    if errors:
        raise RuntimeError("; ".join(errors))


if __name__ == "__main__":
    main()
