import { describe, expect, it } from "vitest";
import { diffTokens } from "../src/diff";

describe("diffTokens", () => {
  it("marks identical text as equal", () => {
    const d = diffTokens("hola mundo", "hola mundo");
    expect(d.every((t) => t.op === "equal")).toBe(true);
  });

  it("detects an added word", () => {
    const d = diffTokens("Inicio", "Inicio principal");
    const added = d.filter((t) => t.op === "add").map((t) => t.text);
    expect(added).toContain("principal");
  });

  it("detects a removed word", () => {
    const d = diffTokens("Página principal", "Página");
    const removed = d.filter((t) => t.op === "remove").map((t) => t.text);
    expect(removed).toContain("principal");
  });

  it("handles a full replacement", () => {
    const d = diffTokens("foo", "bar");
    expect(d.some((t) => t.op === "remove" && t.text === "foo")).toBe(true);
    expect(d.some((t) => t.op === "add" && t.text === "bar")).toBe(true);
  });

  it("treats empty strings as no tokens", () => {
    expect(diffTokens("", "")).toEqual([]);
  });
});
