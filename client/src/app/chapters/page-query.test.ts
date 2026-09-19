import { describe, expect, it } from "vitest";

import { normaliseChapterPage } from "./page-query";

describe("normaliseChapterPage", () => {
  it("uses the requested positive whole-number page without router state", () => {
    expect(normaliseChapterPage("2")).toBe(2);
  });

  it("falls back to the first page for missing or invalid query values", () => {
    expect(normaliseChapterPage(null)).toBe(1);
    expect(normaliseChapterPage("0")).toBe(1);
    expect(normaliseChapterPage("-1")).toBe(1);
    expect(normaliseChapterPage("1.5")).toBe(1);
    expect(normaliseChapterPage("not-a-page")).toBe(1);
  });
});
