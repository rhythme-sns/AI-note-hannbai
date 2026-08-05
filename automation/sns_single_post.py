import os
import sys
import datetime

from common import generate_structured_with_search, send_mail, BRAND_CONTEXT
from social_post import post_thread_to_x, post_thread_to_threads
from content_research import research_trending_ai_content
from content_strategist import plan_content_angle

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

BASE_PATTERNS = {
    0: "問いかけ型(読者の疑問を刺激する)",
    1: "断定型(核心を言い切る)",
    2: "体験談型(実務エピソードを想起させる。具体的すぎる作り話の数字は書かない)",
    3: "悩み共感型(読者のあるあるに寄り添う)",
    4: "数字型(分身メソッドの4ステップなど構造を見せる)",
    5: "フック重視型(強い一文で惹きつける)",
    6: "自由選択(その週で最も反応が良さそうな型)",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "x_post": {
            "type": "string",
            "description": (
                "X用、140字以内の単発ポスト本文。CTAやURLは含めず、投稿本文だけで完結させること"
            ),
        },
        "threads_post": {
            "type": "string",
            "description": (
                "Threads用、単発ポスト本文。x_postと伝えたい要点は同じだが、言い回しや切り出し方を変え、"
                "丸写しにならないようにする。こちらもCTAやURLは含めない"
            ),
        },
    },
    "required": ["x_post", "threads_post"],
    "additionalProperties": False,
}


def build_prompt(slot_label: str, pattern: str, angle: str, key_point: str) -> str:
    return f"""あなたは「本質のAI活用術」の集客を担当するSNSマーケターです。

{BRAND_CONTEXT}

# 今回の切り口(リサーチ担当・企画担当エージェントが事前検討済み)
切り口:{angle}
伝えたい核心:{key_point}

# 今日作成するもの({slot_label}の単発ポスト)
今日のパターン:{pattern}
上記の「切り口」「伝えたい核心」を土台に、今日のパターンの語り口で投稿本文を作成してください。

## X用
140字以内。ハッシュタグを2〜4個(#本質のAI活用術 を必ず含む)。

## Threads用
X用と同じ要点・同じテーマを扱うが、言い回しや切り口を変え、Xの投稿をそのままコピーしたようにならないようにする。

# 制約
- CTAやURL、note誘導文は入れないこと。投稿本文だけで完結させる
- 誇張・釣り表現、実在しない実績数字、特定個人の断定的引用は禁止です
- 指定されたJSON形式で出力してください
"""


def main() -> None:
    slot = sys.argv[1] if len(sys.argv) > 1 else "morning"
    slot_label = "朝" if slot == "morning" else "夜"

    weekday = datetime.datetime.now().weekday()
    # 朝と夜で型をずらし、同じ日に同じ切り口の投稿にならないようにする
    offset = 0 if slot == "morning" else 3
    pattern = BASE_PATTERNS[(weekday + offset) % 7]

    # 投稿前タスク①:人気AI発信アカウントの傾向をリサーチ
    research_summary = research_trending_ai_content()
    # 投稿前タスク②:リサーチを踏まえて今回の切り口を企画
    plan = plan_content_angle(research_summary, slot_label)
    angle = plan["angle"]
    key_point = plan["key_point"]

    result = generate_structured_with_search(
        build_prompt(slot_label, pattern, angle, key_point), SCHEMA, max_tokens=2000
    )
    x_post = result["x_post"]
    threads_post = result["threads_post"]

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
