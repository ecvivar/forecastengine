const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const PAGES = [
  { url: "/", name: "01-dashboard" },
  { url: "/teams", name: "02-teams" },
  { url: "/groups", name: "03-groups" },
  { url: "/groups/A", name: "04-group-detail" },
  { url: "/knockout", name: "05-knockout" },
  { url: "/bracket", name: "06-bracket" },
  { url: "/matches", name: "07-matches" },
  { url: "/predictions", name: "08-predictions" },
  { url: "/rankings", name: "09-rankings" },
  { url: "/simulations", name: "10-simulations" },
  { url: "/calibration", name: "11-calibration" },
];

const OUT_DIR = path.join(__dirname, "..", "screenshots");
const BASE_URL = "http://localhost:3000";

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  for (const page of PAGES) {
    const url = `${BASE_URL}${page.url}`;
    console.log(`Capturing: ${url}`);
    try {
      const p = await context.newPage();
      await p.goto(url, { waitUntil: "networkidle", timeout: 30000 });
      await p.waitForTimeout(2000); // Wait for recharts to render
      await p.screenshot({
        path: path.join(OUT_DIR, `${page.name}.png`),
        fullPage: true,
      });
      await p.close();
      console.log(`  Saved: ${page.name}.png`);
    } catch (err) {
      console.log(`  FAILED: ${page.url} - ${err.message}`);
    }
  }

  await browser.close();
  console.log("Done!");
}

main();
