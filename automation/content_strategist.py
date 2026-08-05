"""投稿前に実行する企画エージェント。

リサーチエージェント(content_research.py)がまとめた傾向を踏まえつつ、
「サカキ」のペルソナ・ブランドに合わせて、今回のSNS投稿で扱う具体的な切り口を1つ考える。
リサーチ結果はあくまで着想の材料であり、丸写しはしない。
「プロンプト活用」「マネタイズ」系は切り口の一例に過ぎず、それだけに偏らないよう幅広く検討する。
"""

from common import generate_structured, BRAND_CONTEXT

SCHEMA = {
    "type": "object",
    "properties": {
        "angle": {
            "type": "string",
            "description": (
                "今回の投稿で扱う具体的な切り口を1つ。抽象度は高いが実用的なテーマにすること"
                "(例:「◯◯な場面ではこのプロンプトを使うと良い」「マネタイズするにはどのAIをどう使うといいか」"
                "など。これらは一例に過ぎず、他にも実用的な切り口があれば自由に考えてよい)"
            ),
        },
        "key_point": {
            "type": "string",
            "description": "その切り口で読者に伝える核心的なメッセージ(1〜2文)",
        },
    },
    "required": ["angle", "key_point"],
    "additionalProperties": False,
}


def build_prompt(research_summary: str, slot_label: str) -> str:
    return f"""あなたは「本質のAI活用術」の企画担当です。

{BRAND_CONTEXT}

# 直近のAI発信トレンドのリサーチ結果(リサーチ担当エージェントより)
{research_summary}

# タスク({slot_label}向け)
上記のリサーチはあくまで参考情報です。自分の言葉・自分のペルソナ(分身メソッド)に合わせて、
今回のSNS投稿で扱う「切り口」を1つ考えてください。

抽象度は高いが実用的なテーマにすること。方向性の一例は以下ですが、これらに縛られる必要はなく、
リサーチ結果や読者の関心に合わせて他の切り口を考えても構いません:
- 「◯◯な場面ではこのプロンプトを使うと良い」系(具体的なプロンプト文そのものを丸ごと開示する必要はなく、
  考え方・使いどころを抽象化して伝える)
- 「マネタイズするにはどのAIをどう使えばいいか」系
- その他、分身メソッド(言語化・権限設計・仕組み化・検証ループ)に関連する実用的な切り口

# 制約
- リサーチ結果の丸写し・特定アカウントの模倣はしないこと
- 具体的な社名・商品名の羅列、実在しない実績数字は書かないこと
- 指定されたJSON形式で出力してください
"""


def plan_content_angle(research_summary: str, slot_label: str) -> dict:
    """リサーチ結果と自アカウントのペルソナから、今回発信する切り口を考えるエージェント。"""
    return generate_structured(build_prompt(research_summary, slot_label), SCHEMA, max_tokens=1200)
