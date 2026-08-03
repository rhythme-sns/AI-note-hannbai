import datetime
import base64
import os
from pathlib import Path

import requests

from common import generate_with_search, send_mail, BRAND_CONTEXT

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
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


def generate_image_prompt_and_caption() -> tuple[str, str]:
    weekday = datetime.datetime.now().weekday()
    angle = WEEKDAY_ANGLES[weekday]

    prompt = f"""あなたは「本質のAI活用術」のInstagram投稿を担当するエージェントです。

{BRAND_CONTEXT}

# リサーチ
web_searchで、AI活用系のインフルエンサーが「AIのメリット」についてどんな切り口で語っているかを調べてください。
特定個人を名指しで引用せず、一般的傾向として要約し着想に使ってください。

# 今日の角度
{angle}

# 出力(必ずこの2つの見出しで分けて出力する)

## IMAGE_PROMPT
Instagram用の正方形(1080x1080)情報グラフィック画像を生成するための、英語の画像生成プロンプトを1つ書いてください。
ブランドのビジュアルアイデンティティ(深いインディゴ〜バイオレット〜ブラックのグラデーション、光の粒子、上品でミニマル、サイバーロボット感は避ける)に沿い、
今日の角度「{angle}」を表す短い日本語の見出しコピー(1行)を画像内に入れる指示を含めてください。テキストは詰め込みすぎない。

## CAPTION
日本語のキャプション文。リサーチで見えた一般的傾向を踏まえた共感導入文→分身メソッドの考え方に軽く触れる→ハッシュタグ5〜8個(#本質のAI活用術 を必ず含む)。
実在しない実績数字は書かない。
"""
    text = generate_with_search(prompt, max_tokens=2000)

    if "## IMAGE_PROMPT" in text and "## CAPTION" in text:
        # web_search利用時にClaudeが前置きの説明文を挟むことがあるため、
        # マーカーの"間"だけを厳密に取り出す(前置き文が紛れ込むのを防ぐ)
        image_prompt = text.split("## IMAGE_PROMPT", 1)[1].split("## CAPTION", 1)[0].strip()
        caption = text.split("## CAPTION", 1)[1].strip()
    else:
        # フォーマットが崩れた場合のフォールバック(画像生成が失敗しないようにする)
        print("⚠ 出力フォーマットが期待通りではありませんでした。フォールバックのプロンプトを使用します。")
        print("=== Claudeの生出力 ===")
        print(text)
        image_prompt = (
            "Minimalist Instagram square infographic, deep indigo to violet to black gradient, "
            "glowing light particles, elegant premium tone, no sci-fi or robot cliches, no readable text."
        )
        caption = text.strip()

    # OpenAI側の上限に余裕を持たせて安全に切り詰める
    image_prompt = image_prompt[:3500]

    return image_prompt, caption


def generate_image(image_prompt: str) -> Path:
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-image-1",
            "prompt": image_prompt,
            "size": "1024x1024",
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
    image_prompt, caption = generate_image_prompt_and_caption()
    image_path = generate_image(image_prompt)

    body = f"""本文キャプション:

{caption}

---
⚠ これは自動生成された下書きです。内容を確認のうえ、ご自身でInstagramに投稿してください。
(画像はこのメールに添付されています)
"""
    send_mail(
        f"【本質のAI活用術】今日のInstagram投稿案 ({datetime.date.today()})",
        body,
        attachment_path=image_path,
    )


if __name__ == "__main__":
    main()
