"""Level-Set propellant regression (port of ``legacy/back_modules/back_1.py``).

Numbers, update order and stop conditions are identical to the legacy module.
The GUI coupling is replaced by callbacks:

* ``on_message(message)`` is called with exactly the same strings the original
  inserted into the ``CTkTextbox`` (including the leading ``\\n`` of the final
  messages). When a textbox-like object is passed instead, it is adapted
  (``insert("end", ...)`` + ``see`` + ``update_idletasks``).
* ``cancel_check()`` returning ``True`` stops the simulation and emits
  ``"\\nSimulación cancelada.\\n"``.

Note: the original typo ``"Diveregencia Detectada"`` is preserved on purpose.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable
from typing import Any

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from scipy.optimize import fsolve


def _as_message_sink(on_message: Any) -> Callable[[str], None]:
    """Return a callable sink for ``on_message`` (callable or textbox-like)."""
    if on_message is None:
        return lambda message: None
    if callable(on_message):
        return on_message
    insert = getattr(on_message, "insert", None)
    if callable(insert):
        def sink(message: str) -> None:
            on_message.insert("end", message)
            see = getattr(on_message, "see", None)
            if callable(see):
                see("end")
            update = getattr(on_message, "update_idletasks", None)
            if callable(update):
                update()
        return sink
    raise TypeError("on_message must be callable or a textbox-like object")


class PropellantRegresionLSM:
    def __init__(
        self,
        on_message: Callable[[str], None] | Any = None,
        cancel_check: Callable[[], bool] | None = None,
        dt: float | None = None,
        dh: float | None = None,
        maxIters: int | None = None,
        phi0: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None,
        init_data: dict | None = None,
        workingPrecision: int | None = None,
        image_resolution: tuple[int, int] | None = None,
    ):
        """
        Initialize the Propellant Regression Level Set Method (LSM) simulation.

        Parameters:
        - on_message (Callable[[str], None]): sink for console messages (callable
          or textbox-like object). The legacy ``textbox`` positional argument.
        - cancel_check (Callable[[], bool]): optional cancellation probe.
        - dt (float): Time step for the simulation.
        - dh (float): Spatial step size.
        - maxIters (int): Maximum number of iterations for the simulation.
        - phi0 (tuple[np.ndarray, np.ndarray, np.ndarray]): Initial level set function and grid coordinates (X, Y).
        - init_data (dict): Dictionary containing initial simulation data.
        - workingPrecision (int): Precision for rounding time values.
        - image_resolution (tuple[int, int]): Resolution for image outputs.
        """

        # Simulation parameters
        self.on_message = _as_message_sink(on_message)
        self.cancel_check = cancel_check if callable(cancel_check) else None
        self.cancelled = False
        self.dt = dt  # Time step
        self.h = dh  # Spatial step size
        self.maxIters = int(maxIters)  # Maximum iterations
        self.workingPrecision = workingPrecision  # Working precision
        self.image_resolution = image_resolution  # Image resolution

        # Calculate the number of decimals for rounding based on dt
        self.decimals = max(0, -int(math.floor(math.log10(self.dt))))

        # Initialize iteration count
        self.iterationCount = 1

        # Initialize level set function and grid coordinates
        self.phi_init, self.X, self.Y = phi0

        # Get limits based on grid coordinates
        self.x_limits = (np.min(self.X), np.max(self.X))
        self.y_limits = (np.min(self.Y), np.max(self.Y))

        # Extract initial data for simulation
        self.P0     = init_data["P0"]  # Initial pressure
        self.a      = init_data["a"] * 1e-2  # Some parameter a (converted from cm to m)
        self.n      = init_data["n"]  # Some exponent n
        self.R      = init_data["R"]  # Radius
        self.T1     = init_data["T1"]  # Initial temperature
        self.cChar  = init_data["cChar"]  # Characteristic speed
        self.rho_b  = init_data["rho_b"]  # Density of the propellant
        self.At     = init_data["Rt"]**2 * np.pi  # Throat area
        self.l_comb = init_data["Lc"]  # Combustion length
        self.R2     = init_data["R2"]  # Another radius

        # Maximum and minimum pressures
        self.P1_max = init_data["P1_max"]
        self.P1_min = init_data["P1_min"]

        # Time vector for the simulation
        self.time = np.round(np.arange(0, int(self.maxIters * self.dt) + self.dt, dt), self.workingPrecision)

        # Initialize arrays for simulation results
        self.P1 = np.zeros(self.maxIters)  # Pressure array
        self.r  = np.zeros(self.maxIters)  # Some parameter r
        self.Ab = np.zeros(self.maxIters)  # Area array
        self.Vc = np.zeros(self.maxIters)  # Combustion volume
        self.Vp = np.zeros(self.maxIters)  # Propellant volume
        self.Mp = np.zeros(self.maxIters)  # Propellant mass
        self.Gp = np.zeros(self.maxIters)  # Mass flow rate
        self.phi = np.zeros((self.maxIters, self.phi_init.shape[0], self.phi_init.shape[1]), dtype=np.float32)  # Level set over time

        # Set initial conditions
        self.P1[0] = self.P0                    # Initial pressure
        self.r[0] = self.a * self.P0**self.n    # Initial value for parameter r
        self.phi[0] = self.phi_init             # Initial level set function
        self.get_area_vol()                     # Calculate area and volume

        # Calculate initial propellant volume and mass
        self.Vp[0] = np.pi * (self.R2)**2 * self.l_comb - self.Vc[0]  # Initial volume of propellant
        self.Mp[0] = self.Vp[0] * self.rho_b                          # Initial mass of propellant

    def update_p(self):
        p_old   = self.P1[self.iterationCount - 1]
        r_old   = self.r[self.iterationCount - 1]
        Ab_old  = self.Ab[self.iterationCount - 1]
        Vc_old  = self.Vc[self.iterationCount - 1]

        # Función que representa la ecuación a resolver
        def implicit_equation(p_new):
            C1 = self.R * self.T1
            C2 = (Ab_old * self.rho_b / Vc_old) * r_old
            C3 = - (p_new * self.At) / (Vc_old * self.cChar)
            return p_new - p_old - self.dt * C1 * (C2 + C3)

        # Realizamos la búsqueda del valor de p_new que satisface la ecuación implícita
        p_new, = fsolve(implicit_equation, p_old)  # p_old como valor inicial

        self.P1[self.iterationCount] = p_new
        self.Gp[self.iterationCount] = p_new * self.At / self.cChar

    def update_r(self):
        p_old = self.P1[self.iterationCount - 1]
        r_new = self.a * p_old**self.n

        self.r[self.iterationCount] = r_new

    def update_front(self):
        phi_old = self.phi[self.iterationCount - 1]
        r_old   = self.r[self.iterationCount - 1]

        # Usar np.gradient para calcular el gradiente
        grad_x, grad_y = np.gradient(phi_old, self.h)

        # Derivadas hacia adelante
        D_plusX = grad_x[1:, :]  # Derivada hacia adelante en x
        D_plusY = grad_y[:, 1:]  # Derivada hacia adelante en y

        # Derivadas hacia atrás
        D_minX = grad_x[:-1, :]  # Derivada hacia atrás en x
        D_minY = grad_y[:, :-1]  # Derivada hacia atrás en y

        # Asegúrate de que las matrices sean del mismo tamaño
        D_plusX = np.pad(D_plusX, ((0, 1), (0, 0)), mode='edge')
        D_plusY = np.pad(D_plusY, ((0, 0), (0, 1)), mode='edge')
        D_minX = np.pad(D_minX, ((1, 0), (0, 0)), mode='edge')
        D_minY = np.pad(D_minY, ((0, 0), (1, 0)), mode='edge')

        nabla_plus = (np.maximum(D_minX, 0)**2 + np.minimum(D_plusX, 0)**2 +
                    np.maximum(D_minY, 0)**2 + np.minimum(D_plusY, 0)**2)
        nabla_min = (np.minimum(D_minX, 0)**2 + np.maximum(D_plusX, 0)**2 +
                    np.minimum(D_minY, 0)**2 + np.maximum(D_plusY, 0)**2)

        # Actualiza phi
        phi_new = self.phi[self.iterationCount - 1] - self.dt * (np.maximum(r_old, 0) * nabla_plus +
                                            np.minimum(r_old, 0) * nabla_min)

        radius = np.sqrt((self.X - 0.0)**2 + (self.Y - 0.0)**2)  # Centro en (0,0)
        mask = radius > self.R2
        phi_new[mask] = phi_old[mask]  # Usar la misma forma que phi_old para evitar el IndexError

        self.phi[self.iterationCount] = phi_new

    def checkEnd(self):
        if self.Mp[self.iterationCount-1] / self.Mp[0] < 0.001:
            return False
        else:
            return True

    def get_area_vol(self):
        phi_old = self.phi[self.iterationCount-1]

        # Crear una máscara para identificar las celdas en el frente (donde phi = 0)
        front_mask = (phi_old < 0) & (np.roll(phi_old, shift=1, axis=0) >= 0) | \
                     (phi_old < 0) & (np.roll(phi_old, shift=-1, axis=0) >= 0) | \
                     (phi_old < 0) & (np.roll(phi_old, shift=1, axis=1) >= 0) | \
                     (phi_old < 0) & (np.roll(phi_old, shift=-1, axis=1) >= 0)

        # Obtener las coordenadas de las celdas en el frente
        edge_coords = np.argwhere(front_mask)

        if edge_coords.size == 0:
            return 0, 0  # Si no hay celdas en el frente, la longitud y el área son 0

        # Inicializar la longitud del frente
        front_length = 0.0

        # Usar BFS para recorrer el frente
        visited = np.zeros_like(phi_old, dtype=bool)
        queue = deque([tuple(edge_coords[0])])  # Empezar desde el primer punto del borde
        visited[edge_coords[0][0], edge_coords[0][1]] = True

        # Direcciones de movimiento (vertical, horizontal, diagonal)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]

        # Calcular el radio para la máscara
        radius = np.sqrt((self.X - 0.0)**2 + (self.Y - 0.0)**2)  # Centro en (0,0)
        mask = radius > self.R2

        while queue:
            x, y = queue.popleft()

            # Solo computar la longitud del frente si no está en la máscara
            if not mask[x, y]:  # Excluir celdas más allá de R2
                for dx, dy in directions:
                    x2, y2 = x + dx, y + dy

                    # Asegurarse de que estamos dentro de los límites
                    if 0 <= x2 < phi_old.shape[0] and 0 <= y2 < phi_old.shape[1]:
                        if front_mask[x2, y2] and not visited[x2, y2]:  # Si la celda vecina está en el borde y no ha sido visitada
                            visited[x2, y2] = True
                            queue.append((x2, y2))

                            # Calcular la distancia real entre (x, y) y (x2, y2)
                            distance = np.sqrt((dx * self.h)**2 + (dy * self.h)**2)
                            front_length += distance  # Sumar la distancia real

        # Calcular el área interna
        interior_mask = phi_old < 0  # Máscara de las celdas interiores al frente (phi negativo)
        num_interior_points = np.sum(interior_mask)  # Contar los puntos interiores
        area = num_interior_points * (self.h**2)  # Área = número de puntos interiores * h^2

        self.Ab[self.iterationCount] = (front_length) * self.l_comb
        self.Vc[self.iterationCount] = (area) * self.l_comb
        self.Vp[self.iterationCount] = np.pi * (self.R2)**2 * self.l_comb - self.Vc[self.iterationCount-1]
        self.Mp[self.iterationCount] = self.Vp[self.iterationCount-1] * self.rho_b

    def run(self, textbox: Any = None) -> dict:
        """Run the simulation until a stop condition is met.

        ``textbox`` is only accepted for drop-in compatibility with the legacy
        signature; when given it overrides the ``on_message`` sink.
        """
        sink = self.on_message if textbox is None else _as_message_sink(textbox)

        while self.iterationCount < self.maxIters:
            # Cancellation probe (new in the engine: the GUI closed the progress
            # window instead).
            if self.cancel_check is not None and self.cancel_check():
                self.cancelled = True
                sink("\nSimulación cancelada.\n")
                break

            self.update_p()
            self.update_r()
            self.update_front()
            self.get_area_vol()
            self.iterationCount += 1

            # Formatear el texto que se va a mostrar en el textbox
            # Formatear el texto en notación científica con un ancho fijo de 10 caracteres
            message = (
                f"Iter: {self.iterationCount-1}\t"
                f"t(s): {self.time[self.iterationCount-1]:.{self.decimals}f}\t"
                f"P1 (Pa): {self.P1[self.iterationCount-1]:10.3e}\t"
                f"G (kg/s): {self.Gp[self.iterationCount-1]:10.3e}\t"
                f"Mp (kg): {self.Mp[self.iterationCount-1]:10.3e}\n"
            )

            # Publicar el mensaje en la consola (event/console del contrato)
            sink(message)

            # Verificar si la condición de finalización se cumple
            if not self.checkEnd():
                sink(f"\nSimulación terminada en el tiempo {self.time[self.iterationCount]:.3f}.\n")
                break  # Detener el evento de animación

            if not self.P1_min <= self.P1[self.iterationCount-1] <= self.P1_max:
                sink("\nPresión calculada fuera de rango. Simulación detenida.\n")
                break  # Detener el evento de animación

            if np.abs(np.diff(self.P1[-2:]))[0] > 1e6:
                sink("\nDiveregencia Detectada. Simulación detenida.\n")
                break  # Detener el evento de animación

        results = {
            "PHI": self.phi,
            "TIME": self.time[:self.iterationCount],
            "P1": self.P1[:self.iterationCount],
            "GP": self.Gp[:self.iterationCount],
            "MP": self.Mp[:self.iterationCount]
        }

        return results

    def result_figure(self):
        # Configuración de la figura
        fig, ax = plt.subplots()
        ax.set_title('Método Level Set - Evolución de la Interfaz')
        ax.set_aspect('equal')
        ax.set_xlim(self.x_limits)
        ax.set_ylim(self.y_limits)

        circle_outer = Circle((0.0, 0.0), self.R2, edgecolor='black', facecolor='lightgray', lw=4)
        ax.add_patch(circle_outer)

        # Definir un colormap (puedes elegir uno como 'viridis', 'plasma', etc.)
        cmap = cm.jet  # Puedes cambiar a otros mapas de colores como 'plasma', 'inferno', etc.

        # Dibujar contornos para las iteraciones
        for i in np.linspace(0, self.iterationCount - 1, self.image_resolution, dtype=int)[:-1]:
            # Normalizar el índice de iteración para el colormap
            normalized_index = i / (self.iterationCount - 1)  # Normaliza entre 0 y 1
            color = cmap(normalized_index)  # Obtiene el color correspondiente del colormap
            ax.contour(self.X, self.Y, self.phi[i], levels=[0], colors=[color], zorder=20)

        ax.set_title(f'Método Level Set - Tiempo: {self.P1[-1]:.0f}')
        ax.set_xlim(self.x_limits)
        ax.set_ylim(self.y_limits)
        ax.set_aspect('equal')

        # Crear la animación
        return fig

    def plot_pressure(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.time[:self.iterationCount], self.P1[:self.iterationCount])
        ax.set_title('Pressure vs. Time')           # Updated title
        ax.set_xlabel('Time')                       # Add x-axis label
        ax.set_ylabel('Pressure')                   # Add y-axis label
        ax.set_aspect('auto')                       # Change aspect to auto

        return fig

    def plot_massFlow(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.time[:self.iterationCount], self.Gp[:self.iterationCount])
        ax.set_title('Mass Flow vs. Time')          # Updated title
        ax.set_xlabel('Time')                       # Add x-axis label
        ax.set_ylabel('Mass Flow')                  # Add y-axis label
        ax.set_aspect('auto')                       # Change aspect to auto

        return fig

    def plot_massBurn(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.time[:self.iterationCount], self.Mp[:self.iterationCount])
        ax.set_title('Mass Burn vs. Time')          # Updated title
        ax.set_xlabel('Time')                       # Add x-axis label
        ax.set_ylabel('Mass Burn')                  # Add y-axis label
        ax.set_aspect('auto')                       # Change aspect to auto

        return fig
