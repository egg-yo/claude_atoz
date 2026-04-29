"""
analyzer/trend_analyzer.py — Claude Sonnet 기반 밈 트렌드 분석
수집된 영상 데이터를 AI에 넘겨 TOP 10 선정 + 심층 분석 리포트 생성
"""
import json
import logging
import textwrap
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import CLAUDE_API_KEY, CLAUDE_MODEL, GEMINI_API_KEY, AI_PROVIDER

logger = logging.getLogger(__name__)


def _build_prompt(items: list[dict]) -> str:
    """분석용 프롬프트 작성"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    lines = [f"오늘 날짜: {today}\n총 수집 영상 수: {len(items)}개\n"]

    for i, item in enumerate(items, 1):
        lines.append(
            f"{i}. [{item['platform']}] {item['title']}\n"
            f"   조회수: {item['view_count']:,} | 좋아요: {item['like_count']:,} | 댓글: {item['comment_count']:,}\n"
            f"   URL: {item['url']}\n"
            f"   태그: {', '.join(item.get('tags', []) or item.get('hashtags', []))}\n"
        )

    prompt = textwrap.dedent(f"""
        아래는 이번 주 틱톡과 유튜브 쇼츠에서 수집된 인기 영상 목록입니다.

        {"".join(lines)}

        다음 항목을 분석하여 JSON 형식으로 반환하세요:

        {{
          "top10": [
            {{
              "rank": 1,
              "platform": "YouTube 또는 TikTok",
              "title": "영상 제목",
              "url": "URL",
              "view_count": 숫자,
              "like_count": 숫자,
              "comment_count": 숫자,
              "thumbnail_url": "썸네일 URL",
              "why_trending": "이 영상이 왜 트렌드인지 2~3문장 설명"
            }}
          ],
          "common_patterns": [
            "공통점 1 (예: 공감형 일상 유머, 짧은 반전 구조 등)",
            "공통점 2",
            "공통점 3"
          ],
          "trend_analysis": "이번 주 전체 트렌드를 3~5문장으로 요약. 왜 이런 밈이 유행하는지, 사회·문화적 배경 포함.",
          "content_tips": [
            "콘텐츠 제작자가 참고할 팁 1",
            "팁 2",
            "팁 3",
            "팁 4",
            "팁 5"
          ],
          "hot_keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
          "summary_for_kakao": "카카오톡 발송용 3줄 요약 (이모지 포함, 친근한 말투)"
        }}

        주의:
        - top10은 조회수와 바이럴 지수를 종합하여 선정하세요.
        - 반드시 유효한 JSON만 반환하세요. 다른 텍스트는 포함하지 마세요.
    """).strip()

    return prompt


def analyze(items: list[dict]) -> dict:
    """
    수집된 영상 목록을 AI로 분석하여 트렌드 리포트 반환.
    """
    if not items:
        raise ValueError("분석할 영상 데이터가 없습니다.")

    prompt = _build_prompt(items)

    if AI_PROVIDER == "gemini":
        return _analyze_with_gemini(prompt, items)
    else:
        return _analyze_with_claude(prompt, items)


def _analyze_with_claude(prompt: str, items: list[dict]) -> dict:
    """Anthropic Claude 분석"""
    import anthropic

    if not CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY가 설정되지 않았습니다.")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    logger.info(f"[Analyzer] Claude 분석 시작 ({len(items)}개 영상, 모델: {CLAUDE_MODEL})")

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": "당신은 한국 SNS 트렌드 전문 분석가입니다. 반드시 유효한 JSON만 반환합니다. 다른 텍스트는 절대 포함하지 마세요.",
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    raw = message.content[0].text
    result = json.loads(raw)
    logger.info("[Analyzer] Claude 분석 완료")
    return result


def _analyze_with_gemini(prompt: str, items: list[dict]) -> dict:
    """Google Gemini 분석 (대안)"""
    from google import genai
    from google.genai import types

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    import time

    # 모델 우선순위: 최신 → 안정 순
    model_candidates = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        system_instruction="당신은 한국 SNS 트렌드 전문 분석가입니다. 반드시 유효한 JSON만 반환합니다. 다른 텍스트는 절대 포함하지 마세요.",
        response_mime_type="application/json",
    )

    last_err = None
    response = None
    for model_name in model_candidates:
        logger.info(f"[Analyzer] Gemini 시도 — 모델: {model_name}")
        for attempt in range(1, 3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                break
            except Exception as e:
                last_err = e
                logger.warning(f"[Analyzer] {model_name} 시도 {attempt}/2 실패: {str(e)[:80]}")
                if attempt < 2:
                    time.sleep(5)
        if response:
            logger.info(f"[Analyzer] Gemini 분석 시작 ({len(items)}개 영상, 모델: {model_name})")
            break

    if not response:
        raise last_err

    result = json.loads(response.text)
    logger.info("[Analyzer] Gemini 분석 완료")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 더미 데이터로 테스트
    dummy = [
        {
            "platform": "YouTube", "title": "직장인 공감 밈", "url": "https://youtube.com/watch?v=test1",
            "view_count": 5_200_000, "like_count": 82_000, "comment_count": 3_400,
            "tags": ["직장인", "밈", "공감"], "thumbnail_url": "", "channel": "테스트채널",
        },
        {
            "platform": "TikTok", "title": "요즘 애들 특 #밈", "url": "https://tiktok.com/@test/video/1",
            "view_count": 3_100_000, "like_count": 60_000, "comment_count": 1_200,
            "hashtags": ["밈", "틱톡밈"], "thumbnail_url": "", "username": "test_user",
        },
    ]
    result = analyze(dummy)
    print(json.dumps(result, ensure_ascii=False, indent=2))
