import datetime

from common import generate_structured_with_search, send_mail, BRAND_CONTEXT
from social_post import post_thread_to_x, post_thread_to_threads

WEEKDAY_PATTERNS = {
    0: "問いかけ型(読者の疑問を刺激する)",
    1: "断定型(核心を言い切る)",
    2: "体験談型(実務エピソードを想起させる。具体的すぎる作り話の数字は書かない)",
    3: "悩み共感型(読者のあるあるに寄り添う)",
    4: "数字型(分身メソッドの4ステップなど構造を見せる)",
    5: "フック重視型(スレッドの1ツイート目のような強い一文)",
    6: "自由選択(その週で最も反応が良さそうな型)",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "single_post": {
            "type": "string",
            "description": "140字以内の単発ポスト本文。文末にnote誘導とハッシュタグ2〜4個を含む",
        },
        "thread": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "14ツイート構成のスレッド。必ずちょうど14個の文字列を入れること"
                "(多くても少なくてもいけない)。各要素が1ツイート分の本文(140字程度)。"
                "番号(1/14など)は含めない"
            ),
        },
    },
    "required": ["single_post", "thread"],
    "additionalProperties": False,
}


def build_prompt(pattern: str) -> str:
    return f"""あなたは「本質のAI活用術」の集客を担当するSNSマーケターです。

{BRAND_CONTEXT}

# リサーチ
web_searchで、AI活用・生成AI関連で発信しているインフルエンサーが今どんな切り口・フォーマットで投稿しているかを調べてください。
特定個人を名指しで引用・模倣せず、一般的な傾向として要約し着想に使ってください。

# 今日作成するもの

## 単発ポスト(140字以内)
今日のパターン:{pattern}
文末に `[note URLをここに挿入]` を入れる。ハッシュタグを2〜4個(#本質のAI活用術 を必ず含む)。

## スレッド(ちょうど14ツイート)
1ツイート目で完全に興味を持たせるフック。分身メソッドの考え方(言語化→権限設計→仕組み化→検証ループ)を、
14ツイートかけてじっくり展開する(各ステップに複数ツイートを割り当て、具体例や補足を挟みながら深掘りする)。
最後にnoteへの誘導とハッシュタグ。

誇張・釣り表現、実在しない実績数字、特定個人の断定的引用は禁止です。
指定されたJSON形式で出力してください。thread配列は必ずちょうど14個の文字列にすること。
"""


def main() -> None:
    weekday = datetime.datetime.now().weekday()  # 0=Mon ... 6=Sun
    pattern = WEEKDAY_PATTERNS[weekday]

    result = generate_structured_with_search(
        build_prompt(pattern), SCHEMA, max_tokens=5000
    )
    single_post = result["single_post"]
    thread = result["thread"]

    results: list[str] = []
    errors: list[str] = []

    if len(thread) != 14:
        results.append(
            f"⚠ スレッドが14件ちょうどではなく{len(thread)}件生成されました(そのまま投稿します)"
        )
        thread = thread[:14]  # 多すぎる場合のみ安全のため切り詰める

    try:
        x_single_ids = post_thread_to_x([single_post])
        x_thread_ids = post_thread_to_x(thread)
        results.append(
            f"X: 単発ポスト(id={x_single_ids[0]})とスレッド{len(x_thread_ids)}件を投稿しました"
        )
    except Exception as e:  # noqa: BLE001
        errors.append(f"X投稿でエラー: {type(e).__name__}: {e}")

    try:
        th_single_ids = post_thread_to_threads([single_post])
        th_thread_ids = post_thread_to_threads(thread)
        results.append(
            f"Threads: 単発ポスト(id={th_single_ids[0]})とスレッド{len(th_thread_ids)}件を投稿しました"
        )
    except Exception as e:  # noqa: BLE001
        errors.append(f"Threads投稿でエラー: {type(e).__name__}: {e}")

    status = "✅ 自動投稿 完了" if not errors else "⚠ 自動投稿 一部エラーあり"
    total = len(thread)
    thread_text = "\n\n".join(f"{i + 1}/{total}: {t}" for i, t in enumerate(thread))

    body = f"""{status}

【単発ポスト】
{single_post}

【スレッド({total}ツイート)】
{thread_text}

【結果】
{chr(10).join(results + errors) if (results or errors) else "(結果なし)"}
"""
    send_mail(f"【本質のAI活用術】本日のSNS自動投稿結果 ({datetime.date.today()})", body)

    if errors:
        raise RuntimeError("; ".join(errors))


if __name__ == "__main__":
    main()
