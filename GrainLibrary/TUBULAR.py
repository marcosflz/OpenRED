from imports import *
from functions import *


class Tubular:
    nozzle_type = "Tubular-Grain"

    @staticmethod
    def get_input_labels():
        return {
            "X  (m)": "cx_real",
            "Y  (m)": "cy_real",
            "R1 (m)": "r_in",
        }
    
    def __init__(self, specInputs, r_out, dh):

        self.cx_real = specInputs["cx_real"] * 1e3
        self.cy_real = specInputs["cy_real"] * 1e3
        self.r_in = specInputs["r_in"] * 1e3


        self.r_out = r_out * 1e3
        self.x_limits = (-self.r_out - 0.1 * self.r_out, self.r_out + 0.1 * self.r_out)
        self.y_limits = self.x_limits

        self.dh = dh * 1e3

    def getPhi(self):
        """ Inicializa la función level set como una circunferencia con centro y radio dados. """
        # Crear el meshgrid basado en los límites espaciales y la resolución h
        x = np.linspace(self.x_limits[0], self.x_limits[1], int((self.x_limits[1] - self.x_limits[0]) / self.dh) + 1)
        y = np.linspace(self.y_limits[0], self.y_limits[1], int((self.y_limits[1] - self.y_limits[0]) / self.dh) + 1)
        X, Y = np.meshgrid(x, y)

        # Calcular la distancia desde el centro (cx_real, cy_real) a cada punto en el grid
        r = np.sqrt((X - self.cx_real)**2 + (Y - self.cy_real)**2)
            
        # Phi será negativo dentro del círculo y positivo fuera
        phi = r - self.r_in

        return phi, X, Y
    
    def plotGeometry(self):
        fig, ax = plt.subplots()
        ax.set_title('Método Level Set - Evolución de la Interfaz')
        ax.set_aspect('equal')
        ax.set_xlim(self.x_limits)
        ax.set_ylim(self.y_limits)

        circle_outer = Circle((0.0, 0.0), self.r_out, edgecolor='black', facecolor='lightgray', lw=4)
        ax.add_patch(circle_outer)

        circle_inner = Circle((self.cx_real, self.cy_real), self.r_in, edgecolor='black', facecolor='white', lw=4)
        ax.add_patch(circle_inner)
        return fig
    
    def sketchCAD(self, Lc):

        center_propHole = (self.cx_real, self.cy_real)
        r_propHole = self.r_in
        r_propOut = self.r_out

        xPropIn, yPropIn = self.get_circle_points(r_propHole, center=center_propHole, num_points=100) * 1e-3
        xPropOut, yPropOut = self.get_circle_points(r_propHole, center=center_propHole, num_points=100) * 1e-3

        

   
    def get_circle_points(self, r, center=(0, 0), num_points=100):
        # Crear un vector de ángulos
        t = np.linspace(0, 2 * np.pi, num_points)
        # Parametrizar el círculo y añadir el desplazamiento del centro
        x = center[0] + r * np.cos(t)  # x del círculo
        y = center[1] + r * np.sin(t)  # y del círculo
        return x, y
