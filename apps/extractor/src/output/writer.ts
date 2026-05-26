import * as fs from "node:fs";
import * as path from "node:path";
import type { ExtractedString } from "../types.js";

export function writeJson(out: string, extracted: ExtractedString[]): void {
  const normalized = extracted.map((e) => ({
    ...e,
    source_file: normalizePath(e.source_file),
  }));
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(normalized, null, 2) + "\n", "utf8");
}

function normalizePath(p: string): string {
  // strip leading absolute root so CI snapshots match local
  return p.replace(/\\/g, "/");
}
