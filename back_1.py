from imports import *
from functions import *



class TubularGrain:
    def __init__(self, inputs):
        # Lista de atributos que quieres asignar
        attributes = [
            "rIn_0b", "rOut", "rThrt", "lComb", 
            "rho_b", "a", "n", "gamma", "R", "T1", "P1_min","P1_max",
            "delta_r", "P0"
        ]
        
        for attr, value in zip(attributes, inputs):
            setattr(self, attr, value)
   
        self.P, self.G, self.M, self.t = self.combTime()
        self.meanPressure, self.meanMassFlow = self.mean_values()
        self.Pmin, self.Pmax = np.min(self.P[1:-1]), np.max(self.P[1:-1])
        self.Gmin, self.Gmax = np.min(self.G[1:-1]), np.max(self.G[1:-1])
        self.combustion_time = float(self.t[-1])
        self.combustion_mass = float(self.M[0])


    def combTime(self):

        C = (((np.pi * self.rThrt**2 * self.gamma) / (self.rho_b * self.a * 1e-2)))
        R = np.sqrt( (2/(self.gamma + 1))**((self.gamma - 1)/(self.gamma + 1)) / (self.gamma * self.R * self.T1) )

        rt = np.arange(self.rIn_0b, self.rOut + self.delta_r, self.delta_r)
        size = len(rt)

        P  = np.zeros(size)
        G  = np.zeros(size)
        dt = np.zeros(size)
        m  = np.zeros(size)


        def Ab(ti):
            return 2 * np.pi * self.lComb * rt[ti]

        def M(ti):
            return np.pi * self.rho_b * self.lComb * (self.rOut**2 - rt[ti]**2)

        P[0] = self.P0
        G[0] = Ab(0) * self.rho_b * self.a * P[0]**self.n * 1e-2
        dt[0] = (M(0) - M(1)) / G[0]
        m[0] = M(0)

        def iterCalc(ti):
            P_i = ((C / Ab(ti)) * R)**(1/(self.n - 1))
            G_i = Ab(ti) * self.rho_b * self.a * P_i**self.n * 1e-2
            m_i = M(ti)
            dt_i = (M(ti - 1) - M(ti)) / G_i
            return P_i, G_i, m_i ,dt_i

        for i in range(1, size-1):
            P[i], G[i], m[i], dt[i] = iterCalc(i)

            if P[i] > self.P1_max or P[i] < self.P1_min:
                return messagebox.showerror("Out of range","Error PMax - Valor de presion fuera del rango de operacion del propelente")

        P[-1], G[-1], m[-1] = self.P0, 0, 0

        return P, G, m, np.cumsum(dt)
    
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
    

