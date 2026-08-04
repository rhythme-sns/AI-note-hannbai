import datetime
import base64
import os
import random
from pathlib import Path

import requests

from common import generate_structured_with_search, send_mail, BRAND_CONTEXT
from reels_media import generate_ambient_track, build_reel_video
from media_repo import push_video_and_get_url
from instagram_post import post_reel_to_instagram

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
NOTE_URL = "https://note.com/sakaki_ai"
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
REEL_DURATION_SECONDS = 18

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

WEEKDAY_ANGLES = {
    0: "業務効率化(時間の使い方が変わる)",
    1: "判断疲れが減る",
    2: "小さく始められる",
    3: "副業・収益化のきっかけになる",
    4: "学習速度が上がる",
    5: "人間関係・コミュニケーションが楽になる",
    6: "その週で一番刺さりそうな角度を自由選択",
}

# 画像の情景をコード側でランダム化する(毎回マンネリ化しないように)
CAMERA_ANGLES = [
    "斜め上から見下ろすアングル",
    "正面から見たアングル",
    "手元とキーボードのクローズアップ",
    "肩越しに画面を覗き込むようなアングル",
    "デスク全体を少し引いて捉えた俯瞰気味のアングル",
]
TIME_OF_DAY = [
    "朝の柔らかい自然光が差し込む時間帯",
    "夕方のオレンジがかった光が差し込む時間帯",
    "夜、デスクライトだけが灯る落ち着いた時間帯",
    "曇りの日の均一で静かな光の時間帯",
]
WORKSPACE_STYLES = [
    "観葉植物とナチュラルウッドを使ったミニマルな北欧風デスク",
    "複数モニターとメカニカルキーボードが並ぶガジェット好きなデスク",
    "ノートPCとコーヒーカップだけが置かれたミニマリストなカフェ風デスク",
    "大きな窓のある明るいスタジオのようなクリエイティブなワークスペース",
    "スケッチやカラーサンプルが散らばったデザイナーらしい雑多で温かみのあるデスク",
]
BUNSHIN_ACCENTS = [
    "画面の中にほのかに光る抽象的な人型のシルエット(分身)が浮かんでいる",
    "デスクの上に小さな光の粒子が静かに舞っている",
    "モニター越しにほのかに紫がかった光が漏れている",
    "キーボードの上にうっすらとした光の軌跡が残っている",
    "画面に映るもう一つの淡い人影が、本人と同じ姿勢でタイピングしている",
]

# 投稿の締めに毎回必ず入れる、フォロー・いいね・保存の訴求とnoteへの誘導(内容はコード側で固定し、生成任せにしない)
CLOSING_CTA = (
    "━━━━━━━━━\n"
    "📌 保存しておくと、あとで見返せます\n"
    "❤️ 参考になったら「いいね」で教えてください\n"
    "🔔 明日以降の投稿も見逃したくない方はフォローしてお待ちください\n\n"
    "▶ もっと詳しく知りたい方はこちら\n"
    f"{NOTE_URL}"
)

SCHEMA = {
    "type": "object",
    "properties": {
        "image_prompt": {
            "type": "string",
            "description": "Instagramリール用の縦長(9:16)画像を生成するための英語の画像生成プロンプト",
        },
        "caption_body": {
            "type": "string",
            "description": (
                "日本語のキャプション本文。共感導入文→分身メソッドの考え方に軽く触れる、という流れ。"
                "CTA(フォロー・いいね・保存を促す文言)やnoteのURL、ハッシュタグはここに含めないこと"
                "(それらは別途固定で付加される)"
            ),
        },
        "hashtags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "5〜8個。それぞれ先頭に#を付けること。#本質のAI活用術 を必ず含む",
        },
    },
    "required": ["image_prompt", "caption_body", "hashtags"],
    "additionalProperties": False,
}


def build_prompt(angle: str, scene_angle: str, scene_time: str, scene_workspace: str, scene_accent: str) -> str:
    return f"""あなたは「本質のAI活用術」のInstagramリール投稿を担当するエージェントです。

{BRAND_CONTEXT}

# リサーチ
web_searchで、AI活用系のインフルエンサーが「AIのメリット」についてどんな切り口で語っているかを調べてください。
特定個人を名指しで引用せず、一般的傾向として要約し着想に使ってください。

# 今日の角度
{angle}

# 今日の画像の情景設定(必ずこの4つをそのまま反映すること)
- アングル:{scene_angle}
- 時間帯・光:{scene_time}
- ワークスペースの雰囲気:{scene_workspace}
- 「分身」を感じさせる演出:{scene_accent}

# image_promptの要件
Instagramリール(縦型9:16、動画の1枚絵ベースになる)用の画像を生成するための、英語の画像生成プロンプトを1つ書いてください。
クリエイター・デザイナーがおしゃれなワークスペースでPC作業をしている情景を、写実的で温かみのある高級感のあるトーンで描いてください。
人物は後ろ姿・手元・シルエットなど「顔がはっきり写らない」構図にする。上記の情景設定(アングル・時間帯・ワークスペース・分身演出)を必ず具体的に反映すること。
縦長フレームの左右端は動画化の際に軽くクロップされる可能性があるため、主要な被写体は画面中央に収めること。
ブランドカラー(ネイビー〜バイオレット系の差し色)をどこかに感じさせつつ、サイバーロボット感・ネオン感は避ける。
画像内には見出しコピーやロゴ、文字・タイポグラフィの類を一切入れないこと(テキストなしの写真として生成する)。

# caption_bodyとhashtagsの要件
リサーチで見えた一般的傾向を踏まえた共感導入文→分身メソッドの考え方に軽く触れる、という流れの本文を書いてください。
実在しない実績数字は書かない。CTAやURL、ハッシュタグはcaption_bodyに含めないこと。
"""


