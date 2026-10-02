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
  for (const lang of ["ko", "en", "zh"]) {
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
