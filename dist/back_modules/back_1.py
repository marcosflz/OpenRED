from imports import *
from functions import *


class PropellantRegresionLSM:
    def __init__(self, textbox: Any, dt: float, dh: float, maxIters: int, phi0: tuple[np.ndarray, np.ndarray, np.ndarray], init_data: dict, workingPrecision: int, image_resolution: tuple[int, int]):
        """
        Initialize the Propellant Regression Level Set Method (LSM) simulation.

        Parameters:
        - textbox (Any): Textbox for displaying messages or results.
        - dt (float): Time step for the simulation.
        - dh (float): Spatial step size.
        - maxIters (int): Maximum number of iterations for the simulation.
        - phi0 (tuple[np.ndarray, np.ndarray, np.ndarray]): Initial level set function and grid coordinates (X, Y).
        - init_data (dict): Dictionary containing initial simulation data.
        - workingPrecision (int): Precision for rounding time values.
        - image_resolution (tuple[int, int]): Resolution for image outputs.
        """

        # Simulation parameters
        self.textbox = textbox
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
        self.phi = np.zeros((self.maxIters, self.phi_init.shape[0], self.phi_init.shape[1]), dtype=np.float32)  # Level set function over time

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
        self.Vp[self.iterationCount] = np.pi * (self.R2)**2 * self.l_comb  - self.Vc[self.iterationCount-1]
        self.Mp[self.iterationCount] = self.Vp[self.iterationCount-1] * self.rho_b



    def run(self, textbox):
        while self.iterationCount < self.maxIters:
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

            

            
            # Insertar el mensaje en el CTkTextbox
            textbox.insert("end", message)
            
            # Autodesplazamiento al final para que siempre se vea el último mensaje
            textbox.see("end")
            
            # Actualizar la interfaz gráfica para que se muestren los mensajes en tiempo real
            textbox.update_idletasks()

            # Verificar si la condición de finalización se cumple
            if not self.checkEnd():
                textbox.insert("end", f"\nSimulación terminada en el tiempo {self.time[self.iterationCount]:.3f}.\n")
                textbox.see("end")
                textbox.update_idletasks()  # Asegurarse de que el mensaje final se muestre
                break  # Detener el evento de animación

            if not self.P1_min <= self.P1[self.iterationCount-1] <= self.P1_max:
                textbox.insert("end", f"\nPresión calculada fuera de rango. Simulación detenida.\n")
                textbox.see("end")
                textbox.update_idletasks()  # Asegurarse de que el mensaje final se muestre
                break  # Detener el evento de animación

            if np.abs(np.diff(self.P1[-2:]))[0] > 1e6:
                textbox.insert("end", f"\nDiveregencia Detectada. Simulación detenida.\n")
                textbox.see("end")
                textbox.update_idletasks()  # Asegurarse de que el mensaje final se muestre
                break  # Detener el evento de animación
        
        results = {
            "PHI": self.phi, 
            "TIME":self.time[:self.iterationCount], 
            "P1":self.P1[:self.iterationCount], 
            "GP":self.Gp[:self.iterationCount],
            "MP":self.Mp[:self.iterationCount]
        }

        return results
    
    def result_figure(self):
        # Configuración de la figura
        fig, ax = plt.subplots()
        #contour = ax.contour(self.X, self.Y, self.phi[self.iterationCount-1], levels=[0], colors='red')
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
