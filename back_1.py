from imports import *
from functions import *



class TubularGrain:
    def __init__(self, inputs):
        # Lista de atributos que quieres asignar
        attributes = [
            "rIn_0b", "rOut", "rThrt", "lComb", 
            "rho_b", "a", "n", "gamma", "R", "T1", "P1_min","P1_max", "cChar",
            "delta_t", "P0"
        ]
        
        for attr, value in zip(attributes, inputs):
            setattr(self, attr, value)
        
    def Ab(self, r):
        return 2 * np.pi * r * self.lComb
        
    def Vc(self, r):
        return np.pi * r**2 * self.lComb
    
    def calcResults(self):
        self.sol, self.t = self.combTime()
        self.P = self.sol[:, 0]
        self.r = self.sol[:, 1]

        self.rDot = numerical_derivative(self.t, self.r)
        self.G = self.rho_b * self.Ab(self.r) * self.rDot
        self.M = self.lComb * np.pi * (self.rOut**2 - self.r**2) * self.rho_b

        self.meanPressure, self.meanMassFlow = self.mean_values()

        self.Pmin, self.Pmax = np.min(self.P), np.max(self.P)
        self.Gmin, self.Gmax = np.min(self.G), np.max(self.G)
        self.combustion_time = float(self.t[-1])
        self.combustion_mass = float(self.M[0])

    def combTime(self):

    
        def P_dot(u):
            P, r = u
            term_0 = self.R * self.T1
            term_1 = (self.rho_b * self.a * P**self.n * 1e-2 * self.Ab(r)/self.Vc(r)) 
            term_2 = (P * np.pi * self.rThrt**2) / (self.cChar * self.Vc(r))
            print(self.Ab(r), self.Vc(r))
            return term_0 * (term_1 - term_2)

        def r_dot(u):
            P, r = u
            return self.a * P**self.n * 1e-2
        
        
        # Initial conditions: [position, velocity]
        u0 = [self.P0, self.rIn_0b]
        h = self.delta_t
        # Solve the system using RK4 method with indefinite run
        f_system = [P_dot, r_dot]

        def rMax_condition(state):
            P, r = state
            return r >= self.rOut
        
        def maxPressureLimit(state):
            P, r = state
            return P > self.P1_max
        
        def minPressureLimit(state):
            P, r = state
            return P < self.P1_min
        
        stop_conditions = [rMax_condition, maxPressureLimit, minPressureLimit]
        sol, t = solve_ode_system(f_system, u0, h, "RK4", t_max=None, stop_conditions=stop_conditions, indefinite=True)
        
        return sol, t
        
    
    def mean_values(self):
        interval = self.t[-1] - self.t[0]
        mean_pressure = float(discreteIntegration(self.P, self.t) / interval)
        mean_massflow = float(discreteIntegration(self.G, self.t) / interval)
        return mean_pressure, mean_massflow
    
    def pressureGraph(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.t, self.P, label='Pressure',linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Pressure (Pa)')
        ax.set_title('Pressure vs Time')
        ax.grid(True)
        return fig

    def massFlowGraph(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.t, self.G, label='Mass Flow Rate',linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Mass Flow Rate (kg/s)')
        ax.set_title('Mass Flow Rate vs Time')
        ax.grid(True)
        return fig

    def massTimeGraph(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.t, self.M, label='Mass',linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Mass (kg)')
        ax.set_title('Mass vs Time')
        ax.grid(True)
        return fig
    
    def frontSection_plot(self):
        try:
            # Crear una figura y un eje
            #height = frame.winfo_height() / 100
            fig, ax = plt.subplots(figsize=(9, 9))

            radii = np.linspace(self.rOut, self.rIn_0b, 20)
            colors = plt.cm.jet(np.linspace(0, 1, 20))

            for i, radius in enumerate(radii):
                circle = patches.Circle((0, 0), radius, edgecolor=colors[i], facecolor=colors[i], label=f'Radius {radius:.2f}')
                ax.add_patch(circle)

            inner_circle = patches.Circle((0, 0), self.rIn_0b, facecolor='white', label='Initial Inner Radius')
            ax.add_patch(inner_circle)

            ## Establecer los límites del gráfico
            ax.set_xlim(-self.rOut * 1.1, self.rOut * 1.1)
            ax.set_ylim(-self.rOut * 1.1, self.rOut * 1.1)
            # Establecer el aspecto del gráfico para que sea igual
            ax.set_aspect('equal')
            # Añadir título y leyenda
            ax.set_title('Tubular')

        except Exception as e:
            print(e)
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()
        return fig
    
    def profileSection_plot(self):
        try:
            fig, ax = plt.subplots(figsize=(9, 9))
            h_tot = self.rOut - self.rIn_0b
            heights = np.linspace(0, h_tot, 20)
            colors = plt.cm.jet(np.linspace(0, 1, 20))
            colors_reversed = colors[::-1]

            # Dibuja rectángulos superiores
            for i, h in enumerate(heights):
                rectangle = patches.Rectangle((0, self.rIn_0b + h), self.lComb, h_tot / 20, edgecolor=colors_reversed[i], facecolor=colors_reversed[i])
                ax.add_patch(rectangle)

            # Dibuja rectángulos inferiores
            for i, h in enumerate(heights):
                rectangle = patches.Rectangle((0, -self.rOut + h), self.lComb, h_tot / 20, edgecolor=colors[i], facecolor=colors[i])
                ax.add_patch(rectangle)

            # Dibuja el rectángulo interior blanco superior
            inner_rectangle = patches.Rectangle((0, -self.rIn_0b), self.lComb, 2*self.rIn_0b, facecolor='white', edgecolor='black', label='Initial Inner Radius')
            ax.add_patch(inner_rectangle)


            ax.set_xlim(-self.lComb * 0.2, self.lComb * 1.2)
            ax.set_ylim(-self.rOut * 1.1, self.rOut * 1.1)

            ax.set_aspect('equal')
            ax.set_title('Tubular')
            return fig

        except Exception as e:
            print(e)
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()
        return fig
    


class EndBurnerGrain:
    def __init__(self, inputs):
        # Lista de atributos que quieres asignar
        attributes = [
            "lTube", "lProp", "rOut", "rThrt", 
            "rho_b", "a", "n", "gamma", "R", "T1", "P1_min","P1_max", "cChar",
            "delta_t", "P0"
        ]
        
        for attr, value in zip(attributes, inputs):
            setattr(self, attr, value)


    def calcResults(self):
        self.Vc0 = ((self.rOut - self.rThrt) * np.pi / 3) * (self.rOut**2 + self.rThrt**2 + self.rOut*self.rThrt)

        self.sol, self.t = self.combTime()
        self.P = self.sol[:, 0]
        self.l = self.sol[:, 1]

        self.lDot = numerical_derivative(self.t, self.l)
        self.G = self.rho_b * self.Ab() * self.lDot
        self.M = np.pi * self.rOut**2 * self.rho_b * (self.lProp - self.l)

        self.meanPressure, self.meanMassFlow = self.mean_values()

        self.Pmin, self.Pmax = np.min(self.P), np.max(self.P)
        self.Gmin, self.Gmax = np.min(self.G), np.max(self.G)
        self.combustion_time = float(self.t[-1])
        self.combustion_mass = float(self.M[0])

        
    def Ab(self):
        return np.pi * self.rOut**2
    
    def Vc(self, l):
        return np.pi * self.rOut**2 * l + self.Vc0

    def combTime(self):

    
        def P_dot(u):
            P, l = u
            term_0 = self.R * self.T1
            term_1 = (self.rho_b * self.a * P**self.n * 1e-2 * self.Ab()/self.Vc(l)) 
            term_2 = (P * np.pi * self.rThrt**2) / (self.cChar * self.Vc(l))
            return term_0 * (term_1 - term_2)

        def l_dot(u):
            P, l = u
            return self.a * P**self.n * 1e-2
        
        
        # Initial conditions:
        u0 = [self.P0, 0.0]
        h = self.delta_t
        # Solve the system using RK4 method with indefinite run
        f_system = [P_dot, l_dot]

        def lMax_condition(state):
            P, l = state
            return l >= self.lProp
        
        def maxPressureLimit(state):
            P, l = state
            return P > self.P1_max
        
        def minPressureLimit(state):
            P, l = state
            return P < self.P1_min

        def nanPressure(state):
            P, l = state
            return np.isnan(P) or np.isnan(l)
        
        stop_conditions = [lMax_condition, maxPressureLimit, minPressureLimit, nanPressure]
        sol, t = solve_ode_system(f_system, u0, h, "RK4", t_max=None, stop_conditions=stop_conditions, indefinite=True)
        
        return sol, t
        
    
    def mean_values(self):
        interval = self.t[-1] - self.t[0]
        mean_pressure = float(discreteIntegration(self.P, self.t) / interval)
        mean_massflow = float(discreteIntegration(self.G, self.t) / interval)
        return mean_pressure, mean_massflow
    
    def pressureGraph(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.t, self.P, label='Pressure',linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Pressure (Pa)')
        ax.set_title('Pressure vs Time')
        ax.grid(True)
        return fig

    def massFlowGraph(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.t, self.G, label='Mass Flow Rate',linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Mass Flow Rate (kg/s)')
        ax.set_title('Mass Flow Rate vs Time')
        ax.grid(True)
        return fig

    def massTimeGraph(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.t, self.M, label='Mass',linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Mass (kg)')
        ax.set_title('Mass vs Time')
        ax.grid(True)
        return fig
    
    def frontSection_plot(self):
        try:
            # Crear una figura y un eje
            fig, ax = plt.subplots(figsize=(9, 9))

            # Dibujar los círculos exteriores e interiores
            outer_circle = patches.Circle((0, 0), self.rOut, edgecolor='r', facecolor='tab:red', label='Outer Radius')
            # Añadir los círculos al gráfico
            ax.add_patch(outer_circle)

            ax.set_xlim(-self.rOut * 1.1, self.rOut * 1.1)
            ax.set_ylim(-self.rOut * 1.1, self.rOut * 1.1)
            # Establecer el aspecto del gráfico para que sea igual
            ax.set_aspect('equal')
            ax.set_title('End-Burner')

        except Exception:
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()
        return fig
    
    def profileSection_plot(self):
        try:
            # Crear una figura y un eje
            fig, ax = plt.subplots(figsize=(9, 9))

            # Longitud total del rectángulo
            l_tot = self.lProp
            widths = np.linspace(0, l_tot, 40)
            colors = plt.cm.jet(np.linspace(0, 1, 40))

            # Dibujar franjas verticales de colores en el rectángulo
            for i, w in enumerate(widths[:-1]):
                rectangle = patches.Rectangle((w, -self.rOut), widths[1] - widths[0], 2 * self.rOut, edgecolor=colors[i], facecolor=colors[i])
                ax.add_patch(rectangle)

            ax.set_xlim(-self.lProp * 0.1, self.lProp * 1.1)
            ax.set_ylim(-self.rOut * 1.1, self.rOut * 1.1)
            # Establecer el aspecto del gráfico para que sea igual
            ax.set_aspect('equal')
            ax.set_title('End-Burner')

        except Exception:
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()
        return fig