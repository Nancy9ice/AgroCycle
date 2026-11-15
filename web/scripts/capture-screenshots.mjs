#!/usr/bin/env node
/**
 * Captures the app's screens for the 7-slide deck (PRD §13) from a RUNNING web app.
 *
 *   npm run build && npx next start -p 3004      # in one terminal
 *   npm run screenshots -- http://localhost:3004 ../docs/demo/screenshots
 *
 * Needs Chrome (set CHROME_PATH if it is not at the macOS default) and network access (map tiles).
 * No dependencies: it speaks the Chrome DevTools protocol directly.
 *
 * It photographs the app's real states and edits nothing. What each picture shows, and whether it is
 * real, labelled sample or preview, is written in docs/demo/README.md. If you change a path below,
 * change that guide too.
 */
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const base = (process.argv[2] ?? "http://localhost:3004").replace(/\/+$/, "");
const outDir = resolve(process.argv[3] ?? "../docs/demo/screenshots");
const chromePath =
  process.env.CHROME_PATH ??
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const WIDTH = 1280;
const VIEWPORT_HEIGHT = 900;
const PORT = 9360;

const everyConstraint =
  "manure=yes&hayOutlet=own_livestock&oatOutlet=yes&grainEquipment=have";
const someAnswers =
  "soil=high&water=medium&inputs=high&manure=no&hayOutlet=can_sell&oatOutlet=yes&grainEquipment=can_hire";

/**
 * `wait` is milliseconds to let the page settle; `drawer` opens an evidence drawer (the weather card's if
 * there is one); `viewport` skips full-page. Run against the API on the live data, every comparison here is a
 * real engine result. Without the API the web app has no weather values and the comparison says "not enough
 * evidence" for every field, which the guide explains.
 */
const shots = [
  { name: "01-home", path: "/" },
  // The map is sized to the window, so photograph the window, not the whole page.
  { name: "01b-add-your-field", path: "/field", wait: 8000, viewport: true },
  { name: "02-field-map", path: "/field?mode=demo", wait: 8000, viewport: true },
  { name: "03-profile", path: "/fields/primary-001/profile" },
  {
    name: "04-evidence-drawer",
    path: "/fields/primary-001/profile",
    drawer: true,
    viewport: true,
  },
  { name: "05-priorities", path: `/fields/primary-001/priorities?${someAnswers}` },
  { name: "06-compare-with-caveats", path: `/fields/primary-001/compare?${someAnswers}` },
  {
    name: "07-compare-worth-exploring",
    path: `/fields/primary-001/compare?${everyConstraint}&soil=high&inputs=high`,
  },
  {
    name: "08-compare-questions-unanswered",
    path: "/fields/primary-001/compare?soil=high&inputs=high",
  },
  { name: "09-compare-outside-domain", path: "/fields/test-027/compare" },
  {
    name: "10-compare-one-measure-incomplete",
    path: `/fields/test-022/compare?${everyConstraint}`,
  },
  { name: "11-adviser-brief", path: `/fields/primary-001/plan?${someAnswers}` },
  { name: "12-validation", path: "/validation" },
];

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

const chrome = spawn(
  chromePath,
  [
    "--headless=new",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${mkdtempSync(join(tmpdir(), "agrocycle-shots-"))}`,
    "about:blank",
  ],
  { stdio: "ignore" },
);

let socket;
try {
  await sleep(2500);
  const targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  socket = new WebSocket(
    targets.find((target) => target.type === "page").webSocketDebuggerUrl,
  );
  await new Promise((done, fail) => {
    socket.onopen = done;
    socket.onerror = fail;
  });

  let nextId = 0;
  const waiting = new Map();
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.id && waiting.has(message.id)) {
      waiting.get(message.id)(message.result);
      waiting.delete(message.id);
    }
  };
  const send = (method, params = {}) =>
    new Promise((done) => {
      const id = ++nextId;
      waiting.set(id, done);
      socket.send(JSON.stringify({ id, method, params }));
    });
  const evaluate = async (expression) =>
    (await send("Runtime.evaluate", { expression, returnByValue: true })).result.value;

  await send("Page.enable");
  await send("Runtime.enable");
  mkdirSync(outDir, { recursive: true });

  for (const shot of shots) {
    await send("Emulation.setDeviceMetricsOverride", {
      width: WIDTH,
      height: VIEWPORT_HEIGHT,
      deviceScaleFactor: 1,
      mobile: false,
    });
    await send("Page.navigate", { url: `${base}${shot.path}` });
    await sleep(shot.wait ?? 3500);

    if (shot.drawer) {
      await evaluate(`(() => {
        const buttons = [...document.querySelectorAll('button')].filter((b) => b.innerText.includes('Where this comes from'));
        (buttons.find((b) => /rain/i.test(b.closest('article')?.innerText ?? '')) ?? buttons[0])?.click();
      })()`);
      await sleep(700);
    }
    if (!shot.viewport) {
      const height = await evaluate("document.documentElement.scrollHeight");
      await send("Emulation.setDeviceMetricsOverride", {
        width: WIDTH,
        height,
        deviceScaleFactor: 1,
        mobile: false,
      });
      await sleep(500);
    }

    const { data } = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(outDir, `${shot.name}.png`), Buffer.from(data, "base64"));
    console.log(`captured ${shot.name}  (${shot.path})`);
  }
} finally {
  socket?.close();
  chrome.kill();
}
process.exit(0);
