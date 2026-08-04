"""Instagram Graph API経由でリール(動画)を投稿する。"""
import os
import time

import requests

IG_API_BASE = "https://graph.facebook.com/v21.0"
IG_USER_ID = os.environ["IG_USER_ID"]
IG_ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]


def _ig_request(method: str, path: str, **params) -> dict:
    params["access_token"] = IG_ACCESS_TOKEN
    resp = requests.request(method, f"{IG_API_BASE}/{path}", params=params, timeout=60)
    if resp.status_code != 200:
        print(f"=== Instagram Graph APIエラー({path}) ===")
        print(f"status_code: {resp.status_code}")
        print(resp.text)
    resp.raise_for_status()
    return resp.json()


def _create_container_with_retry(video_url: str, caption: str, retries: int = 4, wait_seconds: int = 15) -> str:
    """push直後はraw.githubusercontent.com側のCDN反映待ちで取得に失敗することがあるため、少し待ってリトライする。"""
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            container = _ig_request(
                "POST", f"{IG_USER_ID}/media",
                media_type="REELS",
                video_url=video_url,
                caption=caption,
                share_to_feed="true",
            )
            return container["id"]
        except requests.exceptions.HTTPError as e:
            last_error = e
            print(f"コンテナ作成を再試行します({attempt + 1}/{retries}): {e}")
            time.sleep(wait_seconds)
    raise last_error


def _wait_until_ready(container_id: str, retries: int = 30, wait_seconds: int = 10) -> None:
    for _ in range(retries):
        status = _ig_request("GET", container_id, fields="status_code,status")
        code = status.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise RuntimeError(f"Instagram側の動画処理でエラーが発生しました: {status}")
        time.sleep(wait_seconds)
    raise RuntimeError("Instagram側の動画処理がタイムアウトしました")


def post_reel_to_instagram(video_url: str, caption: str) -> str:
    """動画URLとキャプションからリールコンテナを作成し、処理完了を待ってから公開する。公開されたメディアIDを返す。"""
    container_id = _create_container_with_retry(video_url, caption)
    _wait_until_ready(container_id)
    published = _ig_request("POST", f"{IG_USER_ID}/media_publish", creation_id=container_id)
    return str(published["id"])
