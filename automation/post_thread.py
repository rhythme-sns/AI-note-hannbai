"""お昼のスレッド投稿の機械的な実行部分だけを担う。

文章の生成(リサーチ・企画・執筆)はこのスクリプトを呼び出すエージェント(routine実行時のClaude)が
事前に行い、その結果を JSON ファイルに書き出しておく。このスクリプトはその JSON を読み、
X・Threadsへのスレッド投稿と結果報告メールの送信だけを行う。

JSON形式:
{
  "angle": "今回の切り口",
  "key_point": "伝えたい核心",
  "x_thread": ["1投稿目", "2投稿目", ...],
  "threads_thread": ["1投稿目", "2投稿目", ...]
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
        raise SystemExit("使い方: python post_thread.py <content.json>")

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    angle = data["angle"]
    key_point = data["key_point"]
    x_thread = data["x_thread"]
    threads_thread = data["threads_thread"]

    results: list[str] = []
    errors: list[str] = []

    if DRY_RUN:
        results.append("🧪 DRY RUN: 実際の投稿はスキップしました(生成内容のみ確認できます)")
    else:
        try:
            ids = post_thread_to_x(x_thread)
            results.append(f"X: スレッド{len(ids)}件を投稿しました")
        except Exception as e:  # noqa: BLE001
            errors.append(f"X投稿でエラー: {type(e).__name__}: {e}")

        try:
            ids = post_thread_to_threads(threads_thread)
            results.append(f"Threads: スレッド{len(ids)}件を投稿しました")
        except Exception as e:  # noqa: BLE001
            errors.append(f"Threads投稿でエラー: {type(e).__name__}: {e}")

    status = "🧪 DRY RUN 完了" if DRY_RUN else ("✅ 自動投稿 完了" if not errors else "⚠ 自動投稿 一部エラーあり")
    x_text = "\n\n".join(f"{i + 1}/{len(x_thread)}: {t}" for i, t in enumerate(x_thread))
    th_text = "\n\n".join(f"{i + 1}/{len(threads_thread)}: {t}" for i, t in enumerate(threads_thread))

    body = f"""{status}

【今回の切り口】
{angle}
(核心:{key_point})

【X スレッド({len(x_thread)}ツイート)】
{x_text}

【Threads スレッド({len(threads_thread)}投稿)】
{th_text}

【結果】
{chr(10).join(results + errors)}
"""
    subject_prefix = "【DRY RUN】" if DRY_RUN else "【本質のAI活用術】"
    send_mail(f"{subject_prefix}お昼のスレッド自動投稿結果 ({datetime.date.today()})", body)

    if errors:
        raise RuntimeError("; ".join(errors))


if __name__ == "__main__":
    main()
