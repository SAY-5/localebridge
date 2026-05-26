import { SourceFile, Node, JsxElement, JsxSelfClosingElement } from "ts-morph";
import type { ExtractedString } from "../types.js";

/**
 * Match <Trans i18nKey="foo">Hello {name}</Trans>.
 * If i18nKey is absent, derive a stable key from the inner text.
 */
export function extractTransComponents(sf: SourceFile): ExtractedString[] {
  const out: ExtractedString[] = [];
  sf.forEachDescendant((node) => {
    if (Node.isJsxElement(node)) {
      const opening = node.getOpeningElement();
      if (opening.getTagNameNode().getText() !== "Trans") return;
      const key = readI18nKey(opening) ?? deriveKeyFromChildren(node);
      const text = renderChildren(node);
      out.push({
        key,
        default_value: text,
        source_file: sf.getFilePath(),
        line: opening.getStartLineNumber(),
        context: "trans-component",
      });
    } else if (Node.isJsxSelfClosingElement(node)) {
      if (node.getTagNameNode().getText() !== "Trans") return;
      const key = readI18nKey(node);
      if (key === null) return;
      const defaults = readDefaultsProp(node) ?? key;
      out.push({
        key,
        default_value: defaults,
        source_file: sf.getFilePath(),
        line: node.getStartLineNumber(),
        context: "trans-component",
      });
    }
  });
  return out;
}

function readI18nKey(
  el: JsxSelfClosingElement | ReturnType<JsxElement["getOpeningElement"]>,
): string | null {
  for (const attr of el.getAttributes()) {
    if (!Node.isJsxAttribute(attr)) continue;
    if (attr.getNameNode().getText() !== "i18nKey") continue;
    const init = attr.getInitializer();
    if (init === undefined) continue;
    if (Node.isStringLiteral(init)) return init.getLiteralText();
  }
  return null;
}

function readDefaultsProp(el: JsxSelfClosingElement): string | null {
  for (const attr of el.getAttributes()) {
    if (!Node.isJsxAttribute(attr)) continue;
    if (attr.getNameNode().getText() !== "defaults") continue;
    const init = attr.getInitializer();
    if (init === undefined) continue;
    if (Node.isStringLiteral(init)) return init.getLiteralText();
  }
  return null;
}

function renderChildren(el: JsxElement): string {
  let out = "";
  for (const child of el.getJsxChildren()) {
    if (Node.isJsxText(child)) {
      out += child.getText();
    } else if (Node.isJsxExpression(child)) {
      const inner = child.getExpression();
      if (inner !== undefined) out += `{${inner.getText()}}`;
    } else if (Node.isJsxElement(child) || Node.isJsxSelfClosingElement(child)) {
      out += child.getText();
    }
  }
  return out.trim();
}

function deriveKeyFromChildren(el: JsxElement): string {
  const text = renderChildren(el);
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 64);
}
