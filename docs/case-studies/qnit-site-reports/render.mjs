// Render out/<id>.html to out/<id>.pdf with Playwright Chromium (A4, backgrounds on).
import { chromium } from "playwright";
import path from "node:path";

const id = process.argv[2] || "QNIT-BLR-S03";
const dir = path.resolve("out");
const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
const page = await browser.newPage();
await page.goto("file://" + path.join(dir, `${id}.html`), { waitUntil: "load" });
await page.pdf({ path: path.join(dir, `${id}.pdf`), format: "A4", printBackground: true, preferCSSPageSize: true });
await browser.close();
console.log("wrote", path.join(dir, `${id}.pdf`));
