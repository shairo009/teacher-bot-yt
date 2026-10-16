#!/usr/bin/env python3
"""Upload a pre-made video file as a YouTube Short.

Usage:
    python src/upload_custom_short.py --video <path.mp4> --title "..."
        [--description "..."] [--tags "a,b,c"] [--category-id 15]
        [--privacy public|private|unlisted] [--dry-run]

Credentials come from TOKEN_JSON / CLIENT_SECRETS_JSON env vars
(same GitHub secrets the daily bot uses).
"""
import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
TMP_DIR = REPO_ROOT / "tmp"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="Path to .mp4 to upload")
    ap.add_argument("--title", required=True, help="YouTube title (<=100 chars)")
    ap.add_argument("--description", default="", help="YouTube description")
    ap.add_argument("--tags", default="shorts", help="Comma-separated tags")
    ap.add_argument("--category-id", default="15", help="YouTube category id")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "private", "unlisted"])
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate everything without uploading")
    args = ap.parse_args()

    video_path = Path(args.video)
    if not video_path.is_file():
        print(f"Video not found: {video_path}")
        return 1
    size_mb = video_path.stat().st_size / 1e6
    print(f"Video: {video_path} ({size_mb:.1f} MB)")

    title = args.title[:100]
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    print(f"Title: {title}")

    if args.dry_run:
        print("DRY RUN — not uploading.")
        return 0

    token_json = os.environ.get("TOKEN_JSON", "")
    client_json = os.environ.get("CLIENT_SECRETS_JSON", "")
    token_file = TMP_DIR / "token.json"
    client_file = TMP_DIR / "client_secrets.json"
    if token_json and client_json:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        token_file.write_text(token_json, encoding="utf-8")
        client_file.write_text(client_json, encoding="utf-8")
    elif not (token_file.exists() and client_file.exists()):
        print("[No YouTube credentials found in env/files — cannot upload]")
        return 1

    from src.uploader import YouTubeUploader
    uploader = YouTubeUploader(str(token_file), str(client_file))
    video_id = uploader.upload(
        video_path=str(video_path),
        title=title,
        description=args.description,
        tags=tags,
        category_id=args.category_id,
        made_for_kids=False,
        privacy_status=args.privacy,
    )
    if video_id:
        print(f"Uploaded: https://youtu.be/{video_id}")
        return 0
    print("Upload failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
