import os
import datetime

from common import generate_structured_with_search, send_mail, BRAND_CONTEXT
from social_post import post_thread_to_x, post_thread_to_threads
from content_research import research_trending_ai_content
from content_strategist import plan_content_angle

NOTE_URL = "https://note.com/sakaki_ai"
THREAD_LENGTH = 5
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

SCHEMA = {
    "type": "object",
    "properties": {
        "x_thread": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                f"X用、{THREAD_LENGTH}ツイート構成のスレッド。必ずちょうど{THREAD_LENGTH}個の文字列"
                "(多くても少なくてもいけない)。番号(1/5など)は含めない。最後のツイートに"
                f"「続きはこちらから」などのCTA+{NOTE_URL}を含む"
            ),
        },
        "threads_thread": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                f"Threads用、{THREAD_LENGTH}投稿構成のスレッド。x_threadと同じ内容・流れだが、"
                "言い回しや例えを変え、丸写しにならないようにする。必ずちょうど"
                f"{THREAD_LENGTH}個の文字列。最後の投稿にCTA+{NOTE_URL}を含む"
            ),
        },
    },
    "required": ["x_thread", "threads_thread"],
    "additionalProperties": False,
}


def build_prompt(angle: str, key_point: str) -> str:
    return f"""あなたは「本質のAI活用術」の集客を担当するSNSマーケターです。

{BRAND_CONTEXT}

# 今回の切り口(リサーチ担当・企画担当エージェントが事前検討済み)
切り口:{angle}
伝えたい核心:{key_point}

# 今日作成するもの(お昼のスレッド投稿)
上記の「切り口」「伝えたい核心」を土台に、分身メソッドの考え方(言語化→権限設計→仕組み化→検証ループ)とも
絡めながらスレッドを組み立ててください。

## X用 スレッド(ちょうど{THREAD_LENGTH}ツイート)
{THREAD_LENGTH}ツイートで簡潔に展開する。

### 1〜2ツイート目のつなぎ目を特に工夫すること
- 1ツイート目は「切り口」に沿った強いフックで完全に興味を持たせるが、核心や結論は明かさない
- 1ツイート目の末尾は、あえて核心の一歩手前で止める・具体的な問いを投げる・意外な一言で終えるなど、
  読者が「え、どういうこと?」「続きが気になる」と感じて次を開きたくなる形にする
- 2ツイート目は1ツイート目の引きを正面から回収し、そこから話を広げる構成にする
  (1ツイート目だけで内容が完結してしまう、2ツイート目が唐突に始まる、という構成は避ける)

## Threads用 スレッド
X用と同じ内容・流れ・つなぎ目の工夫を踏襲するが、言い回しや例えを変えて、Xの投稿をそのままコピーしたようにならないようにする。
同じく{THREAD_LENGTH}投稿。

# 制約
- 各スレッドの最後の投稿には必ず「続きはこちらから👇」のようなひと言(CTA)を入れたうえで、直後に
  {NOTE_URL} を貼ること。URLだけを裸で置いたり、プレースホルダーを書いたりしないこと(note誘導はスレッドのみでよい)
- 誇張・釣り表現、実在しない実績数字、特定個人の断定的引用は禁止です
- 指定されたJSON形式で出力してください。各スレッド配列は必ずちょうど{THREAD_LENGTH}個の文字列にすること
"""


def main() -> None:
    # 投稿前タスク①:人気AI発信アカウントの傾向をリサーチ
    research_summary = research_trending_ai_content()
    # 投稿前タスク②:リサーチを踏まえて今回の切り口を企画
    plan = plan_content_angle(research_summary, "お昼のスレッド")
    angle = plan["angle"]
    key_point = plan["key_point"]

    result = generate_structured_with_search(
        build_prompt(angle, key_point), SCHEMA, max_tokens=4000
    )
    x_thread = result["x_thread"]
    threads_thread = result["threads_thread"]

    results: list[str] = []
    errors: list[str] = []

    if len(x_thread) != THREAD_LENGTH:
        results.append(
            f"⚠ Xスレッドが{THREAD_LENGTH}件ちょうどではなく{len(x_thread)}件生成されました(そのまま投稿します)"
        )
        x_thread = x_thread[:THREAD_LENGTH]
    if len(threads_thread) != THREAD_LENGTH:
        results.append(
            f"⚠ Threadsスレッドが{THREAD_LENGTH}件ちょうどではなく{len(threads_thread)}件生成されました(そのまま投稿します)"
        )
        threads_thread = threads_thread[:THREAD_LENGTH]

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
    th_text = "\n\n".join(
        f"{i + 1}/{len(threads_thread)}: {t}" for i, t in enumerate(threads_thread)
    )

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
