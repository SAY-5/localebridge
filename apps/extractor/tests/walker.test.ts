import { describe, it, expect } from "vitest";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { walk } from "../src/ast/walker.js";

function tmpdir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), "lb-walker-"));
}

describe("walker", () => {
  it("extracts t() calls with default values", () => {
    const dir = tmpdir();
    fs.writeFileSync(
      path.join(dir, "a.tsx"),
      `import { useTranslation } from "react-i18next";
export function A() {
  const { t } = useTranslation();
  return <div>{t("a.key", { defaultValue: "Hello" })}</div>;
}`,
    );
    const { extracted } = walk(dir);
    expect(extracted).toHaveLength(1);
    expect(extracted[0]?.key).toBe("a.key");
    expect(extracted[0]?.default_value).toBe("Hello");
    expect(extracted[0]?.context).toBe("t-call");
  });

  it("extracts Trans component with i18nKey", () => {
    const dir = tmpdir();
    fs.writeFileSync(
      path.join(dir, "b.tsx"),
      `import { Trans } from "react-i18next";
export function B() {
  return <Trans i18nKey="greet">Hello world</Trans>;
}`,
    );
    const { extracted } = walk(dir);
    expect(extracted).toHaveLength(1);
    expect(extracted[0]?.key).toBe("greet");
    expect(extracted[0]?.context).toBe("trans-component");
  });

  it("extracts JSDoc @i18n annotated props", () => {
    const dir = tmpdir();
    fs.writeFileSync(
      path.join(dir, "c.tsx"),
      `export function C() {
  return (
    <a /** @i18n nav.home */ aria-label="Home">x</a>
  );
}`,
    );
    const { extracted } = walk(dir);
    const jsdoc = extracted.filter((e) => e.context === "jsdoc");
    expect(jsdoc).toHaveLength(1);
    expect(jsdoc[0]?.key).toBe("nav.home");
    expect(jsdoc[0]?.default_value).toBe("Home");
  });

  it("does not crash on malformed t() calls", () => {
    const dir = tmpdir();
    fs.writeFileSync(
      path.join(dir, "d.tsx"),
      `export function D() { return t(somevar); }`,
    );
    const { extracted } = walk(dir);
    expect(extracted).toEqual([]);
  });

  it("produces stable ordering", () => {
    const dir = tmpdir();
    fs.writeFileSync(
      path.join(dir, "z.tsx"),
      `export const z = () => t("z.k");`,
    );
    fs.writeFileSync(
      path.join(dir, "a.tsx"),
      `export const a = () => t("a.k");`,
    );
    const r1 = walk(dir).extracted.map((e) => e.key);
    const r2 = walk(dir).extracted.map((e) => e.key);
    expect(r1).toEqual(r2);
  });
});
