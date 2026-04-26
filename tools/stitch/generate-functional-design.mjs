import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { Stitch, StitchToolClient } from "@google/stitch-sdk";

const repoRoot = resolve(import.meta.dirname, "../..");
const briefPath = resolve(repoRoot, "docs/design/STITCH-FUNCTIONAL-BRIEF.md");
const stitchDir = resolve(repoRoot, ".stitch");
const outputPath = resolve(stitchDir, "functional-design-result.json");
const htmlPath = resolve(stitchDir, "functional-design.html");
const imagePath = resolve(stitchDir, "functional-design.png");

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  console.log([
    "Generate a Stitch design from docs/design/STITCH-FUNCTIONAL-BRIEF.md.",
    "",
    "Usage:",
    "  STITCH_API_KEY=... npm run functional-design",
    "",
    "Output:",
    "  .stitch/functional-design-result.json",
    "  .stitch/functional-design.html",
    "  .stitch/functional-design.png",
  ].join("\n"));
  process.exit(0);
}

const stitchAuth = process.env.STITCH_API_KEY || process.env.STITCH_ACCESS_TOKEN;
if (!stitchAuth) {
  throw new Error("Set STITCH_API_KEY before running this script.");
}

const brief = await readFile(briefPath, "utf8");
const prompt = `${brief.trim()} Render this as an actual app interface, not as a text document.`;
const generated = await generateWithRetry(prompt);
const result = {
  ...generated,
  generatedAt: new Date().toISOString(),
};

await mkdir(stitchDir, { recursive: true });
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
if (generated.htmlUrl) {
  await download(generated.htmlUrl, htmlPath);
}
if (generated.imageUrl) {
  await download(generated.imageUrl, imagePath);
}
console.log(JSON.stringify(result, null, 2));

async function generateWithRetry(promptText) {
  let lastError;
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    const client = new StitchToolClient({ apiKey: stitchAuth });
    try {
      const sdk = new Stitch(client);
      const project = await sdk.createProject("Styio Community Functional Design");
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
      if (attempt === 2) break;
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
