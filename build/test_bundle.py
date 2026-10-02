import base64
from pathlib import Path

import pytest

import bundle

FONT = Path(__file__).resolve().parents[2] / "Font" / "Paperlogy-4Regular.ttf"
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def test_sets_ok():
    html = '<div><p lang="ko">가</p><p lang="en">A</p><p lang="zh-Hans">甲</p></div>'
    assert bundle.check_lang_sets(html) == []


def test_sets_inline_spans_and_nested():
    html = ('<ul><li><span lang="ko">가</span><span lang="en">A</span><span lang="zh-Hans">甲</span>'
            '<ul><li lang="ko">나</li><li lang="en">B</li><li lang="zh-Hans">乙</li></ul></li></ul>')
    assert bundle.check_lang_sets(html) == []


def test_sets_void_sibling_does_not_break_set():
    html = '<div><img src="x.png"><p lang="ko">가</p><p lang="en">A</p><p lang="zh-Hans">甲</p></div>'
    assert bundle.check_lang_sets(html) == []


def test_sets_missing_en():
    errors = bundle.check_lang_sets('<div><p lang="ko">가</p></div>')
    assert len(errors) == 1 and "lang=en" in errors[0]


def test_sets_missing_zh():
    errors = bundle.check_lang_sets('<div><p lang="ko">가</p><p lang="en">A</p></div>')
    assert len(errors) == 2 and "zh-Hans" in errors[0]


def test_sets_wrong_order():
    errors = bundle.check_lang_sets(
        '<div><p lang="ko">가</p><p lang="zh-Hans">甲</p><p lang="en">A</p></div>')
    assert errors


def test_sets_en_without_ko():
    errors = bundle.check_lang_sets('<div><p lang="en">A</p></div>')
    assert len(errors) == 1


def test_sets_tag_mismatch():
    errors = bundle.check_lang_sets(
        '<div><p lang="ko">가</p><span lang="en">A</span><p lang="zh-Hans">甲</p></div>')
    assert len(errors) == 3


def test_sets_ignore_html_element_lang():
    html = '<html lang="ko" data-lang="ko"><body><p>x</p></body></html>'
    assert bundle.check_lang_sets(html) == []


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
        '<body><img src="assets/a.png"><p lang="ko">가</p><p lang="en">A</p>'
        '<p lang="zh-Hans">甲</p></body></html>',
        encoding="utf-8")
    out = bundle.build(src, tmp_path / "dist" / "o.html")
    html = out.read_text(encoding="utf-8")
    assert "style.css" not in html
    assert "data:font/woff2;base64," in html
    assert 'src="data:image/png;base64,' in html
    assert ".ttf" not in html


def test_build_fails_on_lang_set_error(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "style.css").write_text("", encoding="utf-8")
    (src / "index.html").write_text(
        '<link rel="stylesheet" href="style.css"><p lang="ko">가</p>', encoding="utf-8")
    with pytest.raises(SystemExit):
        bundle.build(src, tmp_path / "o.html")


def _make_src(tmp_path, css, body, head=""):
    src = tmp_path / "src"
    (src / "assets").mkdir(parents=True)
    (src / "assets" / "a.png").write_bytes(PNG_1PX)
    (src / "style.css").write_text(css, encoding="utf-8")
    (src / "index.html").write_text(
        '<html><head><link rel="stylesheet" href="style.css">%s</head><body>%s'
        '<p lang="ko">가</p><p lang="en">A</p><p lang="zh-Hans">甲</p></body></html>' % (head, body),
        encoding="utf-8")
    return src


def test_build_fails_on_single_quoted_css_url(tmp_path):
    src = _make_src(tmp_path, "@font-face{font-family:P;src:url('%s')}" % FONT.as_posix(), "")
    with pytest.raises(SystemExit):
        bundle.build(src, tmp_path / "o.html")


def test_build_fails_on_leftover_href(tmp_path):
    src = _make_src(tmp_path, "", "", head='<link rel="icon" href="assets/a.png">')
    with pytest.raises(SystemExit):
        bundle.build(src, tmp_path / "o.html")


def test_build_allows_fragment_and_external_refs(tmp_path):
    body = ('<svg><rect fill="url(#g)"/></svg><a href="#x">x</a>'
            '<a href="https://e.com">e</a>')
    src = _make_src(tmp_path, "", body)
    assert bundle.build(src, tmp_path / "o.html").exists()


def test_build_fails_on_missing_asset(tmp_path):
    src = _make_src(tmp_path, "", '<img src="assets/nope.png">')
    with pytest.raises(SystemExit) as e:
        bundle.build(src, tmp_path / "o.html")
    assert "nope.png" in str(e.value)
