import sys
import datetime

from common import generate_structured_with_search, send_mail, BRAND_CONTEXT
from social_post import post_thread_to_x, post_thread_to_threads

NOTE_URL = "https://note.com/sakaki_ai"

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
                "X用、140字以内の単発ポスト本文。文末に「続きはこちらから」などのひと言(CTA)を添えたうえで、"
                f"直後に {NOTE_URL} を貼ること(URLだけを裸で置かない)"
            ),
        },
        "threads_post": {
            "type": "string",
            "description": (
                "Threads用、単発ポスト本文。x_postと伝えたい要点は同じだが、言い回しや切り出し方を変え、"
                f"丸写しにならないようにする。こちらもCTA付きで {NOTE_URL} を貼ること"
            ),
        },
    },
    "required": ["x_post", "threads_post"],
    "additionalProperties": False,
}


def build_prompt(slot_label: str, pattern: str) -> str:
    return f"""あなたは「本質のAI活用術」の集客を担当するSNSマーケターです。

{BRAND_CONTEXT}

# リサーチ
web_searchで、AI活用・生成AI関連で発信しているインフルエンサーが今どんな切り口・フォーマットで投稿しているかを調べてください。
特定個人を名指しで引用・模倣せず、一般的な傾向として要約し着想に使ってください。

# 今日作成するもの({slot_label}の単発ポスト)
今日のパターン:{pattern}

## X用
140字以内。ハッシュタグを2〜4個(#本質のAI活用術 を必ず含む)。

## Threads用
X用と同じ要点・同じテーマを扱うが、言い回しや切り口を変え、Xの投稿をそのままコピーしたようにならないようにする。

# 制約
- 文末には必ず「続きはこちらから👇」のようなひと言(CTA)を入れたうえで、直後に {NOTE_URL} を貼ること。
  URLだけを裸で置いたり、プレースホルダーを書いたりしないこと
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

    result = generate_structured_with_search(
        build_prompt(slot_label, pattern), SCHEMA, max_tokens=2000
    )
    x_post = result["x_post"]
    threads_post = result["threads_post"]

    results: list[str] = []
    errors: list[str] = []

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

    status = "✅ 自動投稿 完了" if not errors else "⚠ 自動投稿 一部エラーあり"
    body = f"""{status}

【X 単発ポスト({slot_label})】
{x_post}

【Threads 単発ポスト({slot_label})】
{threads_post}

【結果】
{chr(10).join(results + errors)}
"""
    send_mail(
        f"【本質のAI活用術】{slot_label}の単発ポスト自動投稿結果 ({datetime.date.today()})",
        body,
    )

    if errors:
        raise RuntimeError("; ".join(errors))


if __name__ == "__main__":
    main()
