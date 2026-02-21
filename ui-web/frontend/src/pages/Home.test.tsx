// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import Home from "./Home";

describe("Home page sanity", () => {
  it("renders dashboard header", () => {
    render(<Home />);
    expect(screen.getByText("Sentifargo Dashboard")).toBeTruthy();
  });
});
