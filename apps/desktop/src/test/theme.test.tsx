import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ThemeProvider, useTheme } from "../theme";

function Probe() {
  const { theme, mode, setMode, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="state">{`${theme}:${mode}`}</span>
      <button type="button" onClick={() => setMode(mode === "dark" ? "light" : "dark")}>
        toggle-mode
      </button>
      <button type="button" onClick={() => setTheme(theme === "red" ? "orange" : "red")}>
        toggle-theme
      </button>
    </div>
  );
}

describe("ThemeProvider", () => {
  it("aplica red+dark por defecto y persiste modo y tema", () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );

    expect(screen.getByTestId("state")).toHaveTextContent("red:dark");
    expect(document.documentElement.dataset.theme).toBe("red");
    expect(document.documentElement.dataset.mode).toBe("dark");

    fireEvent.click(screen.getByText("toggle-mode"));
    expect(screen.getByTestId("state")).toHaveTextContent("red:light");
    expect(document.documentElement.dataset.mode).toBe("light");
    expect(window.localStorage.getItem("openred.mode")).toBe("light");

    fireEvent.click(screen.getByText("toggle-theme"));
    expect(screen.getByTestId("state")).toHaveTextContent("orange:light");
    expect(document.documentElement.dataset.theme).toBe("orange");
    expect(window.localStorage.getItem("openred.theme")).toBe("orange");
  });

  it("lee el tema persistido en localStorage", () => {
    window.localStorage.setItem("openred.theme", "orange");
    window.localStorage.setItem("openred.mode", "light");
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("state")).toHaveTextContent("orange:light");
    expect(document.documentElement.dataset.theme).toBe("orange");
    expect(document.documentElement.dataset.mode).toBe("light");
  });
});
