"""Instagramリール投稿の機械的な実行部分だけを担う。

キャプションの執筆と画像そのものの生成(Canva/Gamma等)は、このスクリプトを呼び出す
エージェント(routine実行時のClaude)が事前に行い、生成した画像ファイルと
キャプションを JSON ファイルに書き出しておく。このスクリプトは、その画像を元に
ffmpegで縦型動画(Ken Burns風+BGM)を作り、公開用リポジトリへpushしてから
Instagramへ投稿し、結果報告メールを送る。

JSON形式:
{
  "caption": "投稿キャプション本文(CTA・ハッシュタグ込みの最終形)",
  "image_path": "生成済み画像ファイルへのパス(このJSONファイルからの相対 or 絶対パス)"
}
"""
import datetime
import json
import os
import sys
from pathlib import Path

from common import send_mail
from reels_media import prepare_bgm_track, build_reel_video
from media_repo import push_video_and_get_url
from instagram_post import post_reel_to_instagram

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
REEL_DURATION_SECONDS = 18

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("使い方: python post_instagram_reel.py <content.json>")

    content_path = Path(sys.argv[1])
    data = json.loads(content_path.read_text(encoding="utf-8"))
    caption = data["caption"]
    image_path = Path(data["image_path"])
    if not image_path.is_absolute():
        image_path = (content_path.parent / image_path).resolve()
    if not image_path.exists():
        raise SystemExit(f"画像ファイルが見つかりません: {image_path}")

    # BGMはautomation/music/の音源ファイルを日付でローテーション(未用意なら合成音にフォールバック)
    preset_index = datetime.date.today().toordinal() % 3
    audio_path = prepare_bgm_track(
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
