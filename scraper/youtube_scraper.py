"""
scraper/youtube_scraper.py — YouTube Data API v3로 인기 밈 영상 수집
"""
import logging
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    YOUTUBE_API_KEY, YOUTUBE_REGION_CODE,
    YOUTUBE_MAX_RESULTS, YOUTUBE_SEARCH_KEYWORDS,
)

logger = logging.getLogger(__name__)


def _build_youtube():
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY가 설정되지 않았습니다.")
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def _iso_week_ago() -> str:
    """7일 전 ISO 8601 형식 반환 (YouTube API publishedAfter 파라미터용)"""
    dt = datetime.now(timezone.utc) - timedelta(days=7)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_trending_shorts(youtube) -> list[dict]:
    """YouTube 쇼츠/릴스 유사 인기 영상을 검색 키워드 기반으로 수집"""
    results = []
    published_after = _iso_week_ago()

    for keyword in YOUTUBE_SEARCH_KEYWORDS:
        try:
            response = youtube.search().list(
                part="snippet",
                q=keyword,
                type="video",
                videoDuration="short",          # 60초 이하 쇼츠 필터
                order="viewCount",
                regionCode=YOUTUBE_REGION_CODE,
                publishedAfter=published_after,
                maxResults=min(10, YOUTUBE_MAX_RESULTS),
            ).execute()

            video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
            if not video_ids:
                continue

            # 통계 정보 (조회수, 좋아요 등) 별도 요청
            stats_response = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids),
            ).execute()

            for item in stats_response.get("items", []):
                stats = item.get("statistics", {})
                snippet = item.get("snippet", {})
                results.append({
                    "platform": "YouTube",
                    "video_id": item["id"],
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "description": snippet.get("description", "")[:200],
                    "tags": snippet.get("tags", [])[:10],
                    "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "view_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0)),
                    "search_keyword": keyword,
                })

        except Exception as e:
            logger.warning(f"[YouTube] 키워드 '{keyword}' 수집 실패: {e}")

    # 중복 제거 (video_id 기준)
    seen = set()
    unique = []
    for item in results:
        if item["video_id"] not in seen:
            seen.add(item["video_id"])
            unique.append(item)

    # 조회수 기준 내림차순 정렬
    unique.sort(key=lambda x: x["view_count"], reverse=True)
    logger.info(f"[YouTube] 총 {len(unique)}개 영상 수집 완료")
    return unique


def run() -> list[dict]:
    """외부에서 호출할 메인 진입점"""
    youtube = _build_youtube()
    return fetch_trending_shorts(youtube)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = run()
    for i, item in enumerate(data[:5], 1):
        print(f"{i}. [{item['view_count']:,} views] {item['title']}")
        print(f"   채널: {item['channel']} | URL: {item['url']}")
