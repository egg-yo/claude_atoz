"""
main.py — 전체 파이프라인 진입점
실행: python main.py
"""
import logging
import sys
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("meme_trend_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def run_pipeline():
    start = datetime.now()
    logger.info("=" * 50)
    logger.info(f"🚀 밈 트렌드 봇 시작: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # ── 1. 데이터 수집 ────────────────────────────────────────
    from scraper import youtube_scraper, tiktok_scraper

    logger.info("[1/4] 데이터 수집 시작")
    yt_items = []
    tt_items = []

    try:
        yt_items = youtube_scraper.run()
        logger.info(f"  ✅ YouTube: {len(yt_items)}개 수집")
    except Exception as e:
        logger.error(f"  ❌ YouTube 수집 실패: {e}")

    try:
        tt_items = tiktok_scraper.run()
        logger.info(f"  ✅ TikTok: {len(tt_items)}개 수집")
    except Exception as e:
        logger.error(f"  ❌ TikTok 수집 실패: {e}")

    all_items = yt_items + tt_items
    if not all_items:
        logger.error("수집된 데이터가 없습니다. 파이프라인을 중단합니다.")
        sys.exit(1)

    logger.info(f"  📦 총 수집: {len(all_items)}개")

    # ── 2. AI 분석 ────────────────────────────────────────────
    from analyzer.trend_analyzer import analyze

    logger.info("[2/4] AI 트렌드 분석 시작")
    analysis = analyze(all_items)
    logger.info(f"  ✅ 분석 완료 — TOP {len(analysis.get('top10', []))}개 선정")

    # ── 3. HTML 리포트 저장 ────────────────────────────────────
    from reporter.html_reporter import save as save_report

    logger.info("[3/4] HTML 리포트 생성")
    html_path = save_report(analysis)
    logger.info(f"  ✅ 저장 완료: {html_path}")

    # GitHub Pages에 배포 (토큰이 있을 때만)
    report_url = _deploy_to_github_pages(html_path)

    # ── 4. 카카오톡 발송 ──────────────────────────────────────
    from notifier.kakao_notifier import send as send_kakao

    logger.info("[4/4] 카카오톡 발송")
    try:
        send_kakao(analysis, report_url=report_url)
        logger.info("  ✅ 카카오톡 발송 완료")
    except Exception as e:
        logger.error(f"  ❌ 카카오톡 발송 실패: {e}")

    elapsed = (datetime.now() - start).seconds
    logger.info(f"\n🎉 파이프라인 완료! (소요 시간: {elapsed}초)")
    logger.info(f"📄 리포트: {html_path}")


from typing import Optional

def _deploy_to_github_pages(html_path: str) -> Optional[str]:
    """
    HTML 파일을 GitHub Pages 브랜치에 push.
    GITHUB_TOKEN 과 GITHUB_REPO 가 설정된 경우에만 실행.
    """
    from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH

    if not GITHUB_TOKEN or not GITHUB_REPO:
        logger.info("  ⏭️  GitHub Pages 배포 건너뜀 (GITHUB_TOKEN/GITHUB_REPO 미설정)")
        return None

    try:
        from github import Github

        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 파일명: index.html (최신 리포트) + 주차별 아카이브
        week_dir = os.path.basename(os.path.dirname(html_path))  # e.g. 2026-W15
        gh_path_archive = f"{week_dir}/report.html"
        gh_path_index = "index.html"

        commit_msg = f"📊 {week_dir} 밈 트렌드 리포트 업데이트"

        for gh_path in [gh_path_archive, gh_path_index]:
            try:
                existing = repo.get_contents(gh_path, ref=GITHUB_BRANCH)
                repo.update_file(gh_path, commit_msg, content, existing.sha, branch=GITHUB_BRANCH)
            except Exception:
                repo.create_file(gh_path, commit_msg, content, branch=GITHUB_BRANCH)

        report_url = f"https://{GITHUB_REPO.split('/')[0]}.github.io/{GITHUB_REPO.split('/')[1]}/{week_dir}/report.html"
        logger.info(f"  ✅ GitHub Pages 배포 완료: {report_url}")
        return report_url

    except Exception as e:
        logger.warning(f"  ⚠️  GitHub Pages 배포 실패: {e}")
        return None


if __name__ == "__main__":
    run_pipeline()
