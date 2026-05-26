import { SourceFile, Node } from "ts-morph";
import type { ExtractedString } from "../types.js";

const I18N_RE = /@i18n\s+([\w.\-]+)/;

/**
 * Match JSX attributes preceded by a JSDoc `@i18n key` comment.
 *
 * ts-morph's `getLeadingCommentRanges` returns nothing for trivia between JSX
 * tokens, so we read raw source text between the attribute's `getFullStart()`
 * (which includes leading trivia) and `getStart()` (which doesn't).
 */
export function extractJsDocAnnotated(sf: SourceFile): ExtractedString[] {
  const out: ExtractedString[] = [];
  const fullText = sf.getFullText();
  sf.forEachDescendant((node) => {
    if (!Node.isJsxAttribute(node)) return;
    const init = node.getInitializer();
    if (init === undefined) return;
    if (!Node.isStringLiteral(init)) return;
    const trivia = fullText.slice(node.getFullStart(), node.getStart());
    const match = trivia.match(I18N_RE);
    if (match === null) return;
    const key = match[1];
    if (key === undefined) return;
    out.push({
      key,
      default_value: init.getLiteralText(),
      source_file: sf.getFilePath(),
      line: node.getStartLineNumber(),
      context: "jsdoc",
    });
  });
  return out;
}
