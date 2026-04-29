"""
reporter/html_reporter.py — 분석 결과를 주차별 HTML 리포트로 저장
"""
import os
import logging
from datetime import datetime
from jinja2 import Template

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import ARCHIVE_DIR

logger = logging.getLogger(__name__)

# ── HTML 템플릿 ─────────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🔥 주간 밈 트렌드 {{ week_label }}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Noto Sans KR', sans-serif;
      background: #0f0f13;
      color: #e8e8f0;
      min-height: 100vh;
    }
    header {
      background: linear-gradient(135deg, #6c47ff, #ff4fa3);
      padding: 40px 24px;
      text-align: center;
    }
    header h1 { font-size: 2rem; font-weight: 800; color: #fff; }
    header p  { font-size: 0.95rem; color: rgba(255,255,255,0.8); margin-top: 8px; }
    .badge {
      display: inline-block;
      background: rgba(255,255,255,0.2);
      border-radius: 20px;
      padding: 4px 14px;
      font-size: 0.8rem;
      margin-top: 10px;
    }
    main { max-width: 960px; margin: 0 auto; padding: 32px 16px 60px; }
    .section-title {
      font-size: 1.3rem; font-weight: 700;
      margin: 36px 0 16px;
      display: flex; align-items: center; gap: 10px;
    }
    .section-title::after {
      content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.1);
    }
    /* ── TOP 10 카드 ── */
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 18px; }
    .card {
      background: #1a1a24;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.07);
      transition: transform .2s, box-shadow .2s;
      text-decoration: none; color: inherit;
      display: block;
    }
    .card:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(108,71,255,0.25); }
    .card-thumb {
      width: 100%; aspect-ratio: 16/9; object-fit: cover;
      background: #2a2a38;
    }
    .card-thumb-placeholder {
      width: 100%; aspect-ratio: 16/9;
      background: linear-gradient(135deg, #2a2a38, #1e1e2e);
      display: flex; align-items: center; justify-content: center;
      font-size: 2.5rem;
    }
    .card-body { padding: 14px 16px; }
    .card-rank {
      font-size: 0.7rem; font-weight: 700; color: #6c47ff;
      text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;
    }
    .card-title { font-size: 0.95rem; font-weight: 600; line-height: 1.4; margin-bottom: 10px; }
    .card-stats {
      display: flex; gap: 12px;
      font-size: 0.78rem; color: #8888aa;
    }
    .card-stats span { display: flex; align-items: center; gap: 4px; }
    .card-why {
      margin-top: 10px;
      font-size: 0.8rem; color: #aaaacc;
      line-height: 1.5;
      border-top: 1px solid rgba(255,255,255,0.07);
      padding-top: 10px;
    }
    .platform-badge {
      display: inline-block; font-size: 0.68rem; font-weight: 700;
      padding: 2px 8px; border-radius: 10px; margin-bottom: 6px;
    }
    .platform-yt { background: rgba(255,0,0,0.2); color: #ff6060; }
    .platform-ig { background: rgba(255,79,163,0.2); color: #ff4fa3; }
    /* ── 분석 섹션 ── */
    .analysis-box {
      background: #1a1a24;
      border-radius: 14px;
      padding: 22px 24px;
      border: 1px solid rgba(255,255,255,0.07);
    }
    .analysis-box p { line-height: 1.8; color: #ccccde; font-size: 0.93rem; }
    .tag-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
    .tag {
      background: rgba(108,71,255,0.2); color: #a08fff;
      border-radius: 20px; padding: 5px 14px;
      font-size: 0.83rem; font-weight: 600;
    }
    .tips-list { list-style: none; }
    .tips-list li {
      padding: 10px 0;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      font-size: 0.9rem; color: #ccccde; line-height: 1.6;
    }
    .tips-list li:last-child { border-bottom: none; }
    .tips-list li::before {
      content: '✦'; color: #6c47ff;
      display: inline-block; width: 20px;
    }
    .pattern-list { list-style: none; }
    .pattern-list li {
      padding: 9px 0;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      font-size: 0.9rem; color: #ccccde;
    }
    .pattern-list li::before { content: '→ '; color: #ff4fa3; font-weight: 700; }
    footer {
      text-align: center; color: #444; font-size: 0.8rem;
      padding: 30px;
    }
  </style>
</head>
<body>
<header>
  <h1>🔥 주간 밈 트렌드 리포트</h1>
  <p>인스타그램 릴스 &amp; 유튜브 쇼츠 TOP {{ top10 | length }}</p>
  <span class="badge">{{ week_label }} · {{ generated_at }}</span>
</header>

<main>
  <!-- TOP 10 카드 그리드 -->
  <div class="section-title">🏆 TOP {{ top10 | length }} 이번 주 밈</div>
  <div class="grid">
    {% for item in top10 %}
    <a class="card" href="{{ item.url }}" target="_blank" rel="noopener">
      {% if item.thumbnail_url %}
        <img class="card-thumb" src="{{ item.thumbnail_url }}" alt="{{ item.title }}" loading="lazy">
      {% else %}
        <div class="card-thumb-placeholder">{% if item.platform == 'YouTube' %}▶{% else %}📸{% endif %}</div>
      {% endif %}
      <div class="card-body">
        <span class="platform-badge {% if item.platform == 'YouTube' %}platform-yt{% else %}platform-ig{% endif %}">
          {{ item.platform }}
        </span>
        <div class="card-rank"># {{ item.rank }}</div>
        <div class="card-title">{{ item.title }}</div>
        <div class="card-stats">
          <span>👁 {{ "{:,}".format(item.view_count) }}</span>
          <span>❤️ {{ "{:,}".format(item.like_count) }}</span>
          <span>💬 {{ "{:,}".format(item.comment_count) }}</span>
        </div>
        {% if item.why_trending %}
        <div class="card-why">{{ item.why_trending }}</div>
        {% endif %}
      </div>
    </a>
    {% endfor %}
  </div>

  <!-- 트렌드 분석 -->
  <div class="section-title">📊 이번 주 트렌드 분석</div>
  <div class="analysis-box">
    <p>{{ trend_analysis }}</p>
  </div>

  <!-- 공통점 -->
  <div class="section-title">🔗 공통 패턴</div>
  <div class="analysis-box">
    <ul class="pattern-list">
      {% for pattern in common_patterns %}
      <li>{{ pattern }}</li>
      {% endfor %}
    </ul>
  </div>

  <!-- 핫 키워드 -->
  <div class="section-title">🏷️ 이번 주 핫 키워드</div>
  <div class="analysis-box">
    <div class="tag-list">
      {% for kw in hot_keywords %}
      <span class="tag"># {{ kw }}</span>
      {% endfor %}
    </div>
  </div>

  <!-- 콘텐츠 제작 팁 -->
  <div class="section-title">💡 콘텐츠 제작 인사이트</div>
  <div class="analysis-box">
    <ul class="tips-list">
      {% for tip in content_tips %}
      <li>{{ tip }}</li>
      {% endfor %}
    </ul>
  </div>
</main>

<footer>
  🤖 자동 생성 — {{ generated_at }} · Meme Trend Bot
</footer>
</body>
</html>"""


def _get_week_label() -> str:
    """현재 주차 레이블 반환 (예: 2026-W15)"""
    now = datetime.now()
    return now.strftime("%Y-W%W")


def save(analysis: dict) -> str:
    """
    분석 결과를 HTML로 렌더링하여 archive/{week_label}/report.html 에 저장.

    Returns:
        str: 저장된 HTML 파일 경로
    """
    week_label = _get_week_label()
    generated_at = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    # 폴더 생성
    output_dir = os.path.join(ARCHIVE_DIR, week_label)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "report.html")

    template = Template(HTML_TEMPLATE)
    html = template.render(
        week_label=week_label,
        generated_at=generated_at,
        top10=analysis.get("top10", []),
        trend_analysis=analysis.get("trend_analysis", ""),
        common_patterns=analysis.get("common_patterns", []),
        hot_keywords=analysis.get("hot_keywords", []),
        content_tips=analysis.get("content_tips", []),
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"[Reporter] HTML 리포트 저장 완료: {output_path}")
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 더미 데이터 테스트
    dummy_analysis = {
        "top10": [
            {
                "rank": 1, "platform": "YouTube", "title": "직장인 공감 밈 테스트",
                "url": "https://youtube.com", "view_count": 5_200_000,
                "like_count": 82_000, "comment_count": 3_400,
                "thumbnail_url": "", "why_trending": "직장인의 숨막히는 일상을 짧게 담아 폭발적 공감을 얻었습니다.",
            },
        ],
        "trend_analysis": "이번 주는 직장인 공감형 밈과 짧은 반전 유머가 주를 이뤘습니다.",
        "common_patterns": ["짧은 반전 구조 (15초 이내)", "공감형 일상 소재"],
        "hot_keywords": ["직장인", "공감", "쇼츠", "밈", "챌린지"],
        "content_tips": ["영상을 15초 이내로 제한하세요.", "첫 3초에 후킹 요소를 배치하세요."],
    }
    path = save(dummy_analysis)
    print(f"저장 완료: {path}")
