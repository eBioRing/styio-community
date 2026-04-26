import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Stitch, StitchToolClient } from "@google/stitch-sdk";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "../..");
const briefPath = resolve(repoRoot, "docs/design/STITCH-THEME-BRIEF.md");
const stitchDir = resolve(repoRoot, ".stitch");
const outputPath = resolve(stitchDir, "theme-result.json");
const htmlPath = resolve(stitchDir, "stitch-screen.html");
const imagePath = resolve(stitchDir, "stitch-screen.png");

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  console.log([
    "Generate a Stitch theme screen from docs/design/STITCH-THEME-BRIEF.md.",
    "",
    "Usage:",
    "  STITCH_API_KEY=... npm run theme",
    "",
    "Output:",
    "  .stitch/theme-result.json",
    "  .stitch/stitch-screen.html",
    "  .stitch/stitch-screen.png",
  ].join("\n"));
  process.exit(0);
}

const stitchAuth = process.env.STITCH_API_KEY || process.env.STITCH_ACCESS_TOKEN;
if (!stitchAuth) {
  throw new Error("Set STITCH_API_KEY before running this script.");
}

const brief = await readFile(briefPath, "utf8");
const prompt = [
  brief,
  "",
  "Generate one desktop operations-console screen to refactor the existing Styio Community page.",
  "Use: top bar, left queue, central decision panel, optional compact progress rail.",
  "Show: route, status, 3 key facts, decision opinion, approve/reject/dispatch.",
  "Minimize prose. Avoid hero sections, stock images, profiles, and extra navigation.",
].join("\n");

const generated = await generateWithRetry(prompt);

const result = {
  projectId: generated.projectId,
  screenId: generated.screenId,
  htmlUrl: generated.htmlUrl,
  imageUrl: generated.imageUrl,
  generatedAt: new Date().toISOString(),
};

await mkdir(stitchDir, { recursive: true });
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
await download(generated.htmlUrl, htmlPath);
await download(generated.imageUrl, imagePath);
console.log(JSON.stringify(result, null, 2));

async function generateWithRetry(promptText) {
  let lastError;
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    const client = new StitchToolClient({ apiKey: stitchAuth });
    try {
      const sdk = new Stitch(client);
      const project = await sdk.createProject("Styio Community Decision Desk");
      const screen = await project.generate(promptText, "DESKTOP");
      const [htmlUrl, imageUrl] = await Promise.all([
        screen.getHtml(),
        screen.getImage(),
      ]);
      await client.close();
      return {
        projectId: project.projectId,
        screenId: screen.screenId,
        htmlUrl,
        imageUrl,
      };
    } catch (error) {
      lastError = error;
      await client.close().catch(() => {});
      if (attempt === 2) {
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
  throw lastError;
}

async function download(url, path) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to download ${url}: ${response.status}`);
  }
  const bytes = Buffer.from(await response.arrayBuffer());
  await writeFile(path, bytes);
}
