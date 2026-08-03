import datetime

from common import generate_structured_with_search, send_mail, BRAND_CONTEXT
from social_post import post_thread_to_x, post_thread_to_threads

NOTE_URL = "https://note.com/sakaki_ai"

WEEKDAY_PATTERNS = {
    0: "問いかけ型(読者の疑問を刺激する)",
    1: "断定型(核心を言い切る)",
    2: "体験談型(実務エピソードを想起させる。具体的すぎる作り話の数字は書かない)",
    3: "悩み共感型(読者のあるあるに寄り添う)",
    4: "数字型(分身メソッドの4ステップなど構造を見せる)",
    5: "フック重視型(スレッドの1ツイート目のような強い一文)",
    6: "自由選択(その週で最も反応が良さそうな型)",
}

THREAD_LENGTH = 5

SCHEMA = {
    "type": "object",
    "properties": {
        "x_single_post": {
            "type": "string",
            "description": f"X用、140字以内の単発ポスト本文。文末に {NOTE_URL} とハッシュタグ2〜4個を含む",
        },
        "x_thread": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                f"X用、{THREAD_LENGTH}ツイート構成のスレッド。必ずちょうど{THREAD_LENGTH}個の文字列を入れること"
                "(多くても少なくてもいけない)。各要素が1ツイート分の本文(140字程度)。"
                "番号(1/5など)は含めない"
            ),
        },
        "threads_single_post": {
            "type": "string",
            "description": (
                "Threads用、単発ポスト本文。x_single_postと伝えたい要点は同じだが、"
                "言い回し・切り出し方・文の構成を変え、そのままの丸写しにならないようにする。"
                f"文末に {NOTE_URL} とハッシュタグ2〜4個を含む"
            ),
        },
        "threads_thread": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                f"Threads用、{THREAD_LENGTH}投稿構成のスレッド。x_threadと同じ内容・同じ流れを扱うが、"
                "各投稿の言い回しや例えを変え、そのままの丸写しにならないようにする。"
                f"必ずちょうど{THREAD_LENGTH}個の文字列を入れること。番号は含めない"
            ),
        },
    },
    "required": ["x_single_post", "x_thread", "threads_single_post", "threads_thread"],
    "additionalProperties": False,
}


def build_prompt(pattern: str) -> str:
    return f"""あなたは「本質のAI活用術」の集客を担当するSNSマーケターです。

{BRAND_CONTEXT}

# リサーチ
web_searchで、AI活用・生成AI関連で発信しているインフルエンサーが今どんな切り口・フォーマットで投稿しているかを調べてください。
特定個人を名指しで引用・模倣せず、一般的な傾向として要約し着想に使ってください。

# 今日作成するもの

## X用 単発ポスト(140字以内)
今日のパターン:{pattern}
文末に note誘導(URL: {NOTE_URL})を入れる。ハッシュタグを2〜4個(#本質のAI活用術 を必ず含む)。

## X用 スレッド(ちょうど{THREAD_LENGTH}ツイート)
1ツイート目で完全に興味を持たせるフック。分身メソッドの考え方(言語化→権限設計→仕組み化→検証ループ)を、
{THREAD_LENGTH}ツイートで簡潔に展開する。最後にnote誘導(URL: {NOTE_URL})とハッシュタグ。

## Threads用 単発ポスト・スレッド
上記X用の2つと同じ要点・同じテーマを扱うが、言い回しや切り口を変えて、
Xの投稿をそのままコピーしたようにならないようにする(内容の重複感を避ける)。
スレッドは同じく{THREAD_LENGTH}投稿。こちらもnote誘導(URL: {NOTE_URL})を入れる。

# 制約
- URLは必ず {NOTE_URL} をそのまま使うこと。プレースホルダーや「ここに挿入」のような表記は絶対に書かないこと
- 誇張・釣り表現、実在しない実績数字、特定個人の断定的引用は禁止です
- 指定されたJSON形式で出力してください。thread系の配列は必ずちょうど{THREAD_LENGTH}個の文字列にすること
"""


def _post_and_summarize(label: str, single_post: str, thread: list[str], poster) -> str:
    single_ids = poster([single_post])
    thread_ids = poster(thread)
    return f"{label}: 単発ポスト(id={single_ids[0]})とスレッド{len(thread_ids)}件を投稿しました"


def main() -> None:
    weekday = datetime.datetime.now().weekday()  # 0=Mon ... 6=Sun
    pattern = WEEKDAY_PATTERNS[weekday]

    result = generate_structured_with_search(
        build_prompt(pattern), SCHEMA, max_tokens=5000
    )
    x_single_post = result["x_single_post"]
    x_thread = result["x_thread"]
    threads_single_post = result["threads_single_post"]
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

    try:
        results.append(
            _post_and_summarize("X", x_single_post, x_thread, post_thread_to_x)
        )
    except Exception as e:  # noqa: BLE001
        errors.append(f"X投稿でエラー: {type(e).__name__}: {e}")

    try:
        results.append(
            _post_and_summarize(
                "Threads", threads_single_post, threads_thread, post_thread_to_threads
            )
        )
    except Exception as e:  # noqa: BLE001
        errors.append(f"Threads投稿でエラー: {type(e).__name__}: {e}")

    status = "✅ 自動投稿 完了" if not errors else "⚠ 自動投稿 一部エラーあり"
    x_thread_text = "\n\n".join(f"{i + 1}/{len(x_thread)}: {t}" for i, t in enumerate(x_thread))
    threads_thread_text = "\n\n".join(
        f"{i + 1}/{len(threads_thread)}: {t}" for i, t in enumerate(threads_thread)
    )

    body = f"""{status}

【X 単発ポスト】
{x_single_post}

【X スレッド({len(x_thread)}ツイート)】
{x_thread_text}

【Threads 単発ポスト】
{threads_single_post}

【Threads スレッド({len(threads_thread)}投稿)】
{threads_thread_text}

【結果】
{chr(10).join(results + errors) if (results or errors) else "(結果なし)"}
"""
    send_mail(f"【本質のAI活用術】本日のSNS自動投稿結果 ({datetime.date.today()})", body)

    if errors:
        raise RuntimeError("; ".join(errors))


if __name__ == "__main__":
    main()
