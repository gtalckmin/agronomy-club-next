import { describe, expect, it } from "vitest";

import { validateRegistration } from "./registration-validation";

describe("validateRegistration", () => {
  it("rejects different passwords", () => {
    expect(
      validateRegistration({
        fullName: "Member Example",
        graduationYear: "2029",
        discipline: "Agronomy",
        password: "password-123",
        confirmPassword: "different-password",
      }),
    ).toEqual({ confirmPassword: "Passwords do not match." });
  });
});
