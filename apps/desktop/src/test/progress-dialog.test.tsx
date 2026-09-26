import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ProgressDialog } from "../components/ProgressDialog";
import { mockCalls, resetMockCalls } from "../api/mock";

describe("ProgressDialog", () => {
  it("cancela la petición en curso (request.cancel {id}) y notifica", async () => {
    resetMockCalls();
    const onCancel = vi.fn();

    render(<ProgressDialog open title="Calculando" value={0.4} requestId={7} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    await waitFor(() => expect(onCancel).toHaveBeenCalledTimes(1));
    expect(
      mockCalls().some((call) => call.name === "request.cancel" && call.params.id === 7),
    ).toBe(true);
  });

  it("permite etiqueta de cancelación personalizada", async () => {
    const onCancel = vi.fn();
    render(<ProgressDialog open title="Progreso" onCancel={onCancel} cancelLabel="Abortar" />);
    fireEvent.click(screen.getByRole("button", { name: "Abortar" }));
    await waitFor(() => expect(onCancel).toHaveBeenCalled());
  });

  it("se cierra con ESC", () => {
    const onClose = vi.fn();
    render(<ProgressDialog open title="Progreso" onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