def generate_content() -> tuple[str, str]:
    weekday = datetime.datetime.now().weekday()
    angle = WEEKDAY_ANGLES[weekday]

    scene_angle = random.choice(CAMERA_ANGLES)
    scene_time = random.choice(TIME_OF_DAY)
    scene_workspace = random.choice(WORKSPACE_STYLES)
    scene_accent = random.choice(BUNSHIN_ACCENTS)

    result = generate_structured_with_search(
        build_prompt(angle, scene_angle, scene_time, scene_workspace, scene_accent),
        SCHEMA,
        max_tokens=6000,
    )

    image_prompt = result["image_prompt"][:3500]  # OpenAI側の上限に余裕を持たせて安全に切り詰める
    caption = compose_caption(result["caption_body"], result["hashtags"])
    return image_prompt, caption


def compose_caption(caption_body: str, hashtags: list[str]) -> str:
    tags = " ".join(hashtags)
    return f"{caption_body.strip()}\n\n{CLOSING_CTA}\n\n{tags}"


def generate_image(image_prompt: str) -> Path:
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-image-1",
            "prompt": image_prompt,
            "size": "1024x1536",  # 縦長。ffmpeg側でリール用の1080x1920にクロップ・アニメーション化する
            "quality": "high",
            "n": 1,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        print("=== OpenAI APIエラーの詳細 ===")
        print(f"status_code: {resp.status_code}")
        print(resp.text)
        print("=== 送信した画像プロンプト ===")
        print(image_prompt)
    resp.raise_for_status()
    data = resp.json()["data"][0]
    out_path = OUTPUT_DIR / f"instagram_{datetime.date.today()}.png"

    if "b64_json" in data:
        out_path.write_bytes(base64.b64decode(data["b64_json"]))
    else:
        # response_formatを指定しないとURL形式で返ってくる場合がある
        img_resp = requests.get(data["url"], timeout=60)
        img_resp.raise_for_status()
        out_path.write_bytes(img_resp.content)

    return out_path


def main() -> None:
    image_prompt, caption = generate_content()
    image_path = generate_image(image_prompt)

    # BGMは3種類のアンビエントプリセットを日付でローテーション
    preset_index = datetime.date.today().toordinal() % 3
    audio_path = generate_ambient_track(
        preset_index, REEL_DURATION_SECONDS, OUTPUT_DIR / f"audio_{datetime.date.today()}.wav"
    )
    video_path = build_reel_video(
        image_path, audio_path, OUTPUT_DIR / f"reel_{datetime.date.today()}.mp4",
        duration=REEL_DURATION_SECONDS,
    )

    status_lines: list[str] = []
    error: str | None = None

    if DRY_RUN:
        status_lines.append("🧪 DRY RUN: 実際の投稿はスキップしました(生成内容のみ確認できます)")
    else:
        try:
            video_url = push_video_and_get_url(video_path, f"instagram_{datetime.date.today()}.mp4")
            media_id = post_reel_to_instagram(video_url, caption)
            status_lines.append(f"Instagram: リール投稿(id={media_id})が完了しました")
        except Exception as e:  # noqa: BLE001
            error = f"{type(e).__name__}: {e}"
            status_lines.append(f"⚠ Instagram投稿でエラー: {error}")

    if DRY_RUN:
        status = "🧪 DRY RUN 完了"
        subject_prefix = "【DRY RUN】"
    elif error:
        status = "⚠ 投稿失敗"
        subject_prefix = "【本質のAI活用術/要確認】"
    else:
        status = "✅ 投稿完了"
        subject_prefix = "【本質のAI活用術】"

    body = f"""{status}

【投稿キャプション】
{caption}

【結果】
{chr(10).join(status_lines)}
"""
    send_mail(
        f"{subject_prefix}今日のInstagramリール投稿 ({datetime.date.today()})",
        body,
        attachment_path=image_path,
    )

    if error:
        raise RuntimeError(error)


if __name__ == "__main__":
    main()
