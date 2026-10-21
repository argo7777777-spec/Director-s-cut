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
  const ATTR = { ko: "ko", en: "en", zh: "zh-Hans", ja: "ja" };
  // CJK 전용 폰트: 언어 → [font-family, 실제 렌더 폰트명 정규식] (Paperlogy에도 한자가 있어 섞일 수 있음)
  const CJK = { zh: ["NotoSC", /Noto Sans SC/i], ja: ["NotoJP", /Noto Sans JP/i] };
  for (const lang of Object.keys(ATTR)) {
    const others = Object.entries(ATTR).filter(([k]) => k !== lang).map(([, v]) => v);
    for (const width of [800, 375]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      const external = [];
      page.on("request", (r) => { if (!/^(file|data):/.test(r.url())) external.push(r.url()); });
      await page.goto(`${PAGE}?lang=${lang}`);
      await page.evaluate(() => document.fonts.ready);
      const tag = `${lang}-${width}`;
      await page.screenshot({ path: path.join(SHOTS, `${tag}.png`), fullPage: true });
      const r = await page.evaluate((others) => {
        const loaded = (fam) => [...document.fonts].filter((f) => f.family.replace(/"/g, "") === fam && f.status === "loaded").length;
        return {
          overflow: document.documentElement.scrollWidth - window.innerWidth,
          leaked: [...document.querySelectorAll(others.map((o) => `body [lang="${o}"]`).join(","))].filter((e) => e.getClientRects().length).length,
          paperlogy: loaded("Paperlogy"),
          noto: { NotoSC: loaded("NotoSC"), NotoJP: loaded("NotoJP") },
          placeholders: [...document.querySelectorAll(".placeholder")].filter((e) => e.getClientRects().length).length,
        };
      }, others);
      check(r.overflow <= 0, `${tag}: 가로 넘침 없음 (${r.overflow}px)`);
      check(r.leaked === 0, `${tag}: 다른 언어 요소 노출 0 (${r.leaked})`);
      check(r.paperlogy === 3, `${tag}: Paperlogy 3웨이트 로드 (${r.paperlogy})`);
      if (CJK[lang]) {
        const [fam, re] = CJK[lang];
        check(r.noto[fam] === 3, `${tag}: ${fam} 3웨이트 로드 (${r.noto[fam]})`);
        // 한자·가나가 실제로 해당 Noto 폰트로 그려지는지
        const cdp = await page.context().newCDPSession(page);
        await cdp.send("DOM.enable");
        await cdp.send("CSS.enable");
        const { root } = await cdp.send("DOM.getDocument");
        const { nodeId } = await cdp.send("DOM.querySelector", { nodeId: root.nodeId, selector: `.lede[lang="${ATTR[lang]}"]` });
        const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId });
        const names = fonts.map((f) => `${f.familyName}:${f.glyphCount}`).join(", ");
        check(fonts.some((f) => re.test(f.familyName) && f.glyphCount > 20), `${tag}: 본문이 ${re.source}로 렌더 (${names})`);
        // 다른 CJK 폰트가 섞이지 않는지
        const other = Object.entries(CJK).filter(([k]) => k !== lang).map(([, [, o]]) => o);
        check(!fonts.some((f) => other.some((o) => o.test(f.familyName))), `${tag}: 다른 CJK 폰트 섞임 없음 (${names})`);
      }
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

  for (const lang of ["KO", "EN", "ZH", "JA"]) {
    const file = path.join(DIST, `DirectorsCut_${lang}.pdf`);
    const pdf = fs.readFileSync(file).toString("latin1");
    const pages = (pdf.match(/\/Type\s*\/Page(?!s)/g) || []).length;
    const uris = (pdf.match(/\/URI\s*\(/g) || []).length;
    check(pages === 1, `${lang} PDF: 1페이지 (${pages})`);
    check(uris >= 5, `${lang} PDF: 링크 보존 (${uris}개)`);
    check(pdf.includes("Paperlogy"), `${lang} PDF: Paperlogy 내장`);
    if (lang === "ZH") check(pdf.includes("NotoSansSC"), `${lang} PDF: Noto Sans SC 내장`);
    if (lang === "JA") check(pdf.includes("NotoSansJP"), `${lang} PDF: Noto Sans JP 내장`);
  }

  console.log(fails.length ? `\n${fails.length}건 실패` : "\n전부 통과");
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
