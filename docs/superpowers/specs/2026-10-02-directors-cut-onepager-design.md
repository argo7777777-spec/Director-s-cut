# Director's Cut 외부 공개 원페이지 — 설계

- 작성일: 2026-10-02
- 상태: 설계 확정, 구현 계획 대기
- 원본 초안: https://claude.ai/artifact/U4Zjs9PrNyGWGn56o7ieja (Sourcing TF Draft v1, 다크 문서형 7섹션)

## 1. 목표

내부 초안을 **외부 게임사에 공유하는 소개자료**로 다시 만든다. 내용은 초안 그대로(전부 공개 가능 정보), 디자인과 전달 형식만 바꾼다.

성공 기준:
- 링크를 받은 사람이 클릭 즉시 PC·폰에서 읽을 수 있다 (다운로드 없이)
- 한국어·영어 두 버전이 같은 내용으로 존재한다
- 원스토어 브랜드와 어긋나지 않으면서 "감독판" 분위기가 산다

## 2. 확정 결정

| 항목 | 결정 | 이유 |
|---|---|---|
| 독자·언어 | 국내 퍼블리셔 + 해외 개발사, **한/영** | DC Zone은 글로벌 전용(대한민국 제외) |
| 성격 | **하이브리드** — 상단 랜딩, 하단 가이드 | 첫 접점은 매력, 실무자는 바로 설정 정보 |
| 톤 | **C안** — 다크 네이비 히어로 + 라이트 가이드 | 원스토어 앱 혜택탭의 다크 네이비·보라/레드 배지 문법 차용 → 브랜드 이탈 없이 분위기 확보 |
| 배포 | OneDrive 업로드 + 외부 공개(Anyone) 링크 | 사용자 결정 |
| 대표 형식 | **PDF** (HTML은 부록 다운로드) | OneDrive 웹 뷰어는 HTML을 렌더하지 않고 다운로드시킴. PDF는 바로 렌더 |
| PDF 형태 | **긴 한 장** (폭 800px, 높이 = 콘텐츠 실측) | "원페이지" 그대로, 웹 레이아웃과 1벌 |
| 폰트 | Paperlogy (`D:\Claude\AXTF\Font`) | 사용자 지정 |
| 로고 | onestorecorp.com/brand 워드마크 PNG를 잘라 임시 사용 | SVG 원본 미제공. 정식 파일은 UXD그룹(onestorebrand@onestorecorp.com) 요청 후 교체 |
| 제작 방식 | Claude Code로 HTML 작성 → Playwright로 PDF 출력 | 한 소스에서 KO/EN PDF + HTML 동시 생성, 수정 후 재빌드만 하면 됨 |

기각한 대안: Figma/Canva(한/영 2벌 수작업), AI 원페이지 빌더(템플릿 티, 외부 SaaS 업로드, 폰트 제어 한계), A4 다중 페이지(원페이지 성격과 거리), 폭 1080px(폰에서 본문 ≈6px).

## 3. 페이지 구조 (위→아래)

**다크 구간 (랜딩)**
1. 헤더 — ONE store 워드마크(흰색) · KO|EN 토글(HTML에서만 표시)
2. 히어로 — `19+` `GLOBAL` 배지, 제목 "Director's Cut Zone", 한 줄 정의, CTA 2개(원콘솔 바로가기 / 설정 가이드↓)
3. 핵심 키워드 3칸 — 전용 노출 · 전용 프로모션 · 글로벌 배포
4. 01 개요 — 정의 2문단, "자기 선언형 메타 정보 / 법적 책임은 게임사" 강조 박스, 영상 썸네일 카드(YouTube 링크)
5. 02 지원 사항 — 혜택 카드(전용 노출 지면 / 정기 프로모션 / 추가 혜택) + Zone 폰 목업

**전환** — 다크→라이트 그라데이션 띠

**라이트 구간 (가이드)**
6. 03 설정 방법 — 경로 브레드크럼, 원콘솔 토글 스크린샷, 4단계 스텝
7. 04 주의사항 — 가이드 링크 카드 2개(19+ Game Guide, 제한된 콘텐츠) + 반려·판매불가 경고 박스
8. 05 배포 가능 국가 · 06 서비스 이용료율 — 2단 나란히. 국가 칩(대한민국=대상 아님, 미지원 4개국 강조) | 이용료 요약 카드
9. 07 활성화 가이드 — 채널 카드 2열 그리드(5개) + 숏링크 `https://onesto.re/{PID}` 코드 박스
10. 푸터(다크 네이비) — 워드마크, 개발자센터 링크, 기준일

### Zone 폰 목업
초안의 SVG 목업을 원스토어 앱 UI 문법으로 다시 그린다: 탭바와 언더라인, 원형 `19` 배지, 둥근 썸네일 카드, 랭킹 리스트, 프로모션 배너. 게임 썸네일은 **추상 그라데이션 자리표시**만 쓴다(`screenshot/`의 타사 게임 아트는 권리 문제로 쓰지 않음, 스크린샷은 UI 문법 참고용).

