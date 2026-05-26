import { Project, SourceFile, SyntaxKind } from "ts-morph";
import { extractTCalls } from "../extractors/t-call.js";
import { extractTransComponents } from "../extractors/trans-component.js";
import { extractJsDocAnnotated } from "../extractors/jsdoc.js";
import type { ExtractedString } from "../types.js";

export interface WalkResult {
  files_scanned: number;
  extracted: ExtractedString[];
}

/**
 * Walk every .ts/.tsx file under `src` and run each extractor strategy.
 * Stable sort by source_file then line to make output deterministic.
 */
export function walk(src: string): WalkResult {
  const project = new Project({
    skipAddingFilesFromTsConfig: true,
    compilerOptions: {
      jsx: 4 as unknown as number, // JsxEmit.Preserve
      allowJs: false,
    },
  });
  project.addSourceFilesAtPaths(`${src}/**/*.{ts,tsx}`);

  const sourceFiles = project.getSourceFiles();
  const extracted: ExtractedString[] = [];

  for (const sf of sourceFiles) {
    extracted.push(...runAll(sf));
  }

  extracted.sort((a, b) => {
    if (a.source_file !== b.source_file) {
      return a.source_file.localeCompare(b.source_file);
    }
    if (a.line !== b.line) return a.line - b.line;
    return a.key.localeCompare(b.key);
  });

  return { files_scanned: sourceFiles.length, extracted };
}

function runAll(sf: SourceFile): ExtractedString[] {
  const out: ExtractedString[] = [];
  out.push(...extractTCalls(sf));
  out.push(...extractTransComponents(sf));
  out.push(...extractJsDocAnnotated(sf));
  return out;
}

export { SyntaxKind };
