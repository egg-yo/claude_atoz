"""
scraper/instagram_scraper.py — RapidAPI 기반 인스타그램 릴스 해시태그 수집
"""
import logging
import requests

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    RAPIDAPI_KEY, RAPIDAPI_HOST,
    INSTAGRAM_HASHTAGS, INSTAGRAM_MAX_RESULTS,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://instagram-scraper-api2.p.rapidapi.com/v1/hashtag"


def fetch_hashtag_reels(hashtag: str, max_results: int = 10) -> list[dict]:
    """특정 해시태그의 최근 릴스 게시물 수집"""
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY가 설정되지 않았습니다.")

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    params = {"hashtag": hashtag}

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.warning(f"[Instagram] #{hashtag} 수집 실패: {e}")
        return []

    items = data.get("data", {}).get("items", [])
    results = []

    for item in items[:max_results]:
        media = item.get("media", item)  # API 응답 구조 대응
        caption_text = ""
        if media.get("caption"):
            caption_text = media["caption"].get("text", "")[:200]

        # 해시태그 파싱
        hashtags = [
            word.lstrip("#")
            for word in caption_text.split()
            if word.startswith("#")
        ]

        results.append({
            "platform": "Instagram",
            "media_id": media.get("id", ""),
            "title": caption_text[:80] or f"#{hashtag} 릴스",
            "username": media.get("user", {}).get("username", ""),
            "published_at": media.get("taken_at_timestamp", ""),
            "thumbnail_url": (
                media.get("image_versions2", {})
                .get("candidates", [{}])[0]
                .get("url", "")
            ),
            "url": f"https://www.instagram.com/reel/{media.get('code', '')}",
            "view_count": media.get("play_count", 0) or media.get("view_count", 0),
            "like_count": media.get("like_count", 0),
            "comment_count": media.get("comment_count", 0),
            "hashtags": hashtags[:10],
            "search_hashtag": hashtag,
        })

    return results


def run() -> list[dict]:
    """외부에서 호출할 메인 진입점"""
    results = []
    for tag in INSTAGRAM_HASHTAGS:
        items = fetch_hashtag_reels(tag, max_results=INSTAGRAM_MAX_RESULTS // len(INSTAGRAM_HASHTAGS) + 1)
        results.extend(items)
        logger.info(f"[Instagram] #{tag} → {len(items)}개 수집")

    # 중복 제거 (media_id 기준)
    seen = set()
    unique = []
    for item in results:
        if item["media_id"] not in seen:
            seen.add(item["media_id"])
            unique.append(item)

    # 조회수 기준 내림차순 정렬
    unique.sort(key=lambda x: x["view_count"], reverse=True)
    logger.info(f"[Instagram] 총 {len(unique)}개 릴스 수집 완료")
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = run()
    for i, item in enumerate(data[:5], 1):
        print(f"{i}. [{item['view_count']:,} views] {item['title']}")
        print(f"   유저: @{item['username']} | URL: {item['url']}")
