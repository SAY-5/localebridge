import { describe, it, expect } from "vitest";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { walk } from "../src/ast/walker.js";

function tmpdir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), "lb-prop-"));
}

function rand<T>(arr: readonly T[]): T {
  const v = arr[Math.floor(Math.random() * arr.length)];
  if (v === undefined) throw new Error("empty array");
  return v;
}

function genKey(): string {
  const ns = rand(["nav", "auth", "settings", "inbox", "billing", "errors", "x_"]);
  const k = rand(["home", "title", "save", "cancel", "open", "close", "next", "back"]);
  return `${ns}.${k}`;
}

function genTCall(): string {
  const key = genKey();
  const def = rand(["Hello", "World", "Save", "Cancel", "Go", ""]);
  return `t("${key}"${def ? `, { defaultValue: "${def}" }` : ""})`;
}

function genTrans(): string {
  const key = genKey();
  const txt = rand(["Hello {name}", "Welcome", "Sign in", "Sign out"]);
  return `<Trans i18nKey="${key}">${txt}</Trans>`;
}

function genJunkTCall(): string {
  // not-a-string-literal first arg: extractor must skip silently
  return `t(${rand(["someVar", "1+2", "key.toString()", ""])})`;
}

function genFile(): string {
  const lines: string[] = ['import { useTranslation, Trans } from "react-i18next";'];
  lines.push("export function R() {");
  lines.push("  const { t } = useTranslation();");
  lines.push("  return (");
  lines.push("    <div>");
  const n = 1 + Math.floor(Math.random() * 10);
  for (let i = 0; i < n; i++) {
    const r = Math.random();
    if (r < 0.4) lines.push(`      {${genTCall()}}`);
    else if (r < 0.7) lines.push(`      ${genTrans()}`);
    else if (r < 0.85) lines.push(`      {${genJunkTCall()}}`);
    else lines.push("      <span>plain text</span>");
  }
  lines.push("    </div>");
  lines.push("  );");
  lines.push("}");
  return lines.join("\n");
}

describe("property: walker never crashes and is stable", () => {
  it("survives 50 random source trees", () => {
    for (let i = 0; i < 50; i++) {
      const dir = tmpdir();
      const files = 1 + Math.floor(Math.random() * 4);
      for (let j = 0; j < files; j++) {
        fs.writeFileSync(path.join(dir, `f${j}.tsx`), genFile());
      }
      const r1 = walk(dir);
      const r2 = walk(dir);
      // Stable across runs
      expect(r2.extracted).toEqual(r1.extracted);
      // Every extracted entry has the required shape
      for (const e of r1.extracted) {
        expect(typeof e.key).toBe("string");
        expect(e.key.length).toBeGreaterThan(0);
        expect(typeof e.default_value).toBe("string");
        expect(["t-call", "trans-component", "jsdoc"]).toContain(e.context);
      }
    }
  });

  it("does not invent keys when given files with no translations", () => {
    const dir = tmpdir();
    fs.writeFileSync(
      path.join(dir, "plain.tsx"),
      `export function P() { return <div>plain</div>; }`,
    );
    fs.writeFileSync(
      path.join(dir, "junk.tsx"),
      `export function J() { return <div>{t(someVariable)}</div>; }`,
    );
    expect(walk(dir).extracted).toEqual([]);
  });
});
