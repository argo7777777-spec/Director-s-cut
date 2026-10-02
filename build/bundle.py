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
LANGS = ("ko", "en", "zh-Hans")


class _LangSets(HTMLParser):
    """같은 부모 아래 lang=ko 요소 바로 뒤에 같은 태그의 lang=en, lang=zh-Hans 형제가 순서대로 오는지 검사."""

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
            if lang == LANGS[0]:
                run = kids[i:i + len(LANGS)]
                if [k[1] for k in run] == list(LANGS) and all(k[0] == tag for k in run):
                    i += len(LANGS)
                    continue
                self.errors.append(
                    f"line {line}: <{tag} lang=ko> 바로 뒤에 같은 태그의 lang=en, lang=zh-Hans 가 순서대로 없음")
            elif lang in LANGS[1:]:
                self.errors.append(f"line {line}: <{tag} lang={lang}> 가 lang=ko 로 시작하는 세트 밖에 있음")
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


def check_lang_sets(html: str) -> list[str]:
    p = _LangSets()
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
    if not path.is_file() or path.suffix.lower() not in MIME:
        raise SystemExit(f"asset 없음 또는 미지원 형식: {path}")
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
    errors = check_lang_sets(html)
    if errors:
        raise SystemExit("한/영/중 세트 오류:\n" + "\n".join(errors))
    n = count_placeholders(html)
    if n:
        print(f"경고: placeholder {n}곳 남음 — 공개본에서는 숨겨짐", file=sys.stderr)
    if CSS_LINK not in html:
        raise SystemExit(f"index.html에 {CSS_LINK} 가 없음")
    css = inline_fonts((src / "style.css").read_text(encoding="utf-8"), src, collect_text(html))
    html = html.replace(CSS_LINK, f"<style>\n{css}\n</style>")
    html = inline_images(html, src)
    left = [html[m.start():m.start() + 40] for m in re.finditer(
        r'''(?:\burl\(\s*+['"]?+|(?<![\w-])(?:src|href|srcset)=['"])(?!data:|#|https?:|mailto:)''', html)]
    if left:
        raise SystemExit(f"인라인 안 된 리소스: {left}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    path = build()
    print(f"{path} ({path.stat().st_size // 1024} KB)")