### 시각 토큰
- 다크: 배경 `#1b1d3a`→`#16182f`, 보라 `#6b4cff`, 레드 `#e8204a`, 본문 대비 WCAG AA 이상
- 라이트: 배경 `#ffffff`/`#f6f6fb`, 잉크 `#1b1d3a`, 섹션 번호 레드
- 타이포: Paperlogy 400/600/800 기준(필요 시 구현 중 1개 웨이트 추가 가능), 본문 17~18px, 섹션 번호는 작은 레이블
- 배지 모양은 앱 스크린샷 기준(작은 둥근 사각, 굵은 흰 글자)

## 4. 파일 구성

```
24_Director's cut/
├─ src/
│  ├─ index.html     본문. 문단마다 <span lang="ko">…</span><span lang="en">…</span>
│  ├─ style.css      토큰·레이아웃·@font-face(로컬 TTF 경로)
│  └─ assets/        logo-w.png, logo-b.png, dc-video-thumb.jpg, directors-cut-toggle.png
├─ build/
│  ├─ build.py       → dist/DirectorsCut.html (단일 파일)
│  └─ pdf.js         → dist/DirectorsCut_KO.pdf, DirectorsCut_EN.pdf
└─ dist/             OneDrive 업로드 대상 (git 무시)
```

- 이미지 2장(`dc-video-thumb.jpg`, `directors-cut-toggle.png`)은 원본 아티팩트의 published files에서 회수한다.
- 언어 전환: `<html data-lang="ko|en">` + CSS로 비활성 언어 숨김. 초기값은 `?lang=` 쿼리, 없으면 `ko`. 토글 버튼이 `data-lang`만 바꾼다. 번역 사전·템플릿 엔진 없음.

### build.py
1. `src/index.html`에 `style.css`를 인라인
2. 이미지를 base64 data URI로 인라인
3. 본문 전체 텍스트(KO+EN)를 모아 Paperlogy 각 웨이트를 fontTools로 서브셋 → WOFF2 → base64 `@font-face` 인라인 (`brotli` 패키지 필수 — 없으면 WOFF2 저장이 조용히 실패하므로 설치 확인)
4. 검사: 한/영 짝이 안 맞는 요소가 있으면 **실패**, `.placeholder`가 남아 있으면 **경고**
5. `dist/DirectorsCut.html` 저장 (외부 요청 0개)

### pdf.js
Playwright(Chromium)로 `dist/DirectorsCut.html?lang=ko|en`을 폭 800px로 열고, 폰트 로드 완료 대기 후 `document.documentElement.scrollHeight`를 재서 `page.pdf({width:'800px', height:<실측>px, printBackground:true})`. 인쇄 시 토글 버튼은 숨긴다.

## 5. 콘텐츠

- 국문: 초안 문구 그대로. `onestore-text` MCP로 맞춤법·브랜드 표기만 점검(의미 변경 없음).
- 영문: Claude가 초안 번역 → 사용자 검토 후 확정. 고유명사 표기 고정: "ONE store", "Director's Cut", "Director's Cut Zone", "ONE store Console"(원콘솔).
- 신규 문구는 히어로 한 줄 정의·키워드 3칸·CTA 라벨뿐이며, 초안 내용에서만 도출한다.
- placeholder 2곳(추가 혜택 항목, 배포 가능 국가 리스트 URL): 값이 오면 채우고, 없으면 공개본에서 해당 줄을 숨긴다(빌드 경고로 알림).

## 6. 검증 (실행으로 확인)

1. 800px·375px 스크린샷 — 잘림·겹침·가로 스크롤 없음
2. HTML 열람 중 외부 네트워크 요청 0건
3. PDF 각 1페이지, 링크(YouTube·개발자센터·원콘솔) 클릭 동작, 폰트 내장
4. 한/영 짝 검사 통과, 각 언어 PDF에 다른 언어 텍스트 미노출
5. 대비 검사 — 다크·라이트 구간 본문 AA 이상
6. 국문 맞춤법 점검 결과 반영

## 7. 전달

- `dist/` 3개 파일을 **사용자가** OneDrive에 올리고 Anyone 링크를 만든다(외부 공개 행위라 대행하지 않음).
- 업로드 후 시크릿 창·폰에서 링크를 열어 PDF 미리보기가 렌더되는지 확인한다. 사내 정책으로 Anyone 링크가 막혀 있으면 이 단계에서 드러나므로 먼저 시험 링크를 만들어 본다.

## 8. 범위 밖

- 웹 호스팅(Cloudflare Pages 등) — 승인 나면 같은 `DirectorsCut.html`을 그대로 올리면 된다
- A4 인쇄 레이아웃, 다크/라이트 테마 토글, 애니메이션
- 공식 로고 SVG 확보(사용자 측 요청 사항)
