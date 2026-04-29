"""
notifier/kakao_notifier.py — 카카오톡 '나에게 보내기' API 활용
OAuth 2.0 토큰 관리 + 메시지 발송
"""
import json
import logging
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from typing import Optional

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    KAKAO_REST_API_KEY, KAKAO_CLIENT_SECRET, KAKAO_REDIRECT_URI, KAKAO_TOKEN_FILE,
)

logger = logging.getLogger(__name__)

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_MSG_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


# ── 토큰 관리 ──────────────────────────────────────────────────────────────────

def _load_tokens() -> dict:
    if os.path.exists(KAKAO_TOKEN_FILE):
        with open(KAKAO_TOKEN_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_tokens(tokens: dict):
    with open(KAKAO_TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    logger.info("[Kakao] 토큰 저장 완료")


def _refresh_access_token(refresh_token: str) -> dict:
    """refresh_token으로 access_token 갱신"""
    data = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_API_KEY,
        "refresh_token": refresh_token,
    }
    if KAKAO_CLIENT_SECRET:
        data["client_secret"] = KAKAO_CLIENT_SECRET
    resp = requests.post(KAKAO_TOKEN_URL, data=data)
    resp.raise_for_status()
    new_tokens = resp.json()
    tokens = _load_tokens()
    tokens["access_token"] = new_tokens["access_token"]
    if "refresh_token" in new_tokens:
        tokens["refresh_token"] = new_tokens["refresh_token"]
    _save_tokens(tokens)
    return tokens


def _get_access_token() -> str:
    """
    저장된 토큰 반환. 없으면 OAuth 인증 플로우 시작.
    refresh_token이 있으면 자동 갱신.
    """
    tokens = _load_tokens()

    if not tokens:
        return _run_oauth_flow()

    if tokens.get("refresh_token"):
        try:
            tokens = _refresh_access_token(tokens["refresh_token"])
            logger.info("[Kakao] access_token 자동 갱신 완료")
        except Exception as e:
            logger.warning(f"[Kakao] 토큰 갱신 실패, 재인증 필요: {e}")
            return _run_oauth_flow()

    return tokens["access_token"]


def _run_oauth_flow() -> str:
    """
    로컬 HTTP 서버를 열어 카카오 OAuth 인증 코드를 받는 1회성 플로우.
    브라우저를 자동으로 열어줍니다.
    """
    auth_url = (
        f"{KAKAO_AUTH_URL}"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=talk_message"
    )

    auth_code_holder = []

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            code = query.get("code", [None])[0]
            if code:
                auth_code_holder.append(code)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h2>Kakao OAuth \uc131\uacf5! \uc774 \ud0ed\uc744 \ub2eb\uc544\ub3c4 \ub429\ub2c8\ub2e4.</h2>")
            else:
                self.send_response(400)
                self.end_headers()
        def log_message(self, *_): pass  # 불필요한 로그 억제

    port = int(KAKAO_REDIRECT_URI.split(":")[-1].split("/")[0])
    server = HTTPServer(("", port), _Handler)

    print(f"\n[Kakao] 브라우저에서 카카오 로그인을 진행하세요:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server.handle_request()  # 인증 코드 수신 후 즉시 종료

    if not auth_code_holder:
        raise RuntimeError("카카오 OAuth 인증 코드를 받지 못했습니다.")

    code = auth_code_holder[0]

    # 코드 → 토큰 교환
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    if KAKAO_CLIENT_SECRET:
        token_data["client_secret"] = KAKAO_CLIENT_SECRET
    resp = requests.post(KAKAO_TOKEN_URL, data=token_data)
    resp.raise_for_status()
    tokens = resp.json()
    _save_tokens(tokens)
    logger.info("[Kakao] 최초 인증 완료, 토큰 저장")
    return tokens["access_token"]


# ── 메시지 발송 ─────────────────────────────────────────────────────────────────

def _build_message(analysis: dict, report_url: Optional[str] = None) -> dict:
    """카카오톡 피드 메시지 오브젝트 생성"""
    summary = analysis.get("summary_for_kakao", "이번 주 밈 트렌드 분석이 완료됐어요!")
    top1 = analysis.get("top10", [{}])[0]
    keywords = " ".join([f"#{kw}" for kw in analysis.get("hot_keywords", [])[:5]])

    template = {
        "object_type": "feed",
        "content": {
            "title": f"🔥 이번 주 밈 TOP 10 분석 완료!",
            "description": f"{summary}\n\n{keywords}",
            "image_url": top1.get("thumbnail_url", ""),
            "image_width": 640,
            "image_height": 360,
            "link": {
                "web_url": report_url or "https://github.com",
                "mobile_web_url": report_url or "https://github.com",
            },
        },
        "buttons": [],
    }

    if report_url:
        template["buttons"].append({
            "title": "📄 전체 리포트 보기",
            "link": {
                "web_url": report_url,
                "mobile_web_url": report_url,
            },
        })

    return template


def send(analysis: dict, report_url: Optional[str] = None):
    """
    카카오톡 나에게 메시지 보내기.

    Args:
        analysis: trend_analyzer.analyze() 반환값
        report_url: HTML 리포트 공개 URL (GitHub Pages 등), 없으면 생략
    """
    if not KAKAO_REST_API_KEY:
        raise ValueError("KAKAO_REST_API_KEY가 설정되지 않았습니다.")

    access_token = _get_access_token()
    message = _build_message(analysis, report_url)

    resp = requests.post(
        KAKAO_MSG_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(message, ensure_ascii=False)},
    )

    if resp.status_code == 200 and resp.json().get("result_code") == 0:
        logger.info("[Kakao] 메시지 발송 성공 ✅")
    else:
        logger.error(f"[Kakao] 발송 실패: {resp.status_code} {resp.text}")
        resp.raise_for_status()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dummy_analysis = {
        "summary_for_kakao": "이번 주 밈은 직장인 공감 유머가 대세 🏢😂\n짧은 반전 구조가 핵심!\n콘텐츠 제작 팁 → 전체 리포트 참고!",
        "hot_keywords": ["직장인", "공감", "쇼츠", "밈", "반전"],
        "top10": [{"thumbnail_url": "", "url": "https://youtube.com"}],
    }
    send(dummy_analysis, report_url=None)
