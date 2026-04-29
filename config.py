"""
config.py — 전역 설정값
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── YouTube ──────────────────────────────────────────────────
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# YouTube 트렌드 수집 설정
YOUTUBE_REGION_CODE = "KR"          # 한국 트렌드
YOUTUBE_MAX_RESULTS = 30            # 최초 수집 개수 (TOP 10 선정 전 후보군)
YOUTUBE_ORDER = "viewCount"         # date | viewCount | relevance
# 검색 키워드 목록 (해당 키워드로 최근 7일 인기 영상 수집)
YOUTUBE_SEARCH_KEYWORDS = [
    "밈", "meme", "쇼츠 밈", "reels meme", "trending shorts",
    "유행", "인터넷 밈", "챌린지",
]

# ── TikTok (비공식, 무료) ─────────────────────────────────────
TIKTOK_MAX_RESULTS = 30             # 수집 후보군 수

# ── AI 분석 ──────────────────────────────────────────────────
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # 선택적 대안

# AI 제공자 선택: "claude" | "gemini"
AI_PROVIDER = os.getenv("AI_PROVIDER", "claude").lower()

TOP_N = 10                          # 최종 선정 TOP N

# ── 카카오톡 ─────────────────────────────────────────────────
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:5000/callback")
KAKAO_TOKEN_FILE = ".kakao_tokens.json"  # 토큰 로컬 저장 경로

# ── GitHub Pages ──────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")   # "username/meme-trend-archive"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "gh-pages")

# ── 아카이브 로컬 저장 경로 ────────────────────────────────────
ARCHIVE_DIR = "archive"
