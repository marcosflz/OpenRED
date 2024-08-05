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
        
    def Ab(self, r):
        return 2 * np.pi * r * self.lComb
        
    def Vc(self, r):
        return np.pi * r**2 * self.lComb

    def combTime(self):

    
        def P_dot(u):
            P, r = u
            term_0 = self.R * self.T1
            term_1 = (self.rho_b * self.a * P**self.n * 1e-2 * self.Ab(r)/self.Vc(r)) 
            term_2 = (P * np.pi * self.rThrt**2) / (self.cChar * self.Vc(r))
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
