"""
scraper/tiktok_scraper.py — TikTokApi(비공식, 무료)를 이용한 틱톡 트렌딩 영상 수집
Playwright 기반으로 실제 브라우저처럼 동작하여 anti-bot 우회.

설치 (최초 1회):
    pip install TikTokApi playwright
    playwright install chromium
"""
import asyncio
import logging

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import TIKTOK_MAX_RESULTS

logger = logging.getLogger(__name__)


async def _fetch_trending_async(max_results: int) -> list[dict]:
    try:
        from TikTokApi import TikTokApi
    except ImportError:
        raise ImportError(
            "TikTokApi가 설치되지 않았습니다.\n"
            "  pip install TikTokApi playwright\n"
            "  playwright install chromium"
        )

    results = []

    async with TikTokApi() as api:
        await api.create_sessions(
            num_sessions=1,
            sleep_after=3,
            headless=True,
        )

        async for video in api.trending.videos(count=max_results):
            try:
                info = video.as_dict
                author = info.get("author", {})
                stats = info.get("stats", {})
                hashtags = [
                    tag.get("hashtagName", "")
                    for tag in info.get("textExtra", [])
                    if tag.get("hashtagType") == 1
                ]
                results.append({
                    "platform": "TikTok",
                    "video_id": info.get("id", ""),
                    "title": info.get("desc", "")[:200] or "TikTok 트렌딩",
                    "username": author.get("uniqueId", ""),
                    "published_at": str(info.get("createTime", "")),
                    "thumbnail_url": info.get("video", {}).get("cover", ""),
                    "url": f"https://www.tiktok.com/@{author.get('uniqueId', '')}/video/{info.get('id', '')}",
                    "view_count": stats.get("playCount", 0),
                    "like_count": stats.get("diggCount", 0),
                    "comment_count": stats.get("commentCount", 0),
                    "hashtags": hashtags[:10],
                })
            except Exception as e:
                logger.warning(f"[TikTok] 영상 파싱 실패: {e}")

    results.sort(key=lambda x: x["view_count"], reverse=True)
    logger.info(f"[TikTok] 총 {len(results)}개 트렌딩 영상 수집 완료")
    return results


def run() -> list[dict]:
    """외부에서 호출할 메인 진입점"""
    return asyncio.run(_fetch_trending_async(TIKTOK_MAX_RESULTS))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = run()
    for i, item in enumerate(data[:5], 1):
        print(f"{i}. [{item['view_count']:,} views] {item['title']}")
        print(f"   @{item['username']} | URL: {item['url']}")
