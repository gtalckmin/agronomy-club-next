import { describe, expect, it } from "vitest";

import { profileNeedsCompletion } from "./member-profile";

describe("profileNeedsCompletion", () => {
  it("asks imported members for missing fields", () => {
    expect(
      profileNeedsCompletion({
        id: 1,
        full_name: "Imported Member",
        grad_yr: null,
        discipline: "",
        email: "member@example.com",
        global_role: "user",
      }),
    ).toBe(true);
  });

  it("does not prompt members with a complete profile", () => {
    expect(
      profileNeedsCompletion({
        id: 1,
        full_name: "Complete Member",
        grad_yr: 2029,
        discipline: "Agronomy",
        email: "member@example.com",
        global_role: "user",
      }),
    ).toBe(false);
  });
});
