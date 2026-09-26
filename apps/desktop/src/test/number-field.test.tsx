import { describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { NumberField } from "../components/NumberField";
import { getEntryValue, validateScientificNotation } from "../utils/numbers";

describe("NumberField", () => {
  it("vacío -> '0' al perder el foco (semántica get_entry_value)", () => {
    function Controlled() {
      const [value, setValue] = useState("101325");
      return <NumberField label="P0" value={value} onChange={setValue} />;
    }

    render(<Controlled />);
    const input = screen.getByLabelText("P0");
    fireEvent.change(input, { target: { value: "" } });
    expect(input).toHaveValue("");
    fireEvent.blur(input);
    expect(input).toHaveValue("0");
  });

  it("valida notación decimal y científica", () => {
    expect(validateScientificNotation("1.5e-3")).toBe(true);
    expect(validateScientificNotation("-2.4E+5")).toBe(true);
    expect(validateScientificNotation(".5")).toBe(true);
    expect(validateScientificNotation("abc")).toBe(false);
    expect(validateScientificNotation("1,5")).toBe(false);

    expect(getEntryValue("")).toBe("0");
    expect(getEntryValue("   ")).toBe("0");
    expect(getEntryValue("2.5")).toBe("2.5");
  });

  it("muestra error cuando el texto no es numérico", () => {
    function Controlled() {
      const [value, setValue] = useState("1");
      return <NumberField label="dt" value={value} onChange={setValue} />;
    }

    render(<Controlled />);
    const input = screen.getByLabelText("dt");
    fireEvent.change(input, { target: { value: "abc" } });
    fireEvent.blur(input);
    expect(screen.getByText("Notación numérica no válida")).toBeInTheDocument();
  });

  it("normaliza comas cuando se pide (ventanas DB)", () => {
    const onChange = vi.fn();
    render(<NumberField label="Hf0" value="1,5" onChange={onChange} normalizeCommas />);
    const input = screen.getByLabelText("Hf0");
    fireEvent.blur(input);
    expect(onChange).toHaveBeenLastCalledWith("1.5");
  });
});
