import { SourceFile, Node, SyntaxKind, CallExpression } from "ts-morph";
import type { ExtractedString } from "../types.js";

/**
 * Match `t("key")` and `t("key", { defaultValue: "..." })`.
 * Skip calls whose first argument is not a string literal.
 */
export function extractTCalls(sf: SourceFile): ExtractedString[] {
  const out: ExtractedString[] = [];
  sf.forEachDescendant((node) => {
    if (!Node.isCallExpression(node)) return;
    if (!isTCall(node)) return;
    const args = node.getArguments();
    if (args.length === 0) return;
    const first = args[0];
    if (first === undefined) return;
    if (!Node.isStringLiteral(first) && !Node.isNoSubstitutionTemplateLiteral(first)) return;
    const key = first.getLiteralText();
    const defaultValue = readDefaultValue(node) ?? key;
    out.push({
      key,
      default_value: defaultValue,
      source_file: sf.getFilePath(),
      line: first.getStartLineNumber(),
      context: "t-call",
    });
  });
  return out;
}

function isTCall(call: CallExpression): boolean {
  const expr = call.getExpression();
  const text = expr.getText();
  return text === "t" || text.endsWith(".t");
}

function readDefaultValue(call: CallExpression): string | null {
  const args = call.getArguments();
  if (args.length < 2) return null;
  const second = args[1];
  if (second === undefined) return null;
  if (!Node.isObjectLiteralExpression(second)) return null;
  for (const prop of second.getProperties()) {
    if (prop.getKind() !== SyntaxKind.PropertyAssignment) continue;
    const text = prop.getText();
    const match = text.match(/^defaultValue\s*:\s*(['"])([^'"]*)\1/);
    if (match && match[2] !== undefined) return match[2];
  }
  return null;
}
