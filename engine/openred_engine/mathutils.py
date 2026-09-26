"""Numerical utilities ported from ``legacy/functions.py`` (headless).

The algorithms are copied literally to preserve bit-for-bit parity with the
original application. The only intentional difference is the error handling:
where the legacy code popped a ``tkinter.messagebox`` it now raises an
exception, so the engine can be used without a GUI.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

__all__ = [
    "TempSchemes",
    "convert_to_latex",
    "discreteIntegration",
    "getSerialValues",
    "get_clean_component_name",
    "get_circle_points",
    "integration",
    "newtonRaph",
    "numerical_derivative",
    "read_json",
    "solve_ode_system",
    "validate_scientific_notation",
    "write_json_atomic",
    "write_text_atomic",
]


def validate_scientific_notation(value: str) -> bool:
    """
    Validates if a given string follows scientific notation format.

    Parameters:
    - value (str): The string to be validated.

    Returns:
    - bool: True if the string is in valid scientific notation, otherwise False.
    """

    # Regular expression pattern for matching scientific notation.
    pattern = r'^-?\d*\.?\d+(?:[eE][-+]?\d+)?$'

    # Use the 're.match' function to check if the value matches the pattern.
    # If it matches, return True; otherwise, return False.
    return re.match(pattern, value) is not None


def convert_to_latex(component: str) -> str:
    """
    Converts a chemical component string into LaTeX format by:
    1. Removing any text within parentheses.
    2. Converting numbers into subscript format for chemical notations.

    Args:
    - component (str): The chemical component string (e.g., "H2O", "C6H12O6").

    Returns:
    - str: A LaTeX-formatted string where numbers are subscripted.
    """

    # Step 1: Remove any text inside parentheses along with the parentheses themselves.
    component = re.sub(r'\(.*?\)', '', component).strip()

    # Step 2: Replace any numeric characters in the string with LaTeX subscript notation.
    component = re.sub(r'(\d+)', r'_{\1}', component)

    # Return the LaTeX-formatted component string.
    return component


def get_clean_component_name(component: str) -> str:
    """Remove numbers in parentheses at the end of the component name.

    Ported from ``front_chemWin.get_clean_component_name`` /
    ``front_propWin.get_clean_component_name``.
    """

    return re.sub(r'\(\d+\)$', '', component).strip()


def newtonRaph(f: Callable[[float], float], x0: float, tol: float, max_iter: int, h: float) -> float:
    """
    Newton-Raphson method for finding the roots of a function.

    Parameters:
    f : Callable[[float], float]
        The objective function for which the root is to be found.
    x0 : float
        Initial guess for the root.
    tol : float
        Tolerance level for convergence.
    max_iter : int
        Maximum number of iterations to perform.
    h : float
        Small step size for numerical derivative approximation.

    Returns:
    float
        The approximate root of the function.

    Raises:
    ValueError
        If the derivative is zero or the method does not converge. The legacy
        implementation displayed a messagebox instead.
    """

    def fp(f: Callable[[float], float], x: float, h: float) -> float:
        """
        Computes the numerical derivative of the function at a given point.

        Parameters:
        f : Callable[[float], float]
            The function for which the derivative is calculated.
        x : float
            The point at which the derivative is evaluated.
        h : float
            Small step size for derivative approximation.

        Returns:
        float
            The numerical derivative at point x.
        """
        return (f(x + h) - f(x - h)) / (2 * h)

    x = x0  # Start with the initial guess
    for _ in range(max_iter):
        fx = f(x)  # Evaluate the function at the current x
        dfx = fp(f, x, h)  # Calculate the numerical derivative

        if dfx == 0:  # Check for zero derivative to avoid division by zero
            raise ValueError("Zero derivative. Newton-Raphson method cannot proceed.")

        x_new = x - fx / dfx  # Update the root estimate using the Newton-Raphson formula

        if abs(x_new - x) < tol:  # Check for convergence
            return x_new  # Return the approximated root if within tolerance

        x = x_new  # Update x for the next iteration

    raise ValueError("Newton-Raphson method did not converge within the maximum number of iterations.")


def integration(f: Callable[[float], float], a: float, b: float, h: float) -> float:
    """
    Calculates the approximate definite integral of a function f over the interval [a, b]
    using the trapezoidal rule with a step size of h.

    Parameters:
    f : Callable[[float], float]
        The function to integrate. It takes a float as input and returns a float.
    a : float
        The lower limit of integration.
    b : float
        The upper limit of integration.
    h : float
        The step size for integration.

    Returns:
    float
        The approximate value of the definite integral of f over [a, b].
    """

    # Calculate the integral using the trapezoidal rule
    return h * ((f(a) + f(b)) / 2 + sum(f(a + k * h) for k in range(1, int((b - a) / h))))


def discreteIntegration(fs: list[float], xs: list[float]) -> float:
    """
    Calculates the approximate integral of discrete data points using the trapezoidal rule.

    Parameters:
    fs : List[float]
        The function values at discrete points.
    xs : List[float]
        The discrete points corresponding to the function values.

    Returns:
    float
        The approximate value of the integral computed using the trapezoidal rule.
    """
    # Calculate the integral using the trapezoidal rule
    return sum([(xs[i + 1] - xs[i]) * (fs[i + 1] + fs[i]) / 2 for i in range(len(fs) - 1)])


class TempSchemes:
    """
    A collection of numerical integration schemes for solving ordinary differential equations (ODEs).

    Methods:
    - Euler: Implements the Euler method for ODEs.
    - Heun: Implements the Heun method (a type of Runge-Kutta method) for ODEs.
    - RK4: Implements the fourth-order Runge-Kutta method for ODEs.
    """

    @staticmethod
    def Euler(f: Sequence[Callable[[np.ndarray], float]], u: np.ndarray, h: float) -> np.ndarray:
        """
        Performs a single step of the Euler method.

        Parameters:
        f : List[Callable[[np.ndarray], float]]
            A list of functions representing the derivatives of the system.
        u : np.ndarray
            The current state vector.
        h : float
            The time step for the integration.

        Returns:
        np.ndarray
            The updated state vector after one step of the Euler method.
        """
        k1 = np.array([fi(u) for fi in f])  # Evaluate the derivatives
        return u + h * k1  # Update the state vector

    @staticmethod
    def Heun(f: Sequence[Callable[[np.ndarray], float]], u: np.ndarray, h: float) -> np.ndarray:
        """
        Performs a single step of the Heun method (Improved Euler method).

        Parameters:
        f : List[Callable[[np.ndarray], float]]
            A list of functions representing the derivatives of the system.
        u : np.ndarray
            The current state vector.
        h : float
            The time step for the integration.

        Returns:
        np.ndarray
            The updated state vector after one step of the Heun method.
        """
        k1 = np.array([fi(u) for fi in f])  # Evaluate the derivatives at the current state
        k2 = np.array([fi(u + k1 * h) for fi in f])  # Evaluate the derivatives at the predicted state
        return u + h * (k1 + k2) / 2  # Update the state vector

    @staticmethod
    def RK4(f: Sequence[Callable[[np.ndarray], float]], u: np.ndarray, h: float) -> np.ndarray:
        """
        Performs a single step of the fourth-order Runge-Kutta method.

        Parameters:
        f : List[Callable[[np.ndarray], float]]
            A list of functions representing the derivatives of the system.
        u : np.ndarray
            The current state vector.
        h : float
            The time step for the integration.

        Returns:
        np.ndarray
            The updated state vector after one step of the RK4 method.
        """
        k1 = np.array([fi(u) for fi in f])  # Evaluate the derivatives at the current state
        k2 = np.array([fi(u + 0.5 * k1 * h) for fi in f])  # Evaluate the derivatives at the midpoint
        k3 = np.array([fi(u + 0.5 * k2 * h) for fi in f])  # Evaluate the derivatives at the next midpoint
        k4 = np.array([fi(u + k3 * h) for fi in f])  # Evaluate the derivatives at the next state
        return u + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6  # Update the state vector


def numerical_derivative(x: np.ndarray, f: np.ndarray) -> np.ndarray:
    """
    Computes the numerical derivative of a function given by arrays of x and f values.

    Parameters:
    - x: np.ndarray
        An array of x values (independent variable).
    - f: np.ndarray
        An array of f values (dependent variable).

    Returns:
    - np.ndarray
        An array of the numerical derivative df/dx.

    Raises:
    - ValueError: If the lengths of x and f are not the same.
    """
    if len(x) != len(f):
        raise ValueError("The length of x and f must be the same")

    df_dx = np.zeros_like(f)  # Initialize the derivative array with zeros

    # Central difference for the interior points
    df_dx[1:-1] = (f[2:] - f[:-2]) / (x[2:] - x[:-2])

    # Forward difference for the first point
    df_dx[0] = (f[1] - f[0]) / (x[1] - x[0])

    # Backward difference for the last point
    df_dx[-1] = (f[-1] - f[-2]) / (x[-1] - x[-2])

    return df_dx  # Return the computed derivative


def solve_ode_system(
    f_system: list,
    u0: np.ndarray,
    h: float,
    method: str,
    t_max: float,
    divergence_threshold: float = 1e6,
    stop_conditions: list | None = None,
    indefinite: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """
    General solver for a system of differential equations.

    Parameters:
    - f_system: list
        A list of functions defining the system of ODEs.
    - u0: np.ndarray
        Initial conditions as a list or numpy array.
    - h: float
        Step size for the integration.
    - method: str
        The integration method to use: "Euler", "Heun", or "RK4".
    - t_max: float
        Maximum time for the simulation.
    - divergence_threshold: float, optional
        Threshold for divergence detection (default is 1e6).
    - stop_conditions: list of functions, optional
        Each function takes the current state as input and returns a boolean indicating if the simulation should stop.
    - indefinite: bool, optional
        If True, the simulation will run indefinitely until a stop condition is met (default is False).

    Returns:
    - sol: np.ndarray
        A numpy array with the solution for each variable over time.
    - t: np.ndarray
        A numpy array with the time points.

    Raises:
    - ValueError: If ``method`` is not "Euler", "Heun" or "RK4".
    - RuntimeError: If the simulation diverges or a custom stop condition is met.
      The legacy implementation displayed a messagebox and silently returned.
    """
    # Dictionary to map method names to corresponding functions
    schemes = {
        "Euler": TempSchemes.Euler,
        "Heun": TempSchemes.Heun,
        "RK4": TempSchemes.RK4
    }

    if method not in schemes:
        raise ValueError("Method should be 'Euler', 'Heun', or 'RK4'")

    # Determine the initial number of steps based on t_max
    num_steps = int(t_max / h) + 1 if t_max else 1000  # Allocate space for results
    sol = np.zeros((num_steps, len(u0)))  # Solution array
    sol[0] = u0  # Set initial conditions

    t = np.zeros(num_steps)  # Time array

    i = 1  # Current step index
    while True:
        if not indefinite and i >= num_steps:
            break  # Stop if not indefinite and reached maximum steps

        if indefinite and i >= num_steps:
            # Expand arrays if running indefinitely
            sol = np.vstack([sol, np.zeros((1000, len(u0)))])
            t = np.hstack([t, np.zeros(1000)])
            num_steps += 1000  # Increase the number of steps allocated

        sol[i] = schemes[method](f_system, sol[i-1], h)  # Calculate the next step
        t[i] = t[i-1] + h  # Update time

        # Check for divergence
        if np.any(np.abs(sol[i] - sol[i-1]) > divergence_threshold):
            raise RuntimeError("Simulation stopped due to divergence.")

        # Check for custom stop conditions
        if stop_conditions:
            if any(condition(sol[i]) for condition in stop_conditions):
                raise RuntimeError("Simulation stopped due to custom stop condition.")

        i += 1  # Move to the next step

    # Trim the arrays to the actual size
    sol = sol[:i]
    t = t[:i]

    return sol, t  # Return the solution and time arrays


def getSerialValues(line: str) -> tuple[float, float, float] | None:
    """
    Extracts time, force, and temperature values from a text line
    in the format "t(s): <value>\\t F(kg): <value>\\t T(K): <value>".

    Args:
    - line (str): A string containing the values.

    Returns:
    - tuple: A tuple containing the time, force, and temperature as floats.
             Returns None if the values are not found in the expected format.
    """
    # Regular expression to capture the three specific values in the correct format
    match = re.match(
        r"t\(s\):\s*([-+]?\d*\.\d+|\d+)\s*F\(kg\):\s*([-+]?\d*\.\d+|\d+)\s*T\(K\):\s*([-+]?\d*\.\d+|\d+)", line
    )

    if match:  # If the line matches the expected format
        # Extract the three values and convert them to floats
        return tuple(map(float, match.groups()))
    else:
        # Return None if the expected format is not found
        return None


def get_circle_points(r: float, center: tuple[float, float] = (0, 0), num_points: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate points that define a circle.

    Args:
    r (float): The radius of the circle.
    center (Tuple[float, float], optional): The coordinates of the center of the circle. Defaults to (0, 0).
    num_points (int, optional): The number of points to generate around the circle. Defaults to 100.

    Returns:
    Tuple[np.ndarray, np.ndarray]: Two arrays containing the x and y coordinates of the points on the circle.
    """
    # Create a vector of angles from 0 to 2*pi
    t = np.linspace(0, 2 * np.pi, num_points)

    # Parametrize the circle and add the offset of the center
    x = center[0] + r * np.cos(t)  # x coordinates of the circle
    y = center[1] + r * np.sin(t)  # y coordinates of the circle

    return x, y  # Return the x and y coordinates


def read_json(path: str | os.PathLike[str]) -> Any:
    """Read a UTF-8 JSON file."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: str | os.PathLike[str], data: Any, indent: int | None = 4, **kwargs: Any) -> None:
    """Atomically write JSON to ``path`` (tmp file + ``os.replace``).

    ``indent=4`` matches the legacy writers (``app.save_configuration``,
    ``front_propDes.export_results``, ``front_nozDes.export_results``).
    """
    target = os.fspath(path)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=indent, **kwargs)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, target)


def write_text_atomic(path: str | os.PathLike[str], text: str) -> None:
    """Atomically write text to ``path`` (tmp file + ``os.replace``)."""
    target = os.fspath(path)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, target)
