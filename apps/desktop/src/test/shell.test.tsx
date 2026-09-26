import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { AppShell } from "../app/AppShell";
import { TAB_STORAGE_KEY, TABS } from "../app/tabs";

describe("AppShell", () => {
  it("renderiza los 8 módulos en el sidebar", async () => {
    render(<AppShell />);
    const nav = await screen.findByTestId("module-nav");
    expect(within(nav).getAllByRole("button")).toHaveLength(8);
    for (const tab of TABS) {
      expect(within(nav).getByTestId(`nav-${tab.id}`)).toHaveTextContent(tab.label);
    }
  });

  it("cambia de módulo y persiste la pestaña activa", async () => {
    render(<AppShell />);
    fireEvent.click(await screen.findByTestId("nav-engine"));
    const content = screen.getByTestId("module-content");
    expect(within(content).getByText("Engine Design")).toBeInTheDocument();
    expect(window.localStorage.getItem(TAB_STORAGE_KEY)).toBe("engine");
  });

  it("arranca en la pestaña persistida", async () => {
    window.localStorage.setItem(TAB_STORAGE_KEY, "testbed");
    render(<AppShell />);
    const content = await screen.findByTestId("module-content");
    expect(within(content).getByText("Testing Bed")).toBeInTheDocument();
  });

  it("muestra el placeholder Soon en Documentation / OpenFOAM / Post-Processing", async () => {
    render(<AppShell />);
    for (const id of ["documentation", "openfoam", "post"] as const) {
      fireEvent.click(await screen.findByTestId(`nav-${id}`));
      const content = screen.getByTestId("module-content");
      expect(within(content).getByText("Soon")).toBeInTheDocument();
    }
  });
});
