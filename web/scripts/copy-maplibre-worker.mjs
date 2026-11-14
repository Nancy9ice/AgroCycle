#!/usr/bin/env node
/**
 * MapLibre GL v6 runs its geometry code in a Web Worker and looks for the worker file next to
 * the bundled chunk, which bundlers do not emit. This copies the worker (and the shared module
 * it imports) into `public/vendor/maplibre/`, where `setWorkerUrl` points. The copy is
 * git-ignored and refreshed on install, dev and build.
 */
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(webRoot, "node_modules/maplibre-gl/dist");
const target = resolve(webRoot, "public/vendor/maplibre");

mkdirSync(target, { recursive: true });
for (const file of ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"]) {
  copyFileSync(resolve(source, file), resolve(target, file));
}
console.log("copy-maplibre-worker: copied worker files to public/vendor/maplibre");
