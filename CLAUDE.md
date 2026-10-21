# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static one-page brochure for ONE store's **Director's Cut Zone**, written for outside game companies. It's in four languages: Korean, English, Simplified Chinese and Japanese. One HTML source gets built into a single self-contained HTML file plus one tall PDF per language (800px wide, one page). These files are shared through OneDrive links; the user does the upload, not Claude. The design spec is in `docs/superpowers/specs/` and the implementation plan is in `docs/superpowers/plans/`. Code comments and docs are in Korean.

## Commands

Requires Python with `fontTools`, `brotli` and `pytest`, plus Node with `playwright-core` and a system Chrome install.

```bash
pytest build -q                                   # unit tests for bundle.py
pytest build/test_bundle.py::test_sets_missing_en # single test
python build/bundle.py                            # src/ → dist/DirectorsCut.html
node build/pdf.js                                 # dist HTML → DirectorsCut_{KO,EN,ZH,JA}.pdf
node build/verify.js                              # browser checks on HTML + PDFs; exit 1 on any FAIL
```

- The Node scripts load Playwright from `PW_CORE` and fall back to `require("playwright-core")`. Chrome comes from `CHROME`, which defaults to `C:/Program Files/Google/Chrome/Application/chrome.exe`. The plan uses a hard-coded `PW_CORE` path from a different machine, so set your own.
- Full rebuild order: `bundle.py` → `pdf.js` → `verify.js`. `verify.js` reads the PDFs, so it must run after `pdf.js`.
- **Fonts are outside the repo.** `src/style.css` and `build/test_bundle.py` both expect TTFs at `../Font/` relative to the project root (Paperlogy 4/6/8, NotoSansSC and NotoSansJP Regular/SemiBold/ExtraBold). The build and font tests fail if that folder is missing. The NotoSansJP statics were instanced from Google Fonts' variable `NotoSansJP[wght].ttf` at 400/600/800.

## Architecture

**Language switching is CSS only.** Every translatable element comes as a set of four sibling elements with the same tag, always in the order `lang="ko"`, `lang="en"`, `lang="zh-Hans"`, `lang="ja"`. The `data-lang` attribute on `<html>` (`ko|en|zh|ja`) hides the other three through rules in `style.css`. A small inline script sets `data-lang` from `?lang=` and from the KO/EN/中文/日本語 toggle. There's no translation dictionary and no templating. Text that doesn't change between languages (brand names, URLs) is left without a `lang` attribute.

**`bundle.py` enforces the set rule.** `check_lang_sets` fails the build when a `ko` element isn't followed directly by its `en`, `zh-Hans` and `ja` siblings with the same tag, or when an `en`/`zh-Hans`/`ja` element appears outside a set. Anything given the `placeholder` class is hidden in output, and the build prints a warning for it.

**The output must be fully self-contained (zero external requests).** `bundle.py` handles this as follows:
- It inlines `style.css`. `index.html` must contain the exact line `<link rel="stylesheet" href="style.css">`.
- It turns `src="assets/..."` images (png/jpg only) into base64.
- It subsets each `url("...ttf")` font in the CSS down to the glyphs used in the page text plus printable ASCII, then embeds it as base64 WOFF2. The font URL must be double-quoted or it won't be inlined.
- It fails the build if any relative `src`/`href`/`url()` is still left. `#fragment`, `http(s):`, `mailto:` and `data:` are allowed.

**CJK font mixing.** Paperlogy also contains about 2k Han characters. The `NotoSC` faces are therefore limited by `unicode-range` to CJK ranges and come first in the `font-family` stack. Without that, Chinese text would render in a mix of two typefaces. Japanese uses separate `NotoJP` faces (same ranges plus kana), swapped in via `html[data-lang="ja"] body`, because Han glyph shapes differ between SC and JP. `verify.js` uses CDP to check that zh/ja body text renders in Noto Sans SC/JP respectively and that the other CJK font is not mixed in. `word-break: keep-all` is reset for `zh-Hans` and `ja` because they have no spaces to break on.

**`verify.js` checks**, for each language at 800px and 375px:
- no horizontal overflow
- no visible text from the other languages
- font weights loaded
- placeholders hidden
- zero external requests
- WCAG AA contrast (at 800px only)

It also checks each PDF: exactly 1 page, at least 5 link URIs kept, and fonts embedded. Screenshots go to `dist/shots/`. Contrast checks constrain color choices: for example, `.badge.red` uses `--red-ink` because white 13px text on `--red` fails AA.

## Constraints

- `dist/` is gitignored build output. Edit `src/`, never the files in `dist/`.
- Don't use the third-party game art in `screenshot/`; it's a UI reference only (rights issue). Game thumbnails in the phone mockup are abstract gradient placeholders.
- Keep proper-noun spellings fixed: "ONE store", "Director's Cut", "Director's Cut Zone", "ONE store Console" (원콘솔).
- The logo is a temporary PNG cut from the brand page, to be replaced when the official file arrives from the UXD group.
