import { describe, expect, it } from "vitest";

import { isPublicPath, safeNextPath } from "./routes";

describe("isPublicPath", () => {
  it.each(["/sign-in", "/auth/confirm", "/spike/recorder"])("lets signed-out visitors open %s", (path) => {
    expect(isPublicPath(path)).toBe(true);
  });

  it.each(["/", "/settings", "/sign-inx", "/authority"])("requires a session for %s", (path) => {
    expect(isPublicPath(path)).toBe(false);
  });
});

describe("safeNextPath", () => {
  it("keeps same-site relative paths", () => {
    expect(safeNextPath("/settings")).toBe("/settings");
  });

  it.each([null, undefined, "", "https://evil.example", "//evil.example", "/\\evil.example"])(
    "falls back to / for %s",
    (next) => {
      expect(safeNextPath(next)).toBe("/");
    },
  );
});
