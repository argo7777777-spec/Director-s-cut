# Director's Cut 원페이지 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Director's Cut Zone 소개 원페이지를 한 소스(HTML)로 만들어 KO/EN 긴 한 장 PDF 2개 + 외부 의존 0인 단일 HTML 1개를 `dist/`에 출력한다.

**Architecture:** `src/index.html`에 한/영 문구를 `lang="ko"`/`lang="en"` 형제 요소로 나란히 두고 CSS로 비활성 언어를 숨긴다. `build/bundle.py`가 CSS·이미지·Paperlogy 서브셋 폰트를 인라인해 단일 HTML을 만들고, `build/pdf.js`(Playwright)가 `?lang=ko|en`으로 열어 폭 800px·높이 실측 PDF를 찍는다. `build/verify.js`가 레이아웃·네트워크·언어 누출·대비·PDF를 실행으로 검사한다.

**Tech Stack:** HTML/CSS(정적), Python 3.14 + fontTools·brotli·Pillow·pytest, Node 24 + playwright-core + 시스템 Chrome.

**Spec:** `docs/superpowers/specs/2026-10-02-directors-cut-onepager-design.md`

**스펙과 다른 점 (의도적):**
- 빌드 스크립트 이름 `build.py` → `build/bundle.py` (폴더 `build/`와 모듈 이름이 겹쳐 import 혼동을 피함).
- 로고는 흰색 1종(`logo-w.png`)만 — 로고가 나오는 곳(헤더·푸터)이 모두 다크 배경이라 검정판이 쓰일 곳이 없음.
- 히어로 CTA "원콘솔 바로가기" → "가이드 문서 보기"(개발자센터 Director's Cut 문서). 초안에 원콘솔 URL이 없고 검증된 주소가 없음.

## 공통 정보

- 작업 디렉터리: `D:/Claude/AXTF/24_Director's cut` (경로에 `'` 포함 — bash에서는 큰따옴표로 감쌀 것). git 루트는 `D:/Claude/AXTF`, 브랜치 `axtf-phase1`.
- Playwright 실행: `PW_CORE=C:/Users/1000125/AppData/Local/Temp/pw/node_modules/playwright-core node <script>` (Chrome: `C:/Program Files/Google/Chrome/Application/chrome.exe`).
- 폰트 원본: `D:/Claude/AXTF/Font/Paperlogy-{4Regular,6SemiBold,8ExtraBold}.ttf` → `src/`에서 상대경로 `../../Font/…`.
- `screenshot/` 폴더는 타사 게임 아트 포함 → **절대 커밋하지 말 것**, 페이지에도 쓰지 않음.
- 커밋은 항상 이 폴더 안의 파일만 명시적으로 `git add` (저장소에 다른 프로젝트의 미커밋 변경이 많음).

## 파일 구성

| 파일 | 책임 |
|---|---|
| `.gitignore` | `dist/` 무시 |
| `src/index.html` | 본문 마크업, 한/영 문구, 언어 토글 스크립트 |
| `src/style.css` | 토큰·레이아웃·반응형·인쇄, Paperlogy `@font-face`(TTF 상대경로) |
| `src/assets/logo-w.png` | ONE store 흰색 워드마크 (브랜드 사이트 PNG에서 잘라냄) |
| `src/assets/dc-video-thumb.jpg` | 유튜브 영상 썸네일 (원본 아티팩트에서 회수) |
| `src/assets/directors-cut-toggle.png` | 원콘솔 설정 화면 (원본 아티팩트에서 회수) |
| `build/bundle.py` | src → `dist/DirectorsCut.html` 단일 파일. 한/영 짝 검사, placeholder 경고 |
| `build/test_bundle.py` | bundle.py 단위 테스트 |
| `build/pdf.js` | `dist/DirectorsCut_KO.pdf`, `dist/DirectorsCut_EN.pdf` |
| `build/verify.js` | 실행 검증 (스크린샷·가로넘침·외부요청·언어누출·대비·PDF) |

---

### Task 1: 폴더 골격과 이미지 자산

**Files:**
- Create: `.gitignore`
- Create: `src/assets/logo-w.png`, `src/assets/dc-video-thumb.jpg`, `src/assets/directors-cut-toggle.png`

- [ ] **Step 1: `.gitignore` 작성**

```
dist/
__pycache__/
.pytest_cache/
```

- [ ] **Step 2: 로고 내려받아 "ONE store" 부분만 잘라내기**

브랜드 사이트 PNG(427×60)는 오른쪽에 "BRAND" 배지가 붙어 있다. 불투명 열 구간 실측 결과 워드마크는 x=0~252, 배지는 x=268~427.

```bash
cd "D:/Claude/AXTF/24_Director's cut" && mkdir -p src/assets && \
curl --ssl-no-revoke -sSL -o src/assets/_bi_w.png "https://www.onestorecorp.com/brand/wp-content/uploads/2018/07/bi_427x60_w.png" && \
python -c "
from PIL import Image
im = Image.open('src/assets/_bi_w.png').convert('RGBA').crop((0, 0, 253, 60))
im = im.crop(im.getbbox())
im.save('src/assets/logo-w.png')
print(im.size)
" && rm src/assets/_bi_w.png
```

(사내 PC curl은 `--ssl-no-revoke` 없으면 `CRYPT_E_NO_REVOCATION_CHECK`로 실패한다.)

Expected: `(252, 4x)` 근처 크기 출력. 이미지를 Read로 열어 "ONE store"만 있고 "BRAND"가 없는지 확인 (흰 글자라 어두운 배경 뷰어가 아니면 안 보일 수 있음 — 크기와 bbox로 판단해도 됨).

- [ ] **Step 3: 원본 아티팩트에서 이미지 2장 회수**

Artifact 도구로 읽는다 (curl/WebFetch 아님):
`Artifact(action="read", url="https://claude.ai/artifact/U4Zjs9PrNyGWGn56o7ieja", paths=["assets/dc-video-thumb.jpg","assets/directors-cut-toggle.png"])`
결과에 나온 저장 위치에서 `src/assets/`로 복사한다. (서브에이전트에 Artifact 도구가 없으면 이 스텝은 컨트롤러가 수행한다.)

```bash
ls -la "D:/Claude/AXTF/24_Director's cut/src/assets"
```

Expected: `dc-video-thumb.jpg`(29008 bytes), `directors-cut-toggle.png`(8493 bytes), `logo-w.png`.

- [ ] **Step 4: Commit**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && git add .gitignore src/assets && \
git commit -m "chore(directors-cut): 폴더 골격, 로고·썸네일·콘솔 스크린샷 자산"
```

---

### Task 2: 번들러 `build/bundle.py` (TDD)

**Files:**
- Create: `build/bundle.py`
- Test: `build/test_bundle.py`

- [ ] **Step 1: 실패하는 테스트 작성** — `build/test_bundle.py`

```python
import base64
from pathlib import Path

import pytest

import bundle

FONT = Path(__file__).resolve().parents[2] / "Font" / "Paperlogy-4Regular.ttf"
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def test_pairs_ok():
    html = '<div><p lang="ko">가</p><p lang="en">A</p></div>'
    assert bundle.check_pairs(html) == []


def test_pairs_inline_spans_and_nested():
    html = ('<ul><li><span lang="ko">가</span><span lang="en">A</span>'
            '<ul><li lang="ko">나</li><li lang="en">B</li></ul></li></ul>')
    assert bundle.check_pairs(html) == []


def test_pairs_void_sibling_does_not_break_pair():
    html = '<div><img src="x.png"><p lang="ko">가</p><p lang="en">A</p></div>'
    assert bundle.check_pairs(html) == []


def test_pairs_missing_en():
    errors = bundle.check_pairs('<div><p lang="ko">가</p></div>')
    assert len(errors) == 1 and "lang=en" in errors[0]


def test_pairs_en_without_ko():
    errors = bundle.check_pairs('<div><p lang="en">A</p></div>')
    assert len(errors) == 1


def test_pairs_tag_mismatch():
    errors = bundle.check_pairs('<div><p lang="ko">가</p><span lang="en">A</span></div>')
    assert len(errors) == 2


def test_pairs_ignores_html_element_lang():
    html = '<html lang="ko" data-lang="ko"><body><p>x</p></body></html>'
    assert bundle.check_pairs(html) == []


def test_count_placeholders():
    html = '<li class="placeholder">a</li><p class="x placeholder y">b</p><p class="other">c</p>'
    assert bundle.count_placeholders(html) == 2


def test_collect_text_includes_body_excludes_script_and_has_ascii():
    text = bundle.collect_text('<p>감독판</p><script>var 금지="z";</script>')
    assert "감" in text and "판" in text
    assert "금" not in text
    assert all(chr(c) in text for c in range(0x20, 0x7F))


def test_subset_woff2_is_small_woff2():
    data = bundle.subset_woff2(FONT, "감독판 Director's Cut")
    assert data[:4] == b"wOF2"
    assert len(data) < FONT.stat().st_size / 10


def test_build_inlines_everything(tmp_path):
    src = tmp_path / "src"
    (src / "assets").mkdir(parents=True)
    (src / "assets" / "a.png").write_bytes(PNG_1PX)
    (src / "style.css").write_text(
        '@font-face{font-family:P;src:url("%s")}' % FONT.as_posix(), encoding="utf-8")
    (src / "index.html").write_text(
        '<html><head><link rel="stylesheet" href="style.css"></head>'
        '<body><img src="assets/a.png"><p lang="ko">가</p><p lang="en">A</p></body></html>',
        encoding="utf-8")
    out = bundle.build(src, tmp_path / "dist" / "o.html")
    html = out.read_text(encoding="utf-8")
    assert "style.css" not in html
    assert "data:font/woff2;base64," in html
    assert 'src="data:image/png;base64,' in html
    assert ".ttf" not in html


def test_build_fails_on_pair_error(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "style.css").write_text("", encoding="utf-8")
    (src / "index.html").write_text(
        '<link rel="stylesheet" href="style.css"><p lang="ko">가</p>', encoding="utf-8")
    with pytest.raises(SystemExit):
        bundle.build(src, tmp_path / "o.html")
```

- [ ] **Step 2: 실패 확인**

Run: `cd "D:/Claude/AXTF/24_Director's cut" && pytest build -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'bundle'`

- [ ] **Step 3: 구현** — `build/bundle.py`

```python
"""src/ → dist/DirectorsCut.html 단일 파일 빌드.

CSS·이미지·폰트(본문에 쓰인 글자만 남긴 Paperlogy WOFF2)를 전부 인라인해
외부 요청 없이 열리는 HTML 한 개를 만든다.
"""
import base64
import re
import sys
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "dist" / "DirectorsCut.html"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "source", "track", "wbr"}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
CSS_LINK = '<link rel="stylesheet" href="style.css">'


