"""Instagram Graph APIが動画を取得できるよう、公開用の別リポジトリ(Public)へ
生成した動画をpushし、raw.githubusercontent.comの公開URLを返す。

事業内容(企画書・販売ページ等)が入っているメインリポジトリはPrivateのまま維持し、
動画配信専用の空リポジトリだけを公開する構成にしている。
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

MEDIA_REPO = os.environ["MEDIA_REPO"]  # 例: "your-name/ai-note-reels-media"
MEDIA_REPO_TOKEN = os.environ["MEDIA_REPO_TOKEN"]
MEDIA_REPO_BRANCH = os.environ.get("MEDIA_REPO_BRANCH", "main")


def _run_git(args: list[str], cwd: str) -> None:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("=== git エラー ===")
        print(" ".join(args))
        print(result.stderr[-4000:])
        raise RuntimeError(f"git {args[0]} に失敗しました")


def push_video_and_get_url(local_path: Path, remote_filename: str) -> str:
    clone_url = f"https://x-access-token:{MEDIA_REPO_TOKEN}@github.com/{MEDIA_REPO}.git"

    with tempfile.TemporaryDirectory() as tmp:
        _run_git(["clone", "--depth", "1", "--branch", MEDIA_REPO_BRANCH, clone_url, tmp], cwd=".")

        reels_dir = Path(tmp) / "reels"
        reels_dir.mkdir(exist_ok=True)

        # 古い動画は公開後は不要なので、リポジトリが肥大化しないよう毎回削除してから追加する
        for old_file in reels_dir.glob("*"):
            if old_file.is_file():
                old_file.unlink()

        dest = reels_dir / remote_filename
        shutil.copy(local_path, dest)

        _run_git(["add", "."], cwd=tmp)
        _run_git(
            ["-c", "user.email=reels-bot@example.com", "-c", "user.name=reels-bot",
             "commit", "-m", f"add {remote_filename}"],
            cwd=tmp,
        )
        _run_git(["push", "origin", f"HEAD:{MEDIA_REPO_BRANCH}"], cwd=tmp)

    return f"https://raw.githubusercontent.com/{MEDIA_REPO}/{MEDIA_REPO_BRANCH}/reels/{remote_filename}"
