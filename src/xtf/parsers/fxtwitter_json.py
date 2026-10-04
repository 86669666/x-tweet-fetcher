"""Parsers for FxTwitter API JSON responses. Pure functions."""
from __future__ import annotations

from typing import Any


def extract_media(tweet_obj: dict[str, Any]) -> dict[str, Any] | None:
    """Extract media information (photos/videos) from tweet object."""
    media_data = {}
    media = tweet_obj.get("media")
    if not isinstance(media, dict):
        return None

    all_media = media.get("all") or []
    if not isinstance(all_media, list):
        all_media = []
    if all_media:
        photos = [
            item for item in all_media
            if isinstance(item, dict) and item.get("type") == "photo"
        ]
        if photos:
            media_data["images"] = []
            for photo in photos:
                image_info = {"url": photo.get("url", "")}
                if photo.get("width"):
                    image_info["width"] = photo.get("width")
                if photo.get("height"):
                    image_info["height"] = photo.get("height")
                media_data["images"].append(image_info)

    videos = media.get("videos") or []
    if isinstance(videos, list) and len(videos) > 0:
        media_data["videos"] = []
        for video in videos:
            if not isinstance(video, dict):
                continue
            video_info = {}
            if video.get("url"):
                video_info["url"] = video.get("url")
            if video.get("duration"):
                video_info["duration"] = video.get("duration")
            if video.get("thumbnail_url"):
                video_info["thumbnail"] = video.get("thumbnail_url")
            if video.get("variants") and isinstance(video.get("variants"), list):
                video_info["variants"] = []
                for variant in video.get("variants", []):
                    if not isinstance(variant, dict):
                        continue
                    variant_info = {}
                    if variant.get("url"):
                        variant_info["url"] = variant.get("url")
                    if variant.get("bitrate"):
                        variant_info["bitrate"] = variant.get("bitrate")
                    if variant.get("content_type"):
                        variant_info["content_type"] = variant.get("content_type")
                    if variant_info:
                        video_info["variants"].append(variant_info)
            if video_info:
                media_data["videos"].append(video_info)

    return media_data if media_data else None

