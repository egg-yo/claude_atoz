# 🔥 Meme Trend Bot

매주 **인스타그램 릴스 + 유튜브 쇼츠**에서 인기 밈 TOP 10을 자동 수집·분석하여
HTML 리포트로 아카이빙하고 **카카오톡**으로 발송하는 자동화 봇입니다.

---

## 📁 프로젝트 구조

```
meme_trend_bot/
├── main.py                        # 전체 파이프라인 진입점
├── config.py                      # 설정값 & 환경변수 로딩
├── requirements.txt
├── .env.example                   # API 키 템플릿
│
├── scraper/
│   ├── youtube_scraper.py         # YouTube Data API v3
│   └── tiktok_scraper.py          # TikTok 트렌딩 (비공식, 무료)
│
├── analyzer/
│   └── trend_analyzer.py          # Claude Sonnet 트렌드 분석
│
├── reporter/
│   └── html_reporter.py           # HTML 리포트 생성
│
├── notifier/
│   └── kakao_notifier.py          # 카카오톡 발송 (OAuth 2.0)
│
├── archive/                       # 주차별 HTML 저장
│   └── 2026-W15/report.html
│
└── .github/workflows/
    └── weekly_run.yml             # GitHub Actions 스케줄러
```

---

## ⚡ 빠른 시작

### 1. 의존성 설치

```bash
cd toy_project/meme_trend_bot
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 각 API 키 입력
```

### 3. 카카오톡 1회 인증 (최초만)

```bash
python notifier/kakao_notifier.py
# 브라우저가 자동으로 열리며 카카오 로그인 화면이 나타납니다.
# 로그인 후 .kakao_tokens.json 에 토큰이 저장됩니다.
# 이후 실행 시 자동 갱신되므로 재인증 불필요
```

### 4. 수동 실행

```bash
python main.py
```

---

## 🔑 필요한 API 키

| API | 발급처 | 비용 |
|-----|--------|------|
| YouTube Data API v3 | [Google Cloud Console](https://console.cloud.google.com/) | 무료 |
| TikTok 스크래핑 | 별도 키 없음 (Playwright 기반) | 무료 |
| Claude API (Sonnet) | [Anthropic Console](https://console.anthropic.com/) | 사용량 기반 |
| 카카오 REST API | [Kakao Developers](https://developers.kakao.com/) | 무료 |
| GitHub Token (선택) | GitHub Settings > Tokens | 무료 |

---

## 📅 자동 스케줄 (GitHub Actions)

`.github/workflows/weekly_run.yml` 을 GitHub 저장소에 push하면
**매주 월요일 오전 10시 KST**에 자동 실행됩니다.

GitHub 저장소 → **Settings > Secrets** 에 `.env` 의 모든 키를 등록하세요.

수동 실행: 저장소 → **Actions** 탭 → `Weekly Meme Trend Bot` → **Run workflow**

---

## 📦 각 모듈 단독 테스트

```bash
# 유튜브 데이터 수집 확인
python scraper/youtube_scraper.py

# 인스타그램 데이터 수집 확인
python scraper/instagram_scraper.py

# AI 분석 결과 확인 (더미 데이터)
python analyzer/trend_analyzer.py

# HTML 리포트 생성 확인
python reporter/html_reporter.py

# 카카오톡 발송 테스트
python notifier/kakao_notifier.py
```

---

## 🗂️ 아카이브 구조

```
archive/
├── 2026-W14/report.html
├── 2026-W15/report.html
└── ...
```

GitHub Pages로 배포 시 `https://{username}.github.io/{repo}/2026-W15/report.html` 형태로 접근 가능합니다.

---

## ⚙️ 설정 커스터마이징

`config.py` 에서 아래 항목을 수정할 수 있습니다:

| 항목 | 기본값 | 설명 |
|------|--------|------|
| `YOUTUBE_SEARCH_KEYWORDS` | `["밈", "meme", ...]` | 유튜브 검색 키워드 |
| `YOUTUBE_MAX_RESULTS` | `30` | 유튜브 수집 후보군 수 |
| `TIKTOK_MAX_RESULTS` | `30` | 틱톡 수집 후보군 수 |
| `CLAUDE_MODEL` | `"claude-sonnet-4-6"` | 분석 AI 모델 |
| `TOP_N` | `10` | 최종 선정 TOP N |
