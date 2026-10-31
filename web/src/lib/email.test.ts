import { describe, expect, it } from "vitest";

import { normalizeEmail } from "./email";

describe("normalizeEmail", () => {
  it("trims and lowercases", () => {
    expect(normalizeEmail("  Ada@Example.COM ")).toBe("ada@example.com");
  });

  it.each([null, 42, "", "ada", "ada@", "ada@example", "a b@example.com"])("rejects %s", (raw) => {
    expect(normalizeEmail(raw)).toBeNull();
  });

  it("rejects addresses over 254 characters", () => {
    expect(normalizeEmail(`${"a".repeat(250)}@x.co`)).toBeNull();
  });
});
