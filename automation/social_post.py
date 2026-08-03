import os

import requests
import tweepy

# --- X (旧Twitter) ---

X_API_KEY = os.environ["X_API_KEY"]
X_API_SECRET = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]


def _get_x_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )


def post_thread_to_x(texts: list[str]) -> list[str]:
    """textsを順番に投稿する。2件目以降は直前の投稿への返信として連結し、スレッドを作る。
    1件だけならスレッドにならず単発ポストになる。投稿されたツイートIDのリストを返す。
    """
    client = _get_x_client()
    ids: list[str] = []
    reply_to: str | None = None
    for text in texts:
        resp = client.create_tweet(text=text, in_reply_to_tweet_id=reply_to)
        tweet_id = str(resp.data["id"])
        ids.append(tweet_id)
        reply_to = tweet_id
    return ids


# --- Threads (Meta) ---

THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_USER_ID = os.environ["THREADS_USER_ID"]
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]


def _threads_request(path: str, params: dict) -> dict:
    resp = requests.post(
        f"{THREADS_API_BASE}/{path}",
        params={**params, "access_token": THREADS_ACCESS_TOKEN},
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"=== Threads APIエラー({path}) ===")
        print(f"status_code: {resp.status_code}")
        print(resp.text)
    resp.raise_for_status()
    return resp.json()


def _post_one_to_threads(text: str, reply_to_id: str | None = None) -> str:
    params = {"media_type": "TEXT", "text": text}
    if reply_to_id:
        params["reply_to_id"] = reply_to_id
    container = _threads_request(f"{THREADS_USER_ID}/threads", params)
    container_id = container["id"]
    published = _threads_request(
        f"{THREADS_USER_ID}/threads_publish", {"creation_id": container_id}
    )
    return str(published["id"])


def post_thread_to_threads(texts: list[str]) -> list[str]:
    """textsを順番にThreadsへ投稿する。2件目以降は直前の投稿への返信として連結する。
    投稿されたメディアIDのリストを返す。
    """
    ids: list[str] = []
    reply_to: str | None = None
    for text in texts:
        post_id = _post_one_to_threads(text, reply_to_id=reply_to)
        ids.append(post_id)
        reply_to = post_id
    return ids
