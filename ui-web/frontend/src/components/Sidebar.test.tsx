// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Sidebar, { formatLoginError } from "./Sidebar";

describe("Sidebar login error formatting", () => {
  it("returns actionable message for 401", () => {
    const msg = formatLoginError({
      response: { status: 401, data: { detail: "Invalid credentials" } },
    });
    expect(msg).toContain("Unauthorized");
    expect(msg).toContain("auto-bootstrap");
  });

  it("returns endpoint guidance for 404", () => {
    const msg = formatLoginError({ response: { status: 404 } });
    expect(msg).toContain("endpoint not found");
  });

  it("falls back to backend detail when present", () => {
    const msg = formatLoginError({
      response: { status: 400, data: { detail: "Bad request payload" } },
    });
    expect(msg).toBe("Bad request payload");
  });
});

describe("Sidebar render sanity", () => {
  it("renders login controls", () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    expect(screen.getByPlaceholderText("Username")).toBeTruthy();
    expect(screen.getByPlaceholderText("Password")).toBeTruthy();
  });
});