class _Pairs(HTMLParser):
    """같은 부모 아래 lang=ko 요소 바로 다음 형제가 같은 태그의 lang=en 인지 검사."""

    def __init__(self):
        super().__init__()
        self.stack = [[]]  # 열린 요소마다 자식 목록 (tag, lang, line)
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag != "html":
            self.stack[-1].append((tag, dict(attrs).get("lang"), self.getpos()[0]))
        if tag not in VOID:
            self.stack.append([])

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].append((tag, dict(attrs).get("lang"), self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID or len(self.stack) == 1:
            return
        self._check(self.stack.pop())

    def close(self):
        super().close()
        while self.stack:
            self._check(self.stack.pop())

    def _check(self, kids):
        i = 0
        while i < len(kids):
            tag, lang, line = kids[i]
            if lang == "ko":
                nxt = kids[i + 1] if i + 1 < len(kids) else None
                if nxt and nxt[1] == "en" and nxt[0] == tag:
                    i += 2
                    continue
                self.errors.append(f"line {line}: <{tag} lang=ko> 바로 뒤에 같은 태그의 lang=en 없음")
            elif lang == "en":
                self.errors.append(f"line {line}: <{tag} lang=en> 앞에 짝 lang=ko 없음")
            i += 1


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def check_pairs(html: str) -> list[str]:
    p = _Pairs()
    p.feed(html)
    p.close()
    return p.errors


def count_placeholders(html: str) -> int:
    return len(re.findall(r'class="[^"]*\bplaceholder\b', html))


def collect_text(html: str) -> str:
    p = _Text()
    p.feed(html)
    p.close()
    ascii_ = "".join(chr(c) for c in range(0x20, 0x7F))
    return "".join(sorted(set("".join(p.parts) + ascii_)))


def subset_woff2(ttf: Path, text: str) -> bytes:
    opts = subset.Options()
    opts.layout_features = ["*"]
    font = TTFont(ttf)
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(font)
    font.flavor = "woff2"
    buf = BytesIO()
    font.save(buf)
    return buf.getvalue()


def _data_uri(path: Path) -> str:
    return f"data:{MIME[path.suffix.lower()]};base64," + base64.b64encode(path.read_bytes()).decode()


def inline_fonts(css: str, base: Path, text: str) -> str:
    def rep(m):
        data = subset_woff2((base / m.group(1)).resolve(), text)
        return f'url("data:font/woff2;base64,{base64.b64encode(data).decode()}") format("woff2")'
    return re.sub(r'url\("([^"]+\.ttf)"\)', rep, css)


def inline_images(html: str, base: Path) -> str:
    return re.sub(r'src="(assets/[^"]+)"', lambda m: f'src="{_data_uri(base / m.group(1))}"', html)


def build(src: Path = SRC, out: Path = OUT) -> Path:
    html = (src / "index.html").read_text(encoding="utf-8")
    errors = check_pairs(html)
    if errors:
        raise SystemExit("한/영 짝 오류:\n" + "\n".join(errors))
    n = count_placeholders(html)
    if n:
        print(f"경고: placeholder {n}곳 남음 — 공개본에서는 숨겨짐", file=sys.stderr)
    if CSS_LINK not in html:
        raise SystemExit(f"index.html에 {CSS_LINK} 가 없음")
    css = inline_fonts((src / "style.css").read_text(encoding="utf-8"), src, collect_text(html))
    html = html.replace(CSS_LINK, f"<style>\n{css}\n</style>")
    html = inline_images(html, src)
    left = re.findall(r'src="(?!data:)[^"]*"', html)
    if left:
        raise SystemExit(f"인라인 안 된 리소스: {left}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    path = build()
    print(f"{path} ({path.stat().st_size // 1024} KB)")
```

- [ ] **Step 4: 통과 확인**

Run: `cd "D:/Claude/AXTF/24_Director's cut" && pytest build -q`
Expected: `13 passed`

- [ ] **Step 5: Commit**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && git add build/bundle.py build/test_bundle.py && \
git commit -m "feat(directors-cut): 단일 HTML 번들러 — 폰트 서브셋·이미지 인라인·한/영 짝 검사"
```

---

### Task 3: 스타일과 페이지 골격 (헤더·히어로·언어 토글)

**Files:**
- Create: `src/style.css`
- Create: `src/index.html`

- [ ] **Step 1: `src/style.css` 작성**

```css
@font-face{font-family:"Paperlogy";font-weight:400;src:url("../../Font/Paperlogy-4Regular.ttf")}
@font-face{font-family:"Paperlogy";font-weight:600;src:url("../../Font/Paperlogy-6SemiBold.ttf")}
@font-face{font-family:"Paperlogy";font-weight:800;src:url("../../Font/Paperlogy-8ExtraBold.ttf")}

:root{
  --navy:#1b1d3a; --navy-2:#16182f; --navy-line:#2c2f52;
  --purple:#6b4cff; --red:#e8204a; --red-ink:#c4123a; --pink:#ff8aa0;
  --ink:#1b1d3a; --muted:#5b5f7a; --line:#e3e4ee; --soft:#f6f6fb;
  --d-ink:#f4f3fb; --d-muted:#b9b7d4;
}
*{box-sizing:border-box}
html{color-scheme:light}
body{margin:0;background:var(--navy-2);color:var(--ink);font-family:"Paperlogy",system-ui,sans-serif;font-size:17px;line-height:1.7;-webkit-font-smoothing:antialiased}
html[data-lang="ko"] [lang="en"],html[data-lang="en"] [lang="ko"]{display:none!important}
.page{max-width:800px;margin:0 auto;background:#fff}
.wrap{padding:0 48px}
a{color:inherit}
p{margin:0 0 14px}
code{font-family:ui-monospace,Consolas,monospace;font-size:.9em;background:var(--soft);border:1px solid var(--line);border-radius:5px;padding:1px 6px}
.placeholder{display:none}

/* 다크 구간 */
.dark{background-color:var(--navy-2);color:var(--d-ink)}
.hero{background-color:var(--navy);background-image:linear-gradient(160deg,#1b1d3a 0%,#2a1640 55%,#4a1630 100%);color:var(--d-ink);padding:28px 0 52px}
.topbar{display:flex;justify-content:space-between;align-items:center}
.logo{height:22px;width:auto;display:block}
.lang-toggle{display:flex;border:1px solid #55507a;border-radius:999px;overflow:hidden}
.lang-toggle button{all:unset;cursor:pointer;font-size:13px;font-weight:600;padding:4px 12px;color:var(--d-muted)}
.lang-toggle button[aria-pressed="true"]{background:#fff;color:var(--navy)}
.badges{display:flex;gap:6px;margin-top:56px}
.badge{font-size:13px;font-weight:800;line-height:1.5;padding:3px 10px;border-radius:6px;color:#fff}
.badge.purple{background:var(--purple)}
.badge.red{background:var(--red-ink)} /* --red(#e8204a) 위 흰 13px 글자는 4.43:1로 AA 미달 → 진한 레드 */
.hero h1{font-size:52px;line-height:1.1;font-weight:800;margin:14px 0;letter-spacing:-.01em;color:#fff}
.lede{font-size:20px;color:var(--d-muted);margin:0;max-width:30em}
.ctas{display:flex;gap:10px;margin-top:28px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:6px;font-size:15px;font-weight:600;padding:12px 20px;border-radius:999px;text-decoration:none}
.btn.primary{background:#fff;color:var(--navy)}
.btn.ghost{border:1px solid #8a86b8;color:#fff}
.keys{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:40px}
.key{border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.05);border-radius:14px;padding:16px}
.key b{display:block;font-size:17px;font-weight:800;color:#fff}
.key span{font-size:14px;line-height:1.5;color:var(--d-muted)}

/* 섹션 공통 */
.sec{padding:48px 0;border-top:1px solid var(--line)}
.dark .sec{border-top-color:var(--navy-line)}
.dark .sec:first-child{border-top:0}
.sec-head{display:flex;align-items:baseline;gap:12px;margin-bottom:18px}
.sec-num{font-size:14px;font-weight:800;letter-spacing:.08em;color:var(--red-ink)}
.dark .sec-num{color:var(--pink)}
.sec-title{font-size:28px;font-weight:800;line-height:1.3;margin:0}
.dark .sec-title{color:#fff}

/* 01 개요 */
.note{border-left:3px solid var(--purple);background:rgba(107,76,255,.14);padding:14px 18px;border-radius:0 10px 10px 0;font-size:16px}
.note p{margin:0}
.video-card{display:flex;gap:16px;align-items:center;margin-top:20px;text-decoration:none;color:inherit;border:1px solid var(--navy-line);border-radius:14px;padding:12px;background:rgba(255,255,255,.04)}
.video-thumb{position:relative;flex:none;width:200px;aspect-ratio:16/9;border-radius:10px;overflow:hidden}
.video-thumb img{width:100%;height:100%;object-fit:cover;display:block}
.play{position:absolute;inset:0;margin:auto;width:40px;height:40px;border-radius:50%;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center}
.video-meta b{display:block;font-size:16px;line-height:1.4;color:#fff}
.video-meta span{font-size:14px;color:var(--d-muted)}

/* 02 지원 사항 */
.benefits{display:grid;grid-template-columns:1fr 260px;gap:28px;align-items:start}
.benefit{border:1px solid var(--navy-line);background:rgba(255,255,255,.04);border-radius:14px;padding:18px 20px}
.benefit+.benefit{margin-top:12px}
.benefit h3{font-size:18px;font-weight:800;margin:0 0 6px;color:#fff}
.benefit ul{margin:0;padding-left:1.1em;font-size:15.5px}
.benefit li{color:var(--d-muted)}
.phone{width:260px;border-radius:32px;border:6px solid var(--navy-line);overflow:hidden;background:#fff}
.phone svg{display:block;width:100%;height:auto}
.fig-cap{font-size:13px;line-height:1.5;color:var(--d-muted);margin-top:10px}
.fade{height:72px;background:linear-gradient(var(--navy-2),#fff)}

/* 라이트 구간 */
.light{background:#fff;color:var(--ink)}
.soft{background:var(--soft)}
.lead{color:var(--muted)}
.path{display:inline-flex;flex-wrap:wrap;gap:6px;align-items:center;background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:10px 14px;font-size:15px}
.path i{font-style:normal;color:var(--muted)}
.shot{margin:20px 0;border:1px solid var(--line);border-radius:12px;padding:14px;background:#fff}
.shot img{display:block;max-width:100%}
.shot figcaption{font-size:13px;color:var(--muted);margin-top:8px}
.steps{list-style:none;counter-reset:s;margin:0;padding:0;display:grid;gap:10px}
.steps li{counter-increment:s;position:relative;border:1px solid var(--line);border-radius:12px;padding:14px 16px 14px 56px;font-size:16px}
.steps li::before{content:counter(s);position:absolute;left:16px;top:15px;width:26px;height:26px;border-radius:50%;background:var(--purple);color:#fff;font-weight:800;font-size:14px;display:flex;align-items:center;justify-content:center}
.doc-card{border:1px solid var(--line);border-radius:14px;padding:18px 20px}
.doc-card+.doc-card{margin-top:12px}
.doc-card h3{font-size:18px;font-weight:800;margin:0 0 4px}
.doc-card p{margin:0 0 6px;color:var(--muted);font-size:15.5px}
.doc-card a{color:var(--red-ink);font-weight:600;text-decoration:none;font-size:15px}
.tag{font-size:12px;font-weight:600;color:var(--red-ink);border:1px solid currentColor;border-radius:999px;padding:1px 8px;margin-left:8px;vertical-align:2px}
.warn{margin-top:16px;background:#fff4f6;border:1px solid #f6c1cb;border-radius:12px;padding:14px 18px;font-size:15.5px;color:#7a1027}
.warn p{margin:0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.chip{font-size:14px;border:1px solid var(--line);background:#fff;border-radius:999px;padding:4px 12px}
.chip.no{color:var(--red-ink);border-color:#f6c1cb}
.fee{border:1px solid var(--line);background:#fff;border-radius:14px;padding:18px 20px}
.fee .big{font-size:30px;font-weight:800;line-height:1.2;color:var(--navy)}
.fee p{font-size:15px}
.small{font-size:14.5px;color:var(--muted)}
.channels{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.channel{border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.channel.wide{grid-column:1/-1}
.channel h3{font-size:17px;font-weight:800;margin:0 0 4px}
.channel p{font-size:15px;line-height:1.6;color:var(--muted);margin:0}
.shortlink{margin-top:16px;background:var(--navy);color:#fff;border-radius:12px;padding:16px 20px;font-size:15.5px}
.shortlink p{margin:0}
.shortlink code{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.25);color:#fff}

footer{background:var(--navy);color:var(--d-muted);padding:28px 0;font-size:14px}
footer .wrap{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
footer a{color:#fff}

@media (max-width:640px){
  .wrap{padding:0 20px}
  .hero h1{font-size:36px}
  .keys,.two,.channels,.benefits{grid-template-columns:1fr}
  .phone{margin:0 auto}
  .video-card{flex-direction:column;align-items:stretch}
  .video-thumb{width:100%}
}
@page{margin:0}
@media print{.lang-toggle{display:none}}
```

- [ ] **Step 2: `src/index.html` 작성 (헤더·히어로·토글, 섹션 자리 표시 주석)**

```html
<!doctype html>
<html lang="ko" data-lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Director's Cut Zone · ONE store</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="page">

  <header class="hero">
    <div class="wrap">
      <div class="topbar">
        <img class="logo" src="assets/logo-w.png" alt="ONE store">
        <div class="lang-toggle" role="group" aria-label="Language">
          <button type="button" data-set="ko" aria-pressed="true">KO</button>
          <button type="button" data-set="en" aria-pressed="false">EN</button>
        </div>
      </div>
      <div class="badges"><span class="badge purple">19+</span><span class="badge red">GLOBAL</span></div>
      <h1>Director's Cut Zone</h1>
      <p class="lede" lang="ko">청소년 이용불가 등급 게임을 위한 원스토어 글로벌 전용 존. 창작 의도 그대로의 "감독판"을 타겟 유저에게 선보이세요.</p>
      <p class="lede" lang="en">ONE store Global's dedicated zone for games rated unsuitable for minors. Bring your uncut "director's cut" straight to the players looking for it.</p>
      <div class="ctas">
        <a class="btn primary" href="https://onestore-dev.gitbook.io/dev/docs/apps/product/android/main-info/directors-cut"><span lang="ko">가이드 문서 보기</span><span lang="en">Read the guide</span></a>
        <a class="btn ghost" href="#setup"><span lang="ko">설정 방법 ↓</span><span lang="en">How to set up ↓</span></a>
      </div>
      <div class="keys">
        <div class="key"><b lang="ko">전용 노출</b><b lang="en">Dedicated placement</b><span lang="ko">Zone 전용 탭·카드·랭킹</span><span lang="en">Zone tab, cards &amp; ranking</span></div>
        <div class="key"><b lang="ko">전용 프로모션</b><b lang="en">Exclusive promotions</b><span lang="ko">포인트백·쿠폰·다운로드 유도</span><span lang="en">Point-back, coupons, download drives</span></div>
        <div class="key"><b lang="ko">글로벌 배포</b><b lang="en">Global distribution</b><span lang="ko">지원 국가 대상 서비스</span><span lang="en">Served in supported countries</span></div>
      </div>
    </div>
  </header>

  <!-- DARK-SECTIONS -->

  <!-- LIGHT-SECTIONS -->

</div>
<script>
(function () {
  var h = document.documentElement;
  function set(lang) {
    h.dataset.lang = lang;
    h.lang = lang;
    document.querySelectorAll(".lang-toggle button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.set === lang));
    });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest(".lang-toggle button");
    if (b) set(b.dataset.set);
  });
  set(new URLSearchParams(location.search).get("lang") === "en" ? "en" : "ko");
})();
</script>
</body>
</html>
```

- [ ] **Step 3: 빌드 실행**

Run: `cd "D:/Claude/AXTF/24_Director's cut" && python build/bundle.py`
Expected: `…dist\DirectorsCut.html (NN KB)` — 오류 없음, placeholder 경고 없음.

- [ ] **Step 4: 눈으로 확인 (스크린샷)**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && PW_CORE=C:/Users/1000125/AppData/Local/Temp/pw/node_modules/playwright-core node -e "
const {chromium}=require(process.env.PW_CORE);const path=require('path');const {pathToFileURL}=require('url');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const p=await b.newPage({viewport:{width:800,height:900}});
for(const l of ['ko','en']){await p.goto(pathToFileURL(path.resolve('dist/DirectorsCut.html')).href+'?lang='+l);await p.evaluate(()=>document.fonts.ready);
await p.screenshot({path:'dist/hero-'+l+'.png',fullPage:true});}await b.close();})();"
```

Read `dist/hero-ko.png`, `dist/hero-en.png`. 확인: Paperlogy로 렌더(시스템 폰트 아님), 로고에 "BRAND" 없음, 영어판에 한글 없음, KO/EN 토글 버튼의 활성 상태가 언어와 일치.

- [ ] **Step 5: Commit**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && git add src/style.css src/index.html && \
git commit -m "feat(directors-cut): 스타일 토큰, 히어로, 한/영 토글"
```

---

### Task 4: 다크 구간 — 01 개요, 02 지원 사항(폰 목업)

**Files:**
- Modify: `src/index.html` (`<!-- DARK-SECTIONS -->` 주석을 아래 블록으로 교체)

- [ ] **Step 1: `<!-- DARK-SECTIONS -->`를 교체**

```html
  <div class="dark"><div class="wrap">

    <section class="sec">
      <div class="sec-head"><span class="sec-num">01</span><h2 class="sec-title"><span lang="ko">개요</span><span lang="en">Overview</span></h2></div>
      <p lang="ko">Director's Cut은 원스토어가 게임사에게 제공하는 상품 메타 옵션으로, 청소년 이용불가 등급의 콘텐츠(선정성·폭력성 등 "감독판" 수준의 표현)를 포함한 게임을 원스토어 글로벌의 전용 존인 <b>Director's Cut Zone</b>을 통해 서비스할 수 있도록 지원하는 프로그램입니다.</p>
      <p lang="en">Director's Cut is a product metadata option ONE store offers to game companies. It lets games containing content rated unsuitable for minors (sexual or violent expression at a "director's cut" level) be served through <b>Director's Cut Zone</b>, a dedicated zone on ONE store Global.</p>
      <div class="note">
        <p lang="ko">Director's Cut은 법적 등급이 아닌, 게임사가 자사 상품에 자율적으로 설정하는 자기 선언형 메타 정보입니다. 국가별 등급분류 기준 충족 및 콘텐츠에 대한 법적 책임은 게임사에 있으며, 원스토어는 이를 별도로 사전 심의하지 않습니다.</p>
        <p lang="en">Director's Cut is not a legal rating. It is self-declared metadata that each game company sets for its own products. Meeting each country's rating requirements and legal responsibility for the content rest with the game company; ONE store does not pre-screen it separately.</p>
      </div>
      <a class="video-card" href="https://youtu.be/nczZS7ejlFQ">
        <span class="video-thumb">
          <img src="assets/dc-video-thumb.jpg" alt="">
          <span class="play" aria-hidden="true"><svg viewBox="0 0 24 24" width="20" height="20"><path d="M8 5v14l11-7z" fill="#fff"/></svg></span>
        </span>
        <span class="video-meta">
          <b lang="ko">합법적으로 어디까지 가능? 원스토어 디렉터스 컷</b>
          <b lang="en">합법적으로 어디까지 가능? 원스토어 디렉터스 컷 (Korean)</b>
          <span>YouTube · NEXUS 넥서스</span>
        </span>
      </a>
    </section>

    <section class="sec">
      <div class="sec-head"><span class="sec-num">02</span><h2 class="sec-title"><span lang="ko">지원 사항</span><span lang="en">Benefits</span></h2></div>
      <div class="benefits">
        <div>
          <div class="benefit">
            <h3 lang="ko">전용 노출 지면</h3>
            <h3 lang="en">Dedicated placement</h3>
            <ul>
              <li lang="ko">Director's Cut Zone 내 전용 노출 지면을 통한 타겟 유저 대상 발견성 확보</li>
              <li lang="en">Discoverability among your target users through placements exclusive to Director's Cut Zone</li>
              <li lang="ko">신규 게임 카드, 전용 랭킹 카드 등을 활용한 명확한 타겟 유저 노출</li>
              <li lang="en">Clear exposure to target users via new-game cards, a dedicated ranking card and more</li>
              <li lang="ko">Director's Cut Zone은 원스토어 앱 내 별도 탭을 통해 운영됩니다. ('26.10 내 예정)</li>
              <li lang="en">Director's Cut Zone runs as a separate tab in the ONE store app (planned within Oct 2026).</li>
            </ul>
          </div>
          <div class="benefit">
            <h3 lang="ko">전용 정기 프로모션</h3>
            <h3 lang="en">Exclusive recurring promotions</h3>
            <ul>
              <li lang="ko">Director's Cut Zone 전용 정기 프로모션 (2026년 10월 기준 · 일정은 수시로 변경될 수 있음)</li>
              <li lang="en">Recurring promotions exclusive to Director's Cut Zone (as of Oct 2026; schedule subject to change)</li>
              <li lang="ko">전용 포인트백, 사전예약자 대상 전용 쿠폰, 다운로드 유도 프로모션 등 예정</li>
              <li lang="en">Planned: dedicated point-back, exclusive coupons for pre-registrants, download-driving promotions and more</li>
            </ul>
          </div>
          <div class="benefit placeholder">
            <h3 lang="ko">추가 혜택 — 확정 시 반영</h3>
            <h3 lang="en">More benefits — to be added</h3>
          </div>
        </div>
        <figure style="margin:0">
          <div class="phone">
            <svg viewBox="0 0 360 720" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Director's Cut Zone">
              <defs>
                <linearGradient id="gH" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4a1630"/><stop offset="1" stop-color="#1b1d3a"/></linearGradient>
                <linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6b4cff"/><stop offset="1" stop-color="#2a1640"/></linearGradient>
                <linearGradient id="g2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e8204a"/><stop offset="1" stop-color="#4a1630"/></linearGradient>
                <linearGradient id="g3" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff8a5c"/><stop offset="1" stop-color="#7a1f3a"/></linearGradient>
              </defs>
              <rect width="360" height="720" fill="#fff"/>
              <rect x="16" y="18" width="22" height="22" rx="6" fill="#e8204a"/>
              <text x="27" y="35" font-size="15" font-weight="800" fill="#fff" text-anchor="middle">1</text>
              <text x="46" y="35" font-size="16" font-weight="800" fill="#1b1d3a">ONE store</text>
              <g font-size="14" fill="#5b5f7a">
                <text x="16" y="78" lang="ko">추천</text>
                <text x="16" y="78" lang="en">Featured</text>
                <text x="84" y="78" font-weight="800" fill="#1b1d3a">Director's Cut Zone</text>
                <text x="250" y="78" lang="ko">랭킹</text>
                <text x="250" y="78" lang="en">Ranking</text>
              </g>
              <rect x="84" y="88" width="142" height="3" rx="1.5" fill="#1b1d3a"/>
              <line x1="0" y1="92" x2="360" y2="92" stroke="#e3e4ee"/>
              <rect x="16" y="108" width="328" height="150" rx="16" fill="url(#gH)"/>
              <rect x="32" y="124" width="44" height="20" rx="6" fill="#e8204a"/>
              <text x="54" y="138" font-size="11" font-weight="800" fill="#fff" text-anchor="middle">NEW</text>
              <text x="32" y="186" font-size="20" font-weight="800" fill="#fff">Director's Cut Zone</text>
              <text x="32" y="212" font-size="14" fill="#d9d6f0" lang="ko">오픈 기념 혜택!</text>
              <text x="32" y="212" font-size="14" fill="#d9d6f0" lang="en">Grand opening offers!</text>
              <text x="16" y="294" font-size="16" font-weight="800" fill="#1b1d3a" lang="ko">이번 주 인기 Director's Cut</text>
              <text x="16" y="294" font-size="16" font-weight="800" fill="#1b1d3a" lang="en">Popular this week</text>
              <g transform="translate(16,310)">
                <rect width="100" height="100" rx="18" fill="url(#g1)"/><circle cx="84" cy="84" r="11" fill="#1b1d3a" stroke="#fff" stroke-width="1.5"/><text x="84" y="88.5" font-size="11" font-weight="800" fill="#fff" text-anchor="middle">19</text>
                <rect x="114" width="100" height="100" rx="18" fill="url(#g2)"/><circle cx="198" cy="84" r="11" fill="#1b1d3a" stroke="#fff" stroke-width="1.5"/><text x="198" y="88.5" font-size="11" font-weight="800" fill="#fff" text-anchor="middle">19</text>
                <rect x="228" width="100" height="100" rx="18" fill="url(#g3)"/><circle cx="312" cy="84" r="11" fill="#1b1d3a" stroke="#fff" stroke-width="1.5"/><text x="312" y="88.5" font-size="11" font-weight="800" fill="#fff" text-anchor="middle">19</text>
                <rect y="112" width="70" height="10" rx="5" fill="#e3e4ee"/><rect x="114" y="112" width="70" height="10" rx="5" fill="#e3e4ee"/><rect x="228" y="112" width="70" height="10" rx="5" fill="#e3e4ee"/>
              </g>
              <text x="16" y="474" font-size="16" font-weight="800" fill="#1b1d3a" lang="ko">Director's Cut 전용 랭킹</text>
              <text x="16" y="474" font-size="16" font-weight="800" fill="#1b1d3a" lang="en">Director's Cut ranking</text>
              <g transform="translate(16,490)">
                <rect width="328" height="156" rx="14" fill="#f6f6fb"/>
                <text x="18" y="38" font-size="18" font-weight="800" fill="#e8204a">1</text><rect x="44" y="16" width="34" height="34" rx="9" fill="url(#g2)"/><rect x="90" y="27" width="120" height="11" rx="5" fill="#d3d5e4"/>
                <text x="18" y="88" font-size="18" font-weight="800" fill="#e8204a">2</text><rect x="44" y="66" width="34" height="34" rx="9" fill="url(#g1)"/><rect x="90" y="77" width="96" height="11" rx="5" fill="#d3d5e4"/>
                <text x="18" y="138" font-size="18" font-weight="800" fill="#e8204a">3</text><rect x="44" y="116" width="34" height="34" rx="9" fill="url(#g3)"/><rect x="90" y="127" width="136" height="11" rx="5" fill="#d3d5e4"/>
              </g>
              <line x1="0" y1="668" x2="360" y2="668" stroke="#e3e4ee"/>
              <g fill="none" stroke="#b9bbd0" stroke-width="2">
                <circle cx="44" cy="694" r="10" stroke="#1b1d3a"/><circle cx="112" cy="694" r="10"/><circle cx="180" cy="694" r="10"/><circle cx="248" cy="694" r="10"/><circle cx="316" cy="694" r="10"/>
              </g>
            </svg>
          </div>
          <figcaption class="fig-cap"><span lang="ko">예시 이미지 — 실제 탭 명칭·위치·디자인은 출시 시 최종 반영본과 다를 수 있습니다.</span><span lang="en">Illustrative only — the actual tab name, position and design may differ at launch.</span></figcaption>
        </figure>
      </div>
    </section>

  </div></div>
  <div class="fade" aria-hidden="true"></div>
```

- [ ] **Step 2: 빌드**

Run: `cd "D:/Claude/AXTF/24_Director's cut" && python build/bundle.py`
Expected: 성공 + `경고: placeholder 1곳 남음 — 공개본에서는 숨겨짐` (추가 혜택 카드).

- [ ] **Step 3: 스크린샷으로 확인** — Task 3 Step 4 명령을 그대로 다시 실행하고 `dist/hero-ko.png`, `dist/hero-en.png`를 Read.
확인: 폰 목업 안에서 한 언어만 보임(겹친 글자 없음), 썸네일 이미지 표시, 다크→라이트 그라데이션 띠, "추가 혜택" 카드 안 보임.

- [ ] **Step 4: Commit**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && git add src/index.html && \
git commit -m "feat(directors-cut): 01 개요·02 지원 사항, Zone 폰 목업"
```

---

### Task 5: 라이트 구간 — 03~07, 푸터

**Files:**
- Modify: `src/index.html` (`<!-- LIGHT-SECTIONS -->` 주석을 아래 블록으로 교체)

- [ ] **Step 1: `<!-- LIGHT-SECTIONS -->`를 교체**

```html
  <div class="light">

    <section class="sec" id="setup" style="border-top:0"><div class="wrap">
      <div class="sec-head"><span class="sec-num">03</span><h2 class="sec-title"><span lang="ko">설정 방법</span><span lang="en">How to set up</span></h2></div>
      <div class="path" lang="ko"><b>원스토어 원콘솔</b><i>›</i>상품관리<i>›</i>Android 상품관리<i>›</i>기본정보<i>›</i><b>Director's Cut 여부</b></div>
      <div class="path" lang="en"><b>ONE store Console</b><i>›</i>Product Management<i>›</i>Android Product Management<i>›</i>Basic Info<i>›</i><b>Director's Cut setting</b></div>
      <figure class="shot">
        <img src="assets/directors-cut-toggle.png" alt="Director's Cut setting UI">
        <figcaption><span lang="ko">원콘솔 기본정보 화면 내 Director's Cut 여부 설정 UI</span><span lang="en">Director's Cut setting in the Basic Info screen of ONE store Console</span></figcaption>
      </figure>
      <ol class="steps">
        <li lang="ko">원콘솔에 로그인 후 대상 상품의 <b>Android 상품관리 &gt; 기본정보</b> 화면으로 이동합니다.</li>
        <li lang="en">Log in to ONE store Console and open <b>Android Product Management &gt; Basic Info</b> for the target product.</li>
        <li lang="ko">Director's Cut 여부를 <b>예</b>로 설정합니다. (상품 유형이 <code>APK</code> &amp; <code>게임</code>인 경우에만 설정 가능)</li>
        <li lang="en">Set Director's Cut to <b>Yes</b>. (Available only when the product type is <code>APK</code> &amp; <code>Game</code>.)</li>
        <li lang="ko">검증 요청 시, Director's Cut 지원국가만 배포 대상국으로 노출·선택 가능합니다. (대한민국은 서비스 대상국이 아니므로 목록에서 제외)</li>
        <li lang="en">When you request review, only countries supported by Director's Cut can be shown and selected as distribution targets. (Korea is not a service country and is excluded from the list.)</li>
        <li lang="ko">저장 및 배포 정책은 기존 상품 기본정보 정책과 동일하게 적용됩니다.</li>
        <li lang="en">Saving and distribution follow the same policies as existing product basic info.</li>
      </ol>
    </div></section>

    <section class="sec"><div class="wrap">
      <div class="sec-head"><span class="sec-num">04</span><h2 class="sec-title"><span lang="ko">주의사항</span><span lang="en">Important notes</span></h2></div>
      <p class="lead" lang="ko">Director's Cut 콘텐츠를 서비스하기 전, 아래 문서를 반드시 확인해 주세요.</p>
      <p class="lead" lang="en">Before serving Director's Cut content, be sure to review the documents below.</p>
      <div class="doc-card">
        <h3>19+ Game Guide <span class="tag" lang="ko">청소년 이용불가 게임 가이드</span><span class="tag" lang="en">Guide for games unsuitable for minors</span></h3>
        <p lang="ko">전면 금지 콘텐츠 기준, 모자이크(은폐처리) 가이드, 정책 위반 시 조치 등</p>
        <p lang="en">Fully prohibited content criteria, mosaic (concealment) guide, actions on policy violations, etc.</p>
        <a href="https://onestore-dev.gitbook.io/dev/docs/apps/product/android/main-info/directors-cut#id-2.-directors-cut"><span lang="ko">청소년 이용불가 게임 가이드 바로가기 →</span><span lang="en">Open the 19+ Game Guide →</span></a>
      </div>
      <div class="doc-card">
        <h3><span lang="ko">제한된 콘텐츠</span><span lang="en">Restricted Content</span> <span class="tag" lang="ko">상품 검증 가이드라인 내</span><span class="tag" lang="en">In the product review guidelines</span></h3>
        <p lang="ko">청소년 이용불가 콘텐츠 예외 적용 기준</p>
        <p lang="en">Criteria for exceptions applied to content unsuitable for minors</p>
        <a href="https://onestore-dev.gitbook.io/dev/docs/review/one-store-review-guideline/undefined"><span lang="ko">제한된 콘텐츠 페이지 바로가기 →</span><span lang="en">Open Restricted Content →</span></a>
      </div>
      <div class="warn">
        <p lang="ko">단, Director's Cut으로 게임사에서 설정을 하셨다 하더라도 Zone의 특성에 부합하지 않거나 위 가이드에서 정하는 기준을 충족하지 못할 경우, 검증 반려 또는 서비스 중 조치(판매불가 등)의 대상이 될 수 있습니다.</p>
        <p lang="en">Even if a game company sets Director's Cut, a product that does not fit the nature of the Zone or fails to meet the criteria in the guides above may be rejected in review or subject to action during service (e.g., suspension of sales).</p>
      </div>
    </div></section>

    <section class="sec soft"><div class="wrap two">
      <div>
        <div class="sec-head"><span class="sec-num">05</span><h2 class="sec-title"><span lang="ko">배포 가능 국가</span><span lang="en">Available countries</span></h2></div>
        <p class="small" lang="ko">국가별 지원 여부는 사업적 판단에 따라 변경될 수 있습니다.</p>
        <p class="small" lang="en">Support by country may change based on business decisions.</p>
        <p class="placeholder">배포 가능 국가 리스트 URL — 확정 시 반영</p>
        <p lang="ko">대한민국은 Director's Cut Zone 서비스 대상 국가/지역에 포함되지 않으며, 다음 국가/지역은 Director's Cut Zone 미지원으로 Director's Cut Zone 선택 시 자동으로 판매불가 처리됩니다.</p>
        <p lang="en">Korea is not a service country/region for Director's Cut Zone. The following countries/regions do not support Director's Cut Zone, and sales there are automatically disabled when Director's Cut Zone is selected.</p>
        <div class="chips">
          <span class="chip" lang="ko">대한민국 — 서비스 대상국 아님</span><span class="chip" lang="en">Korea — not a service country</span>
          <span class="chip no" lang="ko">아랍에미리트 — 미지원</span><span class="chip no" lang="en">UAE — not supported</span>
          <span class="chip no" lang="ko">카타르 — 미지원</span><span class="chip no" lang="en">Qatar — not supported</span>
          <span class="chip no" lang="ko">쿠웨이트 — 미지원</span><span class="chip no" lang="en">Kuwait — not supported</span>
          <span class="chip no" lang="ko">파키스탄 — 미지원</span><span class="chip no" lang="en">Pakistan — not supported</span>
        </div>
      </div>
      <div>
        <div class="sec-head"><span class="sec-num">06</span><h2 class="sec-title"><span lang="ko">서비스 이용료율</span><span lang="en">Service fee</span></h2></div>
        <div class="fee">
          <div class="big">+10%</div>
          <p><b lang="ko">피처드 수수료 (예정)</b><b lang="en">Featured fee (planned)</b></p>
          <p lang="ko">원스토어 <a href="https://onestore-dev.gitbook.io/dev/docs/payment/service_fee/global">서비스 이용료율</a> 외 추가</p>
          <p lang="en">On top of ONE store's <a href="https://onestore-dev.gitbook.io/dev/docs/payment/service_fee/global">service fee rate</a></p>
          <p class="small" lang="ko">현재는 별도의 피처드 수수료 없이 운영되나, 특정 시점에 사전 고지를 통해 피처드 비용을 수취하게 될 예정입니다.</p>
          <p class="small" lang="en">No featured fee is charged at present; it will be introduced at a later date with prior notice.</p>
        </div>
      </div>
    </div></section>

    <section class="sec"><div class="wrap">
      <div class="sec-head"><span class="sec-num">07</span><h2 class="sec-title"><span lang="ko">DC 게임 활성화를 위한 가이드</span><span lang="en">Growing your DC game</span></h2></div>
      <p class="lead" lang="ko">19+ 게임은 전통적 스토어의 결제·노출 제약 때문에, 자체 커뮤니티를 통한 직접 홍보 의존도가 특히 높은 카테고리입니다. 아래는 실제로 19+ 게임 개발사들이 신작·업데이트 소식을 알리는 데 활발히 활용하는 채널입니다.</p>
      <p class="lead" lang="en">19+ games rely heavily on promotion through their own communities, owing to payment and exposure restrictions on traditional stores. Below are channels that 19+ game developers actively use to announce new releases and updates.</p>
      <div class="channels">
        <div class="channel"><h3>F95Zone</h3>
          <p lang="ko">가장 큰 규모의 성인 게임 포럼. 게임별 전용 스레드에서 리뷰·공략·업데이트 소식이 활발히 공유됩니다.</p>
          <p lang="en">The largest adult game forum. Reviews, walkthroughs and update news are actively shared in dedicated per-game threads.</p></div>
        <div class="channel"><h3>LewdCorner</h3>
          <p lang="ko">F95Zone의 대안 커뮤니티로, 무검열 콘텐츠에 우호적인 유저층이 모여 있습니다.</p>
          <p lang="en">An alternative community to F95Zone, home to users who favor uncensored content.</p></div>
        <div class="channel"><h3><span lang="ko">Reddit (r/lewdgames 등)</span><span lang="en">Reddit (r/lewdgames, etc.)</span></h3>
          <p lang="ko">장르·플랫폼별로 세분화된 서브레딧에서 신작 추천, 유저 반응이 활발히 오갑니다.</p>
          <p lang="en">Subreddits segmented by genre and platform, with active new-release recommendations and user feedback.</p></div>
        <div class="channel"><h3>LemmaSoft Forums</h3>
          <p lang="ko">비주얼노벨 장르에 특화된 개발자·유저 커뮤니티로, VN 형식의 타이틀에 특히 적합합니다.</p>
          <p lang="en">A developer and user community specialized in visual novels — especially suited to VN-format titles.</p></div>
        <div class="channel wide"><h3><span lang="ko">itch.io (Adult 태그) · Patreon</span><span lang="en">itch.io (Adult tag) · Patreon</span></h3>
          <p lang="ko">많은 개발사가 노출 채널과 후원·팬덤 관리를 병행하는 곳으로, 스토어 링크를 함께 안내하기 좋습니다.</p>
          <p lang="en">Where many developers combine exposure with backer and fandom management — a good place to share your store link too.</p></div>
      </div>
      <div class="shortlink">
        <p lang="ko">위 채널에 원스토어 Director's Cut 입점 소식과 프로모션을 직접 안내해 주세요. 원스토어 숏링크로 상품 페이지를 간편하게 공유할 수 있습니다: <code>https://onesto.re/{PID}</code> (PID는 상품 고유 ID로 교체)</p>
        <p lang="en">Announce your Director's Cut launch and promotions on these channels yourself. Share your product page easily with a ONE store short link: <code>https://onesto.re/{PID}</code> (replace PID with your product ID)</p>
      </div>
    </div></section>

  </div>

  <footer><div class="wrap">
    <img class="logo" src="assets/logo-w.png" alt="ONE store">
    <span><a href="https://onestore-dev.gitbook.io/dev"><span lang="ko">원스토어 개발자센터</span><span lang="en">ONE store Developer Center</span></a> · <span lang="ko">2026년 10월 기준</span><span lang="en">As of October 2026</span></span>
  </div></footer>
```

(주의: `.light` 섹션의 위아래 패딩은 `.sec`, 좌우 여백은 안쪽 `.wrap`이 담당한다. 03만 위 구분선을 없앤다 — 그라데이션 띠 바로 아래라서.)

- [ ] **Step 2: 빌드**

Run: `cd "D:/Claude/AXTF/24_Director's cut" && python build/bundle.py`
Expected: 성공 + `경고: placeholder 2곳 남음 — 공개본에서는 숨겨짐`.

- [ ] **Step 3: 스크린샷 확인** — Task 3 Step 4 명령 재실행, 두 이미지를 Read.
확인: 05·06 2단 배치, 07 카드 2열 + itch.io 카드 전체 폭, 푸터 로고, 영어판에 한글 문장 없음(영상 제목·콘솔 스크린샷 제외).

- [ ] **Step 4: Commit**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && git add src/index.html && \
git commit -m "feat(directors-cut): 03~07 가이드 구간과 푸터"
```

---

### Task 6: PDF 출력 `build/pdf.js`

**Files:**
- Create: `build/pdf.js`

- [ ] **Step 1: 작성**

```js
// dist/DirectorsCut.html → dist/DirectorsCut_KO.pdf, DirectorsCut_EN.pdf (폭 800px 긴 한 장)
// 실행: PW_CORE=C:/Users/1000125/AppData/Local/Temp/pw/node_modules/playwright-core node build/pdf.js
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require(process.env.PW_CORE || "playwright-core");

const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const DIST = path.resolve(__dirname, "..", "dist");
const PAGE = pathToFileURL(path.join(DIST, "DirectorsCut.html")).href;

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  const page = await browser.newPage({ viewport: { width: 800, height: 1000 } });
  for (const lang of ["ko", "en"]) {
    await page.goto(`${PAGE}?lang=${lang}`);
    await page.emulateMedia({ media: "print" });
    await page.evaluate(() => document.fonts.ready);
    const height = await page.evaluate(() => Math.ceil(document.documentElement.scrollHeight));
    const out = path.join(DIST, `DirectorsCut_${lang.toUpperCase()}.pdf`);
    await page.pdf({
      path: out,
      width: "800px",
      height: `${height + 2}px`,
      printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });
    console.log(`${out}  (${height}px)`);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
```

- [ ] **Step 2: 실행**

Run: `cd "D:/Claude/AXTF/24_Director's cut" && python build/bundle.py && PW_CORE=C:/Users/1000125/AppData/Local/Temp/pw/node_modules/playwright-core node build/pdf.js`
Expected: PDF 2개 경로와 높이(대략 4000~6000px) 출력.

- [ ] **Step 3: Commit**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && git add build/pdf.js && \
git commit -m "feat(directors-cut): KO/EN 긴 한 장 PDF 출력"
```

---

### Task 7: 실행 검증 `build/verify.js`

**Files:**
- Create: `build/verify.js`

- [ ] **Step 1: 작성**

```js
// 빌드 결과 실행 검증. 실패 항목이 있으면 exit 1.
// 실행: PW_CORE=C:/Users/1000125/AppData/Local/Temp/pw/node_modules/playwright-core node build/verify.js
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require(process.env.PW_CORE || "playwright-core");

const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const DIST = path.resolve(__dirname, "..", "dist");
const PAGE = pathToFileURL(path.join(DIST, "DirectorsCut.html")).href;
const SHOTS = path.join(DIST, "shots");
const fails = [];
const check = (ok, msg) => { console.log(`${ok ? "PASS" : "FAIL"}  ${msg}`); if (!ok) fails.push(msg); };

// 페이지 안에서 실행: 보이는 텍스트 요소 중 WCAG AA 대비 미달 목록
function lowContrast() {
  const parse = (c) => { const m = c.match(/[\d.]+/g).map(Number); return { r: m[0], g: m[1], b: m[2], a: m[3] ?? 1 }; };
  const over = (top, under) => ({ r: top.r * top.a + under.r * (1 - top.a), g: top.g * top.a + under.g * (1 - top.a), b: top.b * top.a + under.b * (1 - top.a), a: 1 });
  const lum = ({ r, g, b }) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let bg = { r: 255, g: 255, b: 255, a: 1 };
    for (const c of layers.reverse()) bg = over(c, bg);
    return bg;
  };
  const out = [];
  for (const el of document.querySelectorAll("body *")) {
    if (el.closest("svg") || el.closest(".lang-toggle")) continue;
    const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!own || !el.getClientRects().length) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden") continue;
    const bg = bgOf(el);
    const fg = over(parse(cs.color), bg);
    const l1 = lum(fg), l2 = lum(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const size = parseFloat(cs.fontSize), bold = Number(cs.fontWeight) >= 700;
    const need = size >= 24 || (bold && size >= 18.66) ? 3 : 4.5;
    if (ratio < need) out.push(`${el.tagName.toLowerCase()}.${el.className} "${el.textContent.trim().slice(0, 30)}" ${ratio.toFixed(2)} < ${need}`);
  }
  return out;
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ executablePath: CHROME });
  for (const lang of ["ko", "en"]) {
    for (const width of [800, 375]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      const external = [];
      page.on("request", (r) => { if (!/^(file|data):/.test(r.url())) external.push(r.url()); });
      await page.goto(`${PAGE}?lang=${lang}`);
      await page.evaluate(() => document.fonts.ready);
      const tag = `${lang}-${width}`;
      await page.screenshot({ path: path.join(SHOTS, `${tag}.png`), fullPage: true });
      const r = await page.evaluate((other) => ({
        overflow: document.documentElement.scrollWidth - window.innerWidth,
        leaked: [...document.querySelectorAll(`body [lang="${other}"]`)].filter((e) => e.getClientRects().length).length,
        fontOk: document.fonts.check('16px "Paperlogy"'),
        placeholders: [...document.querySelectorAll(".placeholder")].filter((e) => e.getClientRects().length).length,
      }), lang === "ko" ? "en" : "ko");
      check(r.overflow <= 0, `${tag}: 가로 넘침 없음 (${r.overflow}px)`);
      check(r.leaked === 0, `${tag}: 다른 언어 요소 노출 0 (${r.leaked})`);
      check(r.fontOk, `${tag}: Paperlogy 로드`);
      check(r.placeholders === 0, `${tag}: placeholder 숨김`);
      check(external.length === 0, `${tag}: 외부 요청 0 (${external.join(", ")})`);
      if (width === 800) {
        const low = await page.evaluate(lowContrast);
        check(low.length === 0, `${tag}: 대비 AA ${low.length ? "\n      " + low.join("\n      ") : ""}`);
      }
      await page.close();
    }
  }
  await browser.close();

  for (const lang of ["KO", "EN"]) {
    const file = path.join(DIST, `DirectorsCut_${lang}.pdf`);
    const pdf = fs.readFileSync(file).toString("latin1");
    const pages = (pdf.match(/\/Type\s*\/Page(?!s)/g) || []).length;
    const uris = (pdf.match(/\/URI\s*\(/g) || []).length;
    check(pages === 1, `${lang} PDF: 1페이지 (${pages})`);
    check(uris >= 5, `${lang} PDF: 링크 보존 (${uris}개)`);
    check(pdf.includes("Paperlogy"), `${lang} PDF: Paperlogy 내장`);
  }

  console.log(fails.length ? `\n${fails.length}건 실패` : "\n전부 통과");
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
```

- [ ] **Step 2: 전체 빌드 후 실행**

Run:
```bash
cd "D:/Claude/AXTF/24_Director's cut" && python build/bundle.py && \
export PW_CORE=C:/Users/1000125/AppData/Local/Temp/pw/node_modules/playwright-core && \
node build/pdf.js && node build/verify.js
```
Expected: 마지막 줄 `전부 통과`.

- [ ] **Step 3: 실패 항목 수정**

실패하면 원인을 고치고(대개 `src/style.css` 색·폭) Step 2를 다시 돌린다. 예상되는 경우와 처리:
- `375: 가로 넘침` → 해당 요소를 `dist/shots/<lang>-375.png`에서 찾아 `@media (max-width:640px)` 블록에 규칙 추가.
- `대비 AA` → 출력된 요소의 글자색을 같은 계열의 더 진하거나 밝은 값으로 조정 (예: 라이트 구간 `--muted` 를 `#4f5370`로).
- `PDF: 1페이지 (2)` → `pdf.js`의 `height + 2` 여유를 `+ 8`로 늘림.
- PDF 링크·폰트 검사가 0으로 나오는데 PDF를 브라우저로 열어 보면 링크·폰트가 정상이면 PDF 객체 압축으로 문자열 검색이 안 되는 것이다. 검사를 임의로 약화하지 말고 사용자에게 보고하고 수동 확인으로 대체한다.

- [ ] **Step 4: 스크린샷 4장 육안 확인** — `dist/shots/ko-800.png`, `en-800.png`, `ko-375.png`, `en-375.png`를 Read. 겹침·잘림·어색한 줄바꿈(특히 영어 제목·버튼)을 확인하고 있으면 고친 뒤 Step 2 재실행.

- [ ] **Step 5: Commit**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && git add build/verify.js src/style.css src/index.html && \
git commit -m "test(directors-cut): 실행 검증 — 넘침·언어 누출·외부요청·대비·PDF"
```

---

### Task 8: 문구 점검과 전달

**Files:**
- Modify: `src/index.html` (맞춤법 수정이 있을 때만)

- [ ] **Step 1: 국문 맞춤법·브랜드 표기 점검**

`src/index.html`의 `lang="ko"` 문구(히어로 신규 문구 + 섹션 본문)를 `mcp__onestore-text__review`(없으면 `check_spelling`, `check_brand`)로 검사한다. 초안 원문의 **의미는 바꾸지 않는다** — 맞춤법·띄어쓰기·브랜드 표기만 반영. 반영 목록과 반영 안 한 지적(이유 포함)을 기록해 둔다.

- [ ] **Step 2: 재빌드·재검증**

Run: Task 7 Step 2 명령.
Expected: `전부 통과`.

- [ ] **Step 3: Commit (수정이 있었을 때만)**

```bash
cd "D:/Claude/AXTF/24_Director's cut" && git add src/index.html && \
git commit -m "fix(directors-cut): 국문 맞춤법·브랜드 표기 점검 반영"
```

- [ ] **Step 4: 사용자에게 전달**

보고 내용:
- `dist/DirectorsCut_KO.pdf`, `dist/DirectorsCut_EN.pdf`, `dist/DirectorsCut.html` 경로와 크기
- 검증 결과 (verify.js 출력 요약), 스크린샷 경로
- **사용자 확인 필요**: ① 영문 번역 검토(히어로·키워드는 신규 문구) ② placeholder 2곳(추가 혜택, 국가 리스트 URL) 값 ③ 로고 SVG 정식 파일 요청(onestorebrand@onestorecorp.com)
- OneDrive 업로드와 Anyone 링크 생성은 사용자가 직접. 업로드 후 시크릿 창·폰에서 PDF 미리보기 렌더 확인.
