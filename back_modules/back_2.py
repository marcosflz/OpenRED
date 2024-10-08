from imports import *
from functions import *


class EngineCADBuilder_ConventionalNozzle:
    def __init__(self, nozzle):
        self.nozzleData = get_data(type='Nozzles', file=nozzle)
        self.engineUsed = self.nozzleData["Inputs"]["EngineConfig"]
        self.nozzle_arch = self.nozzleData["Inputs"]["NozzleConfig"]

        self.engineData = get_data(type='Engines', file=self.engineUsed)

        self.LNozz = self.nozzleData["calculatedResults"]["Longitud (m)"]

        self.nozzle_X = np.array(self.nozzleData["geometry_data"]["X (m)"])
        self.nozzle_Y = np.array(self.nozzleData["geometry_data"]["Y (m)"])

        self.propellant_X = np.array(self.engineData["inputs"]["CADx"])
        self.propellant_Y = np.array(self.engineData["inputs"]["CADy"])
        self.propellant_O = np.array(self.engineData["inputs"]["CAD0"])

        self.rThroat = self.nozzleData["calculatedResults"]["Rt (m)"]
        self.rExit = self.nozzleData["calculatedResults"]["R2 (m)"]

        distances = np.sqrt((self.propellant_X - self.propellant_O[0])**2 + (self.propellant_Y - self.propellant_O[1])**2)
        self.equivalent_r = np.max(distances)

    
    







    # Funciones de geometría

    def create_arc(self, x_center, y_center, theta_1, theta_2 ,radius, num_points=100, turn=1):
        angles = np.linspace(theta_1, theta_2, num_points)
        x_arc = x_center + radius * np.cos(angles) * turn
        y_arc = y_center + radius * np.sin(angles)
        return x_arc, y_arc
    
    def remove_duplicate_points(self, x, y):
        points = np.vstack((x, y)).T
        unique_points = np.unique(points, axis=0)
        return unique_points[:, 0], unique_points[:, 1]
    
    def convergent_throat(self, user_settings, offset=0):
        K1 = user_settings['KIn']
        Rt = self.rThroat
        alpha = user_settings["alpha"] * np.pi / 2
        th = np.linspace(-np.pi / 2, -np.pi / 2 - alpha, int(user_settings["n_conv"]))
        x = K1 * Rt * np.cos(th)
        y = K1 * Rt * np.sin(th) + K1 * Rt + Rt + offset
        return x, y
    
    def convergent_cone(self, user_settings, x0, y0):
        RCartucho = self.engineData["inputs"]["R2"] + user_settings["t_cartridge"]
        alpha = user_settings["alpha"] * np.pi / 2
        dx = (RCartucho - y0) / np.tan(alpha)
        dx_p = user_settings["t_cartridge"] / np.tan(alpha)
        x = x0 - dx + dx_p
        y = self.engineData["inputs"]["R2"]
        return x, y 

    def find_tangent_points(self, Px, Py, r):
        # Definir las variables
        x, y = sp.symbols('x y')
        d = np.sqrt(Px**2 + Py**2)
        
        # Definir las ecuaciones de las circunferencias
        aux_circ1 = (x - Px)**2 + (y - Py)**2 - d**2
        aux_circ2 = x**2 + y**2 - d**2
        
        # Resolver el sistema de ecuaciones
        aux_intersecs = sp.solve([aux_circ1, aux_circ2], (x, y))
        if not aux_intersecs:
            raise ValueError("No se encontraron puntos de intersección.")
        
        x1, y1 = aux_intersecs[0]
        x2, y2 = aux_intersecs[1]
        
        # Encontrar la pendiente de la recta tangente
        m = (y1 - y2) / (x1 - x2)
        # Ecuación de la recta tangente en forma punto-pendiente
        n = y1 - m * x1
        f = m * x + n - y
        
        # Definir la circunferencia final con centro en (Px/2, Py/2) y radio d/2
        finalCirc = (x - Px/2)**2 + (y - Py/2)**2 - (d/2)**2
        rocketCirc = x**2 + y**2 - r**2
        # Resolver para encontrar los puntos tangentes
        tan_intersecs = sp.solve([rocketCirc, finalCirc], (x, y))
        if not tan_intersecs:
            raise ValueError("No se encontraron puntos tangentes.")
        
        tan_point = max(tan_intersecs, key=lambda par: par[0])
        
        return float(tan_point[0]), float(tan_point[1])
    



    def get_sketch(self, user_settings, sketch='Engine'):

        xNozzle, yNozzle = np.flip(self.nozzle_X), np.flip(self.nozzle_Y)
        xConvThr, yConvThr = self.convergent_throat(user_settings)
        xConvCon, yConvCon = self.convergent_cone(user_settings, xConvThr[-1], yConvThr[-1])
        
        xCase = [xConvCon, -self.engineData["inputs"]["Lc"] + xConvCon]
        yCase = [yConvCon + user_settings["t_cartridge"], yConvCon + user_settings["t_cartridge"]]

        self.nozzInPos = xConvCon
        self.coverInPos = -self.engineData["inputs"]["Lc"] + xConvCon

        xWallPoints = [
            -self.engineData["inputs"]["Lc"] + xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon + user_settings["bolt_OffSet"],
            -self.engineData["inputs"]["Lc"] + xConvCon + user_settings["bolt_OffSet"],
            xConvCon
        ]
        
        yWallPoints = [
            yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"] * user_settings["hBoltFactor"],
            yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"] * user_settings["hBoltFactor"],
            yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"],
            yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"]
        ]

        if user_settings["type"] == 'Fitted':
            xNozzleWall = np.concatenate((
                np.flip(xConvThr), 
                np.flip(xNozzle), 
                [xNozzle[0]]
            ))

            yNozzleWall = np.concatenate((
                np.flip(yConvThr) + user_settings["wall_t"], 
                np.flip(yNozzle) + user_settings["wall_t"], 
                [yNozzle[0]]
            ))

        else:
            xNozzleWall = np.concatenate((
                [np.flip(xNozzle)[-1]], 
                [xNozzle[0]]
            ))

            yNozzleWall = np.concatenate((
                [np.flip(yNozzle)[-1] + user_settings["wall_t"]], 
                [yNozzle[0]]
            ))

        xEngine = np.concatenate((xNozzle, xConvThr, [xConvCon], xCase, xWallPoints, xNozzleWall))
        yEngine = np.concatenate((yNozzle, yConvThr, [yConvCon], yCase, yWallPoints, yNozzleWall))

        xCover = np.array([
            -self.engineData["inputs"]["Lc"] + xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon + user_settings["bolt_OffSet"],
            -self.engineData["inputs"]["Lc"] + xConvCon + user_settings["bolt_OffSet"],
            -self.engineData["inputs"]["Lc"] + xConvCon - user_settings["cover_t"],
            -self.engineData["inputs"]["Lc"] + xConvCon - user_settings["cover_t"],
            -self.engineData["inputs"]["Lc"] + xConvCon + user_settings["bolt_OffSet"],
            -self.engineData["inputs"]["Lc"] + xConvCon + user_settings["bolt_OffSet"],
            -self.engineData["inputs"]["Lc"] + xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon
        ])

        yCover = np.array([
            0,
            yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"] * user_settings["hBoltFactor"],
            yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"] * user_settings["hBoltFactor"],
            yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"],
            yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"],
            -(yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"]),
            -(yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"]),
            -(yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"] * user_settings["hBoltFactor"]),
            -(yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"] * user_settings["hBoltFactor"]),
            0
        ])

        xProp = np.array([
            xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon,
            xConvCon,
            xConvCon
        ])

        yProp = np.array([
            yConvCon,
            yConvCon,
            -yConvCon,
            -yConvCon,
            yConvCon
        ])

        

        xCart = np.array([
            xConvCon, 
            xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon,
            xConvCon
        ])

        yCart = np.array([
            yConvCon,
            yConvCon + user_settings["t_cartridge"],
            yConvCon + user_settings["t_cartridge"],
            yConvCon,
            yConvCon
        ])


        R_outter = yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"]
        R_bolt = yConvCon + user_settings["t_cartridge"] + user_settings["wall_t"] * user_settings["hBoltFactor"]
        R_inCase = yConvCon + user_settings["t_cartridge"]
        R_Cart = yConvCon

        
        R_nOut = self.rExit + user_settings["wall_t"]
        R_nIn = self.rExit
        R_nThr = self.rThroat


        xCoverMould = np.array([
            -self.engineData["inputs"]["Lc"] + xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon,
            (-self.engineData["inputs"]["Lc"] + xConvCon) + user_settings["t_cartridge"] + user_settings["cover_len"],
            (-self.engineData["inputs"]["Lc"] + xConvCon) + user_settings["t_cartridge"] + user_settings["cover_len"],
            (-self.engineData["inputs"]["Lc"] + xConvCon) - user_settings["t_cartridge"] * user_settings["t_factor"],
            (-self.engineData["inputs"]["Lc"] + xConvCon) - user_settings["t_cartridge"] * user_settings["t_factor"],
            (-self.engineData["inputs"]["Lc"] + xConvCon) + user_settings["t_cartridge"] + user_settings["cover_len"],
            (-self.engineData["inputs"]["Lc"] + xConvCon) + user_settings["t_cartridge"] + user_settings["cover_len"],
            -self.engineData["inputs"]["Lc"] + xConvCon
        ])

        yCoverMould = np.array([
            -(yConvCon + user_settings["t_cartridge"]),
            (yConvCon + user_settings["t_cartridge"]),
            (yConvCon + user_settings["t_cartridge"]),
            yConvCon +  user_settings["t_cartridge"] * (1 + user_settings["t_factor"]),
            yConvCon +  user_settings["t_cartridge"] * (1 + user_settings["t_factor"]),
            -(yConvCon + user_settings["t_cartridge"] * (1 + user_settings["t_factor"])),
            -(yConvCon + user_settings["t_cartridge"] * (1 + user_settings["t_factor"])),
            -(yConvCon + user_settings["t_cartridge"]),
            -(yConvCon + user_settings["t_cartridge"]),
        ])

        xCoverMould_Fix = np.array([
            xConvCon,
            xConvCon,
            (xConvCon) - user_settings["t_cartridge"] - user_settings["cover_len"],
            (xConvCon) - user_settings["t_cartridge"] - user_settings["cover_len"],
            (xConvCon) + user_settings["t_cartridge"] * user_settings["t_factor"],
            (xConvCon) + user_settings["t_cartridge"] * user_settings["t_factor"],
            (xConvCon) - user_settings["t_cartridge"] - user_settings["cover_len"],
            (xConvCon) - user_settings["t_cartridge"] - user_settings["cover_len"],
            xConvCon
        ])

        yCoverMould_Fix = np.array([
            -(yConvCon + user_settings["t_cartridge"]),
            (yConvCon + user_settings["t_cartridge"]),
            (yConvCon + user_settings["t_cartridge"]),
            yConvCon +  user_settings["t_cartridge"] * (1 + user_settings["t_factor"]),
            yConvCon +  user_settings["t_cartridge"] * (1 + user_settings["t_factor"]),
            -(yConvCon + user_settings["t_cartridge"] * (1 + user_settings["t_factor"])),
            -(yConvCon + user_settings["t_cartridge"] * (1 + user_settings["t_factor"])),
            -(yConvCon + user_settings["t_cartridge"]),
            -(yConvCon + user_settings["t_cartridge"]),
        ])

        xMould = np.array([
            -self.engineData["inputs"]["Lc"] + xConvCon,
            xConvCon,
            xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon,
            -self.engineData["inputs"]["Lc"] + xConvCon,
        ])


        yMould = np.array([
            self.propellant_O[1] + self.equivalent_r,
            self.propellant_O[1] + self.equivalent_r,
            self.propellant_O[1] - self.equivalent_r,
            self.propellant_O[1] - self.equivalent_r,
            self.propellant_O[1] + self.equivalent_r
        ])

        xExtraMould = np.array([
            xConvCon,
            xConvCon + user_settings["extra_len"],
            xConvCon + user_settings["extra_len"],
            xConvCon,
            xConvCon,
        ])

        yExtraMould = np.array([
            self.propellant_O[1] + self.equivalent_r,
            self.propellant_O[1] + self.equivalent_r,
            self.propellant_O[1] - self.equivalent_r,
            self.propellant_O[1] - self.equivalent_r,
            self.propellant_O[1] + self.equivalent_r
        ])

        xNut = np.array([
            (xConvCon) + user_settings["t_cartridge"] * user_settings["t_factor"],
            (xConvCon) + user_settings["t_cartridge"] * user_settings["t_factor"],
            (xConvCon) + user_settings["t_cartridge"] * user_settings["t_factor"] + user_settings["nut_h"],
            (xConvCon) + user_settings["t_cartridge"] * user_settings["t_factor"] + user_settings["nut_h"],
            (xConvCon) + user_settings["t_cartridge"] * user_settings["t_factor"],
        ])

        yNut_up = np.array([
            self.propellant_O[1] + self.equivalent_r,
            self.propellant_O[1] + self.equivalent_r + user_settings["nut_dr"],
            self.propellant_O[1] + self.equivalent_r + user_settings["nut_dr"],
            self.propellant_O[1] + self.equivalent_r,
            self.propellant_O[1] + self.equivalent_r,
        ])

        yNut_down = np.array([
            self.propellant_O[1] - self.equivalent_r - user_settings["nut_dr"],
            self.propellant_O[1] - self.equivalent_r,
            self.propellant_O[1] - self.equivalent_r,
            self.propellant_O[1] - self.equivalent_r - user_settings["nut_dr"],
            self.propellant_O[1] - self.equivalent_r - user_settings["nut_dr"],
        ])


        if sketch == 'Engine':
            x = xEngine
            y = yEngine
            data = x, y

        if sketch == 'Cover':
            x = xCover
            y = yCover
            data = x, y

        if sketch == 'Cartridge':
            x = xCart
            y = yCart
            data = x, y

        if sketch == 'Propellant':
            x = xProp
            y = yProp
            data = x, y

        if sketch == 'CoverFront':
            data = R_outter, R_bolt, R_inCase, R_Cart 

        if sketch == 'NozzleFront':
            data = R_outter, R_nOut, R_nIn, R_nThr

        if sketch == 'MouldCover':
            x = xCoverMould
            y = yCoverMould
            data = x, y

        if sketch == 'MouldCoverFix':
            x = xCoverMould_Fix
            y = yCoverMould_Fix
            data = x, y
        
        if sketch == 'Mould':
            x = xMould
            y = yMould
            data = x, y

        if sketch == 'ExtraMould':
            x = xExtraMould
            y = yExtraMould
            data = x, y

        if sketch == 'NutUp':
            x = xNut
            y = yNut_up
            data = x, y

        if sketch == 'NutDown':
            x = xNut
            y = yNut_down
            data = x, y

        return data
    

    def plot_Engine(self, user_settings):
        fig, ax = plt.subplots(figsize=(10, 5))

        # Obtener las curvas
        if user_settings["on_Engine"]:
            xEng, yEng = self.get_sketch(user_settings, sketch='Engine')
            ax.fill(xEng, yEng, color='lightgray', alpha=1, edgecolor='black', lw=2, hatch='//')
            ax.fill(xEng, -yEng, color='lightgray', alpha=1, edgecolor='black', lw=2, hatch='//')

        if user_settings["on_Cover"]:
            xCov, yCov = self.get_sketch(user_settings, sketch='Cover')
            ax.fill(xCov, yCov, color='lightgray', alpha=1, edgecolor='black', lw=2, hatch='//')

        if user_settings["on_Cartridge"]:
            xCart, yCart = self.get_sketch(user_settings, sketch='Cartridge')
            ax.fill(xCart, yCart, color='grey', alpha=1, edgecolor='black', lw=2, hatch='//')
            ax.fill(xCart, -yCart, color='grey', alpha=1, edgecolor='black', lw=2, hatch='//')

#        if user_settings["on_Background"]:
#            xBack, yBack = self.get_sketch(user_settings, sketch='Propellant')
#            ax.fill(xBack, yBack, color='gray', alpha=0.75, edgecolor='black', lw=2)
   
        if user_settings["on_Propellant"]:
            xProp, yProp = self.get_sketch(user_settings, sketch='Propellant')
            ax.fill(xProp, yProp, color='red', alpha=0.75, edgecolor='black', lw=2)
        



        # Personalizar la gráfica
        ax.set_title("Engine Plot")
        ax.set_xlabel("X Axis")
        ax.set_ylabel("Y Axis")

        # Mejorar la apariencia general
        ax.set_aspect('equal')  # Asegurar que la relación de aspecto sea igual

        return fig

    def plot_CoverFront(self, user_settings):
        # Crear una nueva figura y ejes
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Obtener los radios para los diferentes círculos
        R_outter, R_bolt, R_inCase, R_Cart  = self.get_sketch(user_settings, sketch='CoverFront')
        
        # Dibujar los círculos exteriores y el interior
        outter_circle = Circle((0, 0), R_outter, edgecolor='k', facecolor='lightgray', fill=True, linewidth=2, hatch='//')
        bolt_circle = Circle((0, 0), R_bolt, edgecolor='k', linestyle='--', fill=False, linewidth=2, hatch='//')
        case_circle = Circle((0, 0), R_inCase, edgecolor='k', facecolor='grey', fill=True, linewidth=2, hatch='//')

        if user_settings["on_Propellant"]:
            cart_circle = Circle((0, 0), R_Cart, edgecolor='k', facecolor='red', alpha=0.75, fill=True, linewidth=2, hatch='//')
            ax.fill(self.propellant_X, self.propellant_Y, color='lightgray', zorder=20)  # Rellenar de blanco
            ax.plot(self.propellant_X, self.propellant_Y, color='black', linewidth=2, zorder=25)
            

        else:
            cart_circle = Circle((0, 0), R_Cart, edgecolor='k', facecolor='lightgrey', fill=True, linewidth=2)

        Ox = self.propellant_O[0]
        Oy_up = self.propellant_O[1] + user_settings["dy_elect"] / 2
        Oy_do = self.propellant_O[1] - user_settings["dy_elect"] / 2
        elect_up = Circle((Ox, Oy_up), user_settings["d_elect"] / 2, edgecolor='k', facecolor='white', fill=True, linewidth=2, zorder=30)
        elect_do = Circle((Ox, Oy_do), user_settings["d_elect"] / 2, edgecolor='k', facecolor='white', fill=True, linewidth=2, zorder=30)
        
        # Añadir los círculos a los ejes
        ax.add_patch(outter_circle)
        ax.add_patch(bolt_circle)
        ax.add_patch(case_circle)
        ax.add_patch(cart_circle)
        ax.add_patch(elect_up)
        ax.add_patch(elect_do)
        
        # Calcular el margen en porcentaje
        margin_percent = 0.10  # 10% de margen
        max_radius = R_outter  # Radio máximo que queremos visualizar
            
            # Calcular el margen
        margin = margin_percent * max_radius
            
        # Ajustes del gráfico con márgenes
        ax.set_xlim(-max_radius - margin, max_radius + margin)
        ax.set_ylim(-max_radius - margin, max_radius + margin)
        ax.set_aspect('equal', 'box')  # Mantener la relación de aspecto
        
        # Etiquetas y leyenda
        ax.set_title("Cover Front Sketch")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        return fig
        

    def plot_NozzleFront(self, user_settings):
        # Crear una nueva figura y ejes
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Obtener los radios para los diferentes círculos
        R_out, R_nOut, R_nIn, R_nThr = self.get_sketch(user_settings, sketch='NozzleFront')
        

        circle_ext = Circle((0, 0), R_out, edgecolor='k', facecolor='lightgray', fill=True, linewidth=2)
        circle_in = Circle((0, 0), R_nOut, edgecolor='k', facecolor='lightgray', fill=True, linewidth=2)
        
        # Dibujar los electrodos en la parte superior e inferior
        nozzle1 = Circle((0, 0), R_nIn, edgecolor='k', facecolor='darkgrey', fill=True, linewidth=2)
        nozzle2 = Circle((0, 0), R_nThr, edgecolor='k', facecolor='white', fill=True, linewidth=2)
        
        # Añadir los círculos a los ejes
        ax.add_patch(circle_ext)
        ax.add_patch(circle_in)
        ax.add_patch(nozzle1)
        ax.add_patch(nozzle2)


        # Calcular el margen en porcentaje
        margin_percent = 0.10  # 10% de margen
        max_radius = R_out  # Radio máximo que queremos visualizar
            
            # Calcular el margen
        margin = margin_percent * max_radius
            
        # Ajustes del gráfico con márgenes
        ax.set_xlim(-max_radius - margin, max_radius + margin)
        ax.set_ylim(-max_radius - margin, max_radius + margin)
        ax.set_aspect('equal', 'box')  # Mantener la relación de aspecto
        
        # Etiquetas y leyenda
        ax.set_title("Cover Front Sketch")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        return fig

    def plot_Tools(self, user_settings):
        fig, ax = plt.subplots(figsize=(10, 5))

        if user_settings["on_Cartridge"]:
            xCart, yCart = self.get_sketch(user_settings, sketch='Cartridge')
            ax.fill(xCart, yCart, color='grey', alpha=1, edgecolor='black', lw=2, hatch='//')
            ax.fill(xCart, -yCart, color='grey', alpha=1, edgecolor='black', lw=2, hatch='//')

        if user_settings["on_CoverCast1"]:
            xCoverMould, yCoverMould = self.get_sketch(user_settings, sketch='MouldCover')
            ax.fill(xCoverMould, yCoverMould, color='lightgray', alpha=1, edgecolor='black', lw=2, hatch='//')

        if user_settings["on_CoverCast2"]:
            xCoverMould_Fix, yCoverMould_Fix = self.get_sketch(user_settings, sketch='MouldCoverFix')
            ax.fill(xCoverMould_Fix, yCoverMould_Fix, color='lightgray', alpha=1, edgecolor='black', lw=2, hatch='//')

        if user_settings["on_Mould"]:
            xMould, yMould = self.get_sketch(user_settings, sketch='Mould')
            ax.fill(xMould, yMould, color='lightgray', alpha=1, edgecolor='black', lw=2)

        if user_settings["on_CastBolt"]:
            xExtraMould, yExtraMould = self.get_sketch(user_settings, sketch='ExtraMould')
            ax.fill(xExtraMould, yExtraMould, color='lightgray', alpha=1, edgecolor='black', lw=2, hatch='||')

        if user_settings["on_CastNut"]:
            xNut_up, yNut_up = self.get_sketch(user_settings, sketch='NutUp')
            ax.fill(xNut_up, yNut_up, color='lightgray', alpha=1, edgecolor='black', lw=2, hatch='//')

            xNut_down, yNut_down = self.get_sketch(user_settings, sketch='NutDown')
            ax.fill(xNut_down, yNut_down, color='lightgray', alpha=1, edgecolor='black', lw=2, hatch='//')

        # Personalizar la gráfica
        ax.set_title("Engine Plot")
        ax.set_xlabel("X Axis")
        ax.set_ylabel("Y Axis")

        # Mejorar la apariencia general
        ax.set_aspect('equal')  # Asegurar que la relación de aspecto sea igual


        return fig

    def plot_ToolMould(self, user_settings):
        fig, ax = plt.subplots(figsize=(5, 5))
        xCoverMould, yCoverMould = self.get_sketch(user_settings, sketch='MouldCover')
        rMax = np.max(np.abs(yCoverMould))
        rMin = np.min(np.abs(yCoverMould))

        if user_settings["on_CoverCast1"]:
            cover_circle_ext = Circle((0, 0), rMax, edgecolor='k', facecolor='lightgray', fill=True, linewidth=2)
            cover_circle_int = Circle((0, 0), rMin, edgecolor='k', fill=False, linestyle='--', linewidth=2)
            ax.add_patch(cover_circle_ext)
            ax.add_patch(cover_circle_int)

        if user_settings["on_Cartridge"]:
            xCart, yCart = self.get_sketch(user_settings, sketch='Cartridge')
            rCart_ext = np.max(np.abs(yCart))
            rCart_int = np.min(np.abs(yCart)) 
            cart_circle_ext = Circle((0, 0), rCart_ext, edgecolor='k', facecolor='darkgrey', fill=True, linewidth=2)
            cart_circle_int = Circle((0, 0), rCart_int, edgecolor='k', facecolor='lightgray', fill=True, linewidth=2)
            ax.add_patch(cart_circle_ext)
            ax.add_patch(cart_circle_int)

        if user_settings["on_Mould"]:
            ax.fill(self.propellant_X, self.propellant_Y, color='lightgray', zorder=20)  # Rellenar de blanco
            ax.plot(self.propellant_X, self.propellant_Y, color='black', linewidth=2, zorder=25)




        # Calcular el margen en porcentaje
        margin_percent = 0.10  # 10% de margen
        max_radius = rMax  # Radio máximo que queremos visualizar
            
        # Calcular el margen
        margin = margin_percent * max_radius

        ax.set_xlim(-max_radius - margin, max_radius + margin)
        ax.set_ylim(-max_radius - margin, max_radius + margin)
        ax.set_aspect('equal', 'box')  # Mantener la relación de aspecto
        
        # Etiquetas y leyenda
        ax.set_title("Cover Front Sketch")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        return fig

    def plot_ToolMouldFix(self, user_settings):
        fig, ax = plt.subplots(figsize=(5, 5))
        xCoverMould, yCoverMould = self.get_sketch(user_settings, sketch='MouldCover')
        rMax = np.max(np.abs(yCoverMould))

        if user_settings["on_CoverCast2"]:
            cover_circle_ext = Circle((0, 0), rMax, edgecolor='k', facecolor='lightgray', fill=True, linewidth=2)

            xCart, yCart = self.get_sketch(user_settings, sketch='Cartridge')
            rCart_ext = np.max(np.abs(yCart))
            rCart_int = np.min(np.abs(yCart)) 
            cart_circle_ext = Circle((0, 0), rCart_ext, edgecolor='k', linestyle='--', fill=False, linewidth=2)
            cart_circle_int = Circle((0, 0), rCart_int, edgecolor='k', linestyle='--', fill=False, linewidth=2)
            ax.add_patch(cover_circle_ext)
            ax.add_patch(cart_circle_ext)
            ax.add_patch(cart_circle_int)

        if user_settings["on_CastNut"]:
            rNutExt =  self.equivalent_r + user_settings["nut_dr"]
            rNutInt =  self.equivalent_r 
            nut_ext = Circle((self.propellant_O[0], self.propellant_O[1]), rNutExt, edgecolor='k', facecolor='lightgray', fill=True, linewidth=2)
            nut_int = Circle((self.propellant_O[0], self.propellant_O[1]), rNutInt, edgecolor='k', facecolor='white', fill=True, linewidth=2)
            ax.add_patch(nut_ext)
            ax.add_patch(nut_int)
        else:
            rNutInt =  self.equivalent_r 
            nut_int = Circle((self.propellant_O[0], self.propellant_O[1]), rNutInt, edgecolor='k', facecolor='white', fill=True, linewidth=2)
            ax.add_patch(nut_int)

        

        # Calcular el margen en porcentaje
        margin_percent = 0.10  # 10% de margen
        max_radius = rMax  # Radio máximo que queremos visualizar
                
        # Calcular el margen
        margin = margin_percent * max_radius

        ax.set_xlim(-max_radius - margin, max_radius + margin)
        ax.set_ylim(-max_radius - margin, max_radius + margin)
        ax.set_aspect('equal', 'box')  # Mantener la relación de aspecto
            
        # Etiquetas y leyenda
        ax.set_title("Cover Front Sketch")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")

        return fig



    def export_engine(self, user_settings, file_path):
        x, y = self.get_sketch(user_settings, sketch='Engine')
        z = np.zeros(len(x))

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Sketch', 'Plane', 'x', 'y', 'z'])

            for i in range(len(x)):
                writer.writerow([0, 'XY' ,x[i] * 100, y[i] * 100, z[i] * 100])

    def export_cover(self, user_settings, file_path):
        x0, y0 = self.get_sketch(user_settings, sketch='Cover')
        z0 = np.zeros(len(x0))

        Ox = self.propellant_O[0]
        Oy_up = self.propellant_O[1] + user_settings["dy_elect"] / 2
        Oy_do = self.propellant_O[1] - user_settings["dy_elect"] / 2

        y1, z1 = get_circle_points(user_settings["d_elect"] / 2, (Ox, Oy_up))
        x1 = np.full(len(y1), self.coverInPos)

        y2, z2 = get_circle_points(user_settings["d_elect"] / 2, (Ox, Oy_do))
        x2 = np.full(len(y2), self.coverInPos)

        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Sketch', 'Plane', 'x', 'y', 'z'])

            for i in range(len(x0)):
                writer.writerow([0, 'XY' ,x0[i] * 100, y0[i] * 100, z0[i] * 100])
            for i in range(len(x1)):
                writer.writerow([1, 'YZ' ,x1[i] * 100, y1[i] * 100, z1[i] * 100])
            for i in range(len(x2)):
                writer.writerow([2, 'YZ' ,x2[i] * 100, y2[i] * 100, z2[i] * 100])

    def export_tools(self, user_settings, file_path):

        #Cubierta 
        x0, y0 = self.get_sketch(user_settings, sketch='MouldCover')
        z0 = np.zeros(len(x0))

        #Cubierta con tuerca
        x1, y1 = self.get_sketch(user_settings, sketch='MouldCoverFix')
        z1 = np.zeros(len(x0))

        #Sketch molde 
        y2, z2 = self.propellant_X, self.propellant_Y 
        x2 = np.full(len(y2), self.coverInPos)

        #Sketch circulo rosca
        y3, z3 = get_circle_points(self.equivalent_r, (self.propellant_O[0], self.propellant_O[1]))
        x3 = np.full(len(y3), self.nozzInPos)

        #Eje de molde
        x4 = np.array([self.coverInPos, self.nozzInPos])
        y4 = np.full(2, self.propellant_O[0])
        z4 = np.full(2, self.propellant_O[1])

        #Eje de tornillo
        x5 = np.array([self.nozzInPos, self.nozzInPos + user_settings["extra_len"]])
        y5 = np.full(2, self.propellant_O[0])
        z5 = np.full(2, self.propellant_O[1])

        #Tuerca
        x6, y6 = self.get_sketch(user_settings, sketch='NutUp')
        z6 = np.zeros(len(x6))

        x7, y7 = self.get_sketch(user_settings, sketch='NutDown')
        z7 = np.zeros(len(x7))




        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Sketch', 'Plane', 'x', 'y', 'z'])

            for i in range(len(x0)):
                writer.writerow([0, 'XY' , x0[i] * 100, y0[i] * 100, z0[i] * 100])
            for i in range(len(x1)):
                writer.writerow([1, 'XY' , x1[i] * 100, y1[i] * 100, z1[i] * 100])
            for i in range(len(x2)):
                writer.writerow([2, 'YZ' , x2[i] * 100, y2[i] * 100, z2[i] * 100])
            for i in range(len(x3)):
                writer.writerow([3, 'YZ' , x3[i] * 100, y3[i] * 100, z3[i] * 100])
            for i in range(len(x4)):
                writer.writerow([4, 'XY' , x4[i] * 100, y4[i] * 100, z4[i] * 100])
            for i in range(len(x5)):
                writer.writerow([5, 'XY' , x5[i] * 100, y5[i] * 100, z5[i] * 100])
            for i in range(len(x6)):
                writer.writerow([6, 'XY' , x6[i] * 100, y6[i] * 100, z6[i] * 100])
            for i in range(len(x7)):
                writer.writerow([7, 'XY' , x7[i] * 100, y7[i] * 100, z7[i] * 100])




#    # Funciones de Sketch de Motor
#
#    def sketchEngine(self, user_settings):
#        nozzle_x_in, nozzle_y_in = np.flip(self.nozzle_X), np.flip(self.nozzle_Y)
#        nozzle_x_wall, nozzle_y_wall = np.flip(self.nozzle_X), np.flip(self.nozzle_Y) + user_settings["wall_t"]
#
#        convergent_x, convergent_y = self.convergent_throat(user_settings)
#        convergent_x_wall, convergent_y_wall = self.convergent_throat(user_settings, user_settings["wall_t"])
#
#        self.x1, self.y1 = nozzle_x_in[0], nozzle_y_in[0]
#        self.x2, self.y2 = nozzle_x_in[-1], nozzle_y_in[-1]
#        self.x3, self.y3 = convergent_x[-1], convergent_y[-1]
#        self.x4, self.y4 = self.convergent_cone(user_settings)
#        self.x5, self.y5 = self.x4, self.y4 + user_settings["t_cartridge"]
#        self.x6, self.y6 = self.x5 - self.LComb, self.y5
#        self.x7, self.y7 = self.x6, self.y6 + user_settings["wall_t"] * user_settings["hBoltFactor"]
#        self.x8, self.y8 = self.x7 + user_settings["bolt_OffSet"], self.y7
#        self.x9, self.y9 = self.x8, self.y6 + user_settings["wall_t"]
#        self.x10, self.y10 = self.x5, self.y9
#        self.x11, self.y11 = self.x3, self.y3 + user_settings["wall_t"]
#        self.x12, self.y12 = self.x2, self.y2 + user_settings["wall_t"]
#        self.x13, self.y13 = self.x1, self.y1 + user_settings["wall_t"]
#        
#        self.radi = user_settings["t_cartridge"]/2
#        ring_arc_x, ring_arc_y = self.create_arc(self.x4, self.y4 + self.radi, -np.pi/2, np.pi/2 ,self.radi)
#
#        self.x1c, self.y1c = self.x6, user_settings["r_elect"] + user_settings["d_elect"]/2
#        self.x2c, self.y2c = self.x1c, self.y7
#        self.x3c, self.y3c = self.x8, self.y8
#        self.x4c, self.y4c = self.x9, self.y9
#        self.x5c, self.y5c = self.x6 - user_settings["cover_t"], self.y9
#        self.x6c, self.y6c = self.x5c, self.y1c
#
#        self.x0c, self.y0c = self.x1c, self.y4 + self.radi
#        self.x01c, self.y01c = self.x1c, self.y4
#        self.x02c, self.y02c = self.x1c, self.y5
#
#        fullTHeight = self.y10 + user_settings["upper_offset"] + user_settings["lower_offset"] + user_settings["T_height"]
#        medTHeight = self.y10 + user_settings["lower_offset"] + user_settings["T_height"]
#        lowTHeight = self.y10 + user_settings["lower_offset"]
#
#        self.x1m, self.y1m = user_settings["T_Re"], fullTHeight
#        self.x2m, self.y2m = user_settings["T_Ri"], fullTHeight
#        self.x3m, self.y3m = user_settings["T_Ri"], medTHeight
#        self.x4m, self.y4m = user_settings["T_Re"], medTHeight
#        self.x5m, self.y5m = user_settings["T_Re"], lowTHeight
#        self.x6m, self.y6m = - user_settings["T_Re"], lowTHeight
#        self.x7m, self.y7m = - user_settings["T_Re"], medTHeight
#        self.x8m, self.y8m = - user_settings["T_Ri"], medTHeight
#        self.x9m, self.y9m = - user_settings["T_Ri"], fullTHeight
#        self.x10m, self.y10m = - user_settings["T_Re"], fullTHeight
#
#        available_len = self.x10 - self.x9
#        low_offset = (available_len - user_settings["mount_low_len"])/2
#        high_offset = (available_len - user_settings["mount_high_len"])/2
#
#        self.x1me, self.y1me = self.x9 + low_offset, self.y10
#        self.x2me, self.y2me = self.x9 + high_offset, self.y1m
#        self.x3me, self.y3me = self.x10 - high_offset, self.y1m
#        self.x4me, self.y4me = self.x10 - low_offset, self.y10
#
#        if user_settings["type"] == 'Fitted':
#
#            nozzleBodyWall_x = np.concatenate((
#                [self.x10, self.x11],
#                np.flip(convergent_x_wall),
#                np.flip(nozzle_x_wall),
#                [self.x13,self.x1]
#            ))
#
#            nozzleBodyWall_y = np.concatenate((
#                [self.y10, self.y11],
#                np.flip(convergent_y_wall),
#                np.flip(nozzle_y_wall),
#                [self.y13,self.y1]
#            ))
#
#        elif user_settings["type"] == 'Bulk':
#
#            nozzleBodyWall_x = np.concatenate((
#                [self.x10, self.x13],
#                [self.x13, self.x1]
#            ))
#
#            nozzleBodyWall_y = np.concatenate((
#                [self.y10, self.y13],
#                [self.y13, self.y1]
#            ))
#
#
#
#        engine_sketch_x = np.concatenate([
#            nozzle_x_in,
#            convergent_x,
#            [self.x3, self.x4],
#            [self.x4, self.x5] if not user_settings["oring"] else ring_arc_x,
#            [self.x5, self.x6],
#            [self.x6, self.x7],
#            [self.x7, self.x8],
#            [self.x8, self.x9],
#            [self.x9, self.x10],
#            nozzleBodyWall_x,
#        ])
#
#        engine_sketch_y = np.concatenate([
#            nozzle_y_in,
#            convergent_y,
#            [self.y3, self.y4],
#            [self.y4, self.y5] if not user_settings["oring"] else ring_arc_y,
#            [self.y5, self.y6],
#            [self.y6, self.y7],
#            [self.y7, self.y8],
#            [self.y8, self.y9],
#            [self.y9, self.y10],
#            nozzleBodyWall_y
#        ])
#
#        return engine_sketch_x, engine_sketch_y
#    
#    def sketchCartridge(self, axes, user_settings):
#        t_cartridge = user_settings["t_cartridge"]
#        self.x_cart = self.x6
#        self.yUp_cart = self.engineData["inputs"]["R2"]
#        self.yDown_cart = -self.yUp_cart - t_cartridge
#        cartridge_up = patches.Rectangle((self.x_cart, self.yUp_cart), self.LComb, t_cartridge, edgecolor='k', facecolor='yellow')
#        cartridge_down = patches.Rectangle((self.x_cart, self.yDown_cart), self.LComb, t_cartridge, edgecolor='k', facecolor='yellow')
#        axes.add_patch(cartridge_up)
#        axes.add_patch(cartridge_down)
#
#    def sketchRing_Engine(self, axes, user_settings):
#        t_cartridge = user_settings["t_cartridge"]
#        x = self.x4
#        yUp = self.y4 + t_cartridge/2
#        yDown = -yUp
#        oring_up = patches.Circle((x, yUp), t_cartridge/2, facecolor='r')
#        oring_down = patches.Circle((x, yDown), t_cartridge/2, facecolor='r')
#        axes.add_patch(oring_up)
#        axes.add_patch(oring_down)
#
#    def sketchRing_Cover(self, axes, user_settings):
#        t_cartridge = user_settings["t_cartridge"]
#        x = self.x0c
#        yUp = self.y0c
#        yDown = -yUp
#        oring_up = patches.Circle((x, yUp), t_cartridge/2, facecolor='r')
#        oring_down = patches.Circle((x, yDown), t_cartridge/2, facecolor='r')
#        axes.add_patch(oring_up)
#        axes.add_patch(oring_down)
#
#    def sketchPropellant(self, axes, user_settings):
#        
#        propellant_thickness = self.engineData["inputs"]["R2"] - self.engineData["inputs"]["r_in"]
#        x = self.x6 
#        yUp = self.engineData["inputs"]["r_in"]
#        yDown = -self.engineData["inputs"]["R2"]
#        propellant_up = patches.Rectangle((x, yUp), self.LComb, propellant_thickness, edgecolor='k', facecolor='brown')
#        propellant_down = patches.Rectangle((x, yDown), self.LComb, propellant_thickness, edgecolor='k', facecolor='brown')
#        axes.add_patch(propellant_up)
#        axes.add_patch(propellant_down)
#        #elif self.geometry == 'End-Burner':
#        #    x, y = self.x01c, -self.engineData["inputs"]["R2"]
#        #    w, h = self.LComb, 2 * self.engineData["inputs"]["R2"]
#        #    propellant = patches.Rectangle((x, y), w, h, edgecolor='k', facecolor='brown')
#        #    axes.add_patch(propellant)
#
#
#
#
#    def sketchCover(self, axes, user_settings):
#        arc_x, arc_y = self.create_arc(self.x0c, self.y0c, -np.pi/2, np.pi/2 , self.radi, turn=-1)
#
#        w = user_settings["cover_t"]
#        h = user_settings["r_elect"] - user_settings["d_elect"]/2
#
#        w_b = w
#        h_b = user_settings["r_elect"] + user_settings["d_elect"]/2
#
#        #if self.geometry == 'Tubular':
#        y6c, y1c = self.y6c, self.y1c
#        #elif self.geometry == 'End-Burner':
#        #    y6c, y1c = 0, 0
#
#        if not user_settings["cring"]:
#
#            self.cover_x = np.concatenate((
#                [self.x1c, self.x2c],
#                [self.x2c, self.x3c],
#                [self.x3c, self.x4c],
#                [self.x4c, self.x5c],
#                [self.x5c, self.x6c],
#                [self.x6c, self.x1c],
#            ))
#
#            self.cover_y = np.concatenate((
#                [y1c, self.y2c],
#                [self.y2c, self.y3c],
#                [self.y3c, self.y4c],
#                [self.y4c, self.y5c],
#                [self.y5c, y6c],
#                [y6c, y1c],
#            ))
#
#        else:
#
#            self.cover_x = np.concatenate((
#                [self.x1c, self.x01c],
#                arc_x,
#                [self.x02c, self.x2c],
#                [self.x2c, self.x3c],
#                [self.x3c, self.x4c],
#                [self.x4c, self.x5c],
#                [self.x5c, self.x6c],
#                [self.x6c, self.x1c],
#            ))
#
#            self.cover_y = np.concatenate((
#                [y1c, self.y01c],
#                arc_y,
#                [self.y02c, self.y2c],
#                [self.y2c, self.y3c],
#                [self.y3c, self.y4c],
#                [self.y4c, self.y5c],
#                [self.y5c, y6c],
#                [y6c, y1c],
#            ))
#
#        #if self.geometry == 'Tubular':
#        if user_settings["on_Background"]:
#            backGround = patches.Rectangle((self.x6c, -h_b), w_b, 2*h_b, edgecolor='k', facecolor='darkgrey')
#            axes.add_patch(backGround)
#
#        axes.plot(self.cover_x, self.cover_y, c='k', lw=1)
#        axes.plot(self.cover_x, -self.cover_y ,c='k', lw=1)
#
#        axes.fill(self.cover_x, self.cover_y, alpha=0.3, color='grey')
#        axes.fill(self.cover_x, -self.cover_y, alpha=0.3, color='grey')
#
#        if self.geometry == 'Tubular':
#            innerPart = patches.Rectangle((self.x6c, -h), w, 2*h, edgecolor='k', facecolor='lightgray', lw=1)
#            axes.add_patch(innerPart)
#        elif self.geometry == 'End-Burner':
#            pass
#
#
#
#    def sketchMountProfile(self, axes, user_settings):
#        
#        def x(y):
#            m = (self.x1me - self.x2me) / (self.y1me - self.y2me)
#            n = self.x1me - m * self.y1me
#            return m * y + n
#        
#        self.xLMC, self.yLMC = x(self.y5m), self.y5m
#        self.xHMC, self.yHMC = x(self.y3m), self.y3m
#
#        self.xa, self.ya = x(self.y5m), self.y5m
#        self.xd, self.yd = x(self.y3m), self.y3m
#        self.xf, self.yf = self.x2me, self.y2me
#
#        self.xb, self.yb = self.xf + user_settings["rail_len"], self.ya 
#        self.xc, self.yc = self.xf + user_settings["rail_len"], self.yd
#        self.xe, self.ye = self.xf + user_settings["rail_len"], self.y3me 
#        
#
#
#        self.mountP_sketch_x = np.concatenate((
#            [self.x1me, self.x2me],
#            [self.x2me, self.x3me],
#            [self.x3me, self.x4me],
#            [self.x4me, self.x1me]
#        ))
#
#        self.mountP_sketch_y = np.concatenate((
#            [self.y1me, self.y2me],
#            [self.y2me, self.y3me],
#            [self.y3me, self.y4me],
#            [self.y4me, self.y1me]
#        ))
#
#        back_cut1_x = np.concatenate((
#            [self.xa, self.xb],
#            [self.xb, self.xc],
#            [self.xc, self.xd],
#            [self.xd, self.xa]
#        ))
#
#        back_cut1_y = np.concatenate((
#            [self.ya, self.yb],
#            [self.yb, self.yc],
#            [self.yc, self.yd],
#            [self.yd, self.ya]
#        ))
#
#        back_cut2_x = np.concatenate((
#            [self.xd, self.xc],
#            [self.xc, self.xe],
#            [self.xe, self.xf],
#            [self.xf, self.xd]
#        ))
#
#        back_cut2_y = np.concatenate((
#            [self.yd, self.yc],
#            [self.yc, self.ye],
#            [self.ye, self.yf],
#            [self.yf, self.yd]
#        ))
#
#        axes.fill(self.mountP_sketch_x, self.mountP_sketch_y, facecolor='tab:green', edgecolor='k', lw=1) 
#        axes.fill(back_cut1_x, back_cut1_y, facecolor='darkgreen', edgecolor='k', lw=1)
#        axes.fill(back_cut2_x, back_cut2_y, facecolor='green', edgecolor='k', lw=1)
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#    # Funciones de Sketch de herramientas
#
#    def sketchCastingTubularProfile(self, axes, user_settings):
#
#        t_cartridge = user_settings["t_cartridge"]
#        t_factor = user_settings["t_factor"]
#        extra_len = user_settings["extra_len"]
#        cover_len = user_settings["cover_len"]
#        t_wall = t_cartridge * t_factor
#
#        self.x1_T1, self.y1_T1 = self.x6 - t_wall, 0
#        self.x2_T1, self.y2_T1 = self.x4 + t_wall + extra_len, 0
#        self.x3_T1, self.y3_T1 = self.x2_T1, self.engineData["inputs"]["Ri"]
#        self.x4_T1, self.y4_T1 = self.x6, self.y3_T1
#        self.x5_T1, self.y5_T1 = self.x6, self.y6
#        self.x6_T1, self.y6_T1 = self.x6 + cover_len, self.y6
#        self.x7_T1, self.y7_T1 = self.x6_T1, self.y6_T1 + t_wall
#        self.x8_T1, self.y8_T1 = self.x1_T1, self.y7_T1
#
#        self.x1_T2, self.y1_T2 = self.x4 + t_wall, self.engineData["inputs"]["Ri"]
#        self.x2_T2, self.y2_T2 = self.x1_T2, self.y7_T1
#        self.x3_T2, self.y3_T2 = self.x2_T2 - cover_len - t_wall, self.y7_T1
#        self.x4_T2, self.y4_T2 = self.x3_T2, self.y6_T1
#        self.x5_T2, self.y5_T2 = self.x5, self.y6
#        self.x6_T2, self.y6_T2 = self.x5_T2, self.engineData["inputs"]["Ri"]
#
#        self.x1_T3, self.y1_T3 = self.x1_T2 + user_settings["nut_h"], self.engineData["inputs"]["Ri"]
#        self.x2_T3, self.y2_T3 = self.x1_T3, self.y1_T3 + user_settings["nut_d"]
#        self.x3_T3, self.y3_T3 = self.x1_T2, self.y2_T3
#        self.x4_T3, self.y4_T3 = self.x1_T2, self.engineData["inputs"]["Ri"]
#
#        self.cover_tool_1_x = np.concatenate((
#            [self.x1_T1, self.x2_T1],
#            [self.x2_T1, self.x3_T1],
#            [self.x3_T1, self.x4_T1],
#            [self.x4_T1, self.x5_T1],
#            [self.x5_T1, self.x6_T1],
#            [self.x6_T1, self.x7_T1],
#            [self.x7_T1, self.x8_T1],
#            [self.x8_T1, self.x1_T1],
#        ))
#
#        self.cover_tool_1_y = np.concatenate((
#            [self.y1_T1, self.y2_T1],
#            [self.y2_T1, self.y3_T1],
#            [self.y3_T1, self.y4_T1],
#            [self.y4_T1, self.y5_T1],
#            [self.y5_T1, self.y6_T1],
#            [self.y6_T1, self.y7_T1],
#            [self.y7_T1, self.y8_T1],
#            [self.y8_T1, self.y1_T1],
#        ))
#
#        cover_tool_1_plot_x = np.concatenate((
#            [self.x1_T1, self.x8_T1],
#            [self.x8_T1, self.x7_T1],
#            [self.x7_T1, self.x6_T1],
#            [self.x6_T1, self.x5_T1],
#            [self.x5_T1, self.x4_T1],
#            [self.x4_T1, self.x3_T1],
#            [self.x3_T1, self.x3_T1],
#            [self.x3_T1, self.x4_T1],
#            [self.x4_T1, self.x5_T1],
#            [self.x5_T1, self.x6_T1],
#            [self.x6_T1, self.x7_T1],
#            [self.x7_T1, self.x8_T1],
#            [self.x8_T1, self.x1_T1],
#        ))
#
#        cover_tool_1_plot_y = np.concatenate((
#            [self.y1_T1, self.y8_T1],
#            [self.y8_T1, self.y7_T1],
#            [self.y7_T1, self.y6_T1],
#            [self.y6_T1, self.y5_T1],
#            [self.y5_T1, self.y4_T1],
#            [self.y4_T1, self.y3_T1],
#            [self.y3_T1, -self.y3_T1],
#            [-self.y3_T1, -self.y4_T1],
#            [-self.y4_T1, -self.y5_T1],
#            [-self.y5_T1, -self.y6_T1],
#            [-self.y6_T1, -self.y7_T1],
#            [-self.y7_T1, -self.y8_T1],
#            [-self.y8_T1, -self.y1_T1],
#        ))
#
#
#        self.cover_tool_2_x = np.concatenate((
#            [self.x1_T2, self.x2_T2],
#            [self.x2_T2, self.x3_T2],
#            [self.x3_T2, self.x4_T2],
#            [self.x4_T2, self.x5_T2],
#            [self.x5_T2, self.x6_T2],
#            [self.x6_T2, self.x1_T2],
#        ))
#
#        self.cover_tool_2_y = np.concatenate((
#            [self.y1_T2, self.y2_T2],
#            [self.y2_T2, self.y3_T2],
#            [self.y3_T2, self.y4_T2],
#            [self.y4_T2, self.y5_T2],
#            [self.y5_T2, self.y6_T2],
#            [self.y6_T2, self.y1_T2],
#        ))
#
#        self.cover_tool_3_x = np.concatenate((
#            [self.x1_T3, self.x2_T3],
#            [self.x2_T3, self.x3_T3],
#            [self.x3_T3, self.x4_T3],
#            [self.x4_T3, self.x1_T3],
#        ))
#
#        self.cover_tool_3_y = np.concatenate((
#            [self.y1_T3, self.y2_T3],
#            [self.y2_T3, self.y3_T3],
#            [self.y3_T3, self.y4_T3],
#            [self.y4_T3, self.y1_T3],
#        ))
#
#        if user_settings["on_Axis"]:
#            axes.plot([self.x1_T1, self.x2_T1], [0, 0], color='tab:red', ls='--')
#        
#        if user_settings["on_CoverCast1"]:
#            axes.fill(cover_tool_1_plot_x, cover_tool_1_plot_y, facecolor='lightgrey', edgecolor='k', lw=1) 
#
#        if user_settings["on_CoverCast2"]:
#            axes.fill(self.cover_tool_2_x, self.cover_tool_2_y, facecolor='lightgrey', edgecolor='k', lw=1) 
#            axes.fill(self.cover_tool_2_x, -self.cover_tool_2_y, facecolor='lightgrey', edgecolor='k', lw=1) 
#
#        if user_settings["on_CastNut"]:
#            axes.fill(self.cover_tool_3_x, self.cover_tool_3_y, facecolor='lightgrey', edgecolor='k', lw=1) 
#            axes.fill(self.cover_tool_3_x, -self.cover_tool_3_y, facecolor='lightgrey', edgecolor='k', lw=1) 
#   
#
#    def sketchCastingTubularFront_1(self, axes, user_settings):
#        
#        Ri_cover = self.y6_T1
#        Rext_cover = self.y7_T1
#        R_mould = self.engineData["inputs"]["Ri"]
#
#        circle_exterior = patches.Circle((0, 0), Rext_cover, facecolor='lightgray', edgecolor='k', linewidth=2)
#        circle_interior = patches.Circle((0, 0), Ri_cover, facecolor='lightgray', edgecolor='k', linewidth=2)
#        circle_mould = patches.Circle((0, 0), R_mould, facecolor='lightgray', edgecolor='k', linewidth=2)
#
#        axes.add_patch(circle_exterior)
#        axes.add_patch(circle_interior)
#        axes.add_patch(circle_mould)
#
#    def sketchCastingTubularFront_2(self, axes, user_settings):
#
#        Ri_cover = self.y6_T1
#        Rext_cover = self.y7_T1
#        R_mould = self.engineData["inputs"]["Ri"]
#
#        circle_exterior = patches.Circle((0, 0), Rext_cover, facecolor='lightgray', edgecolor='k', linewidth=2)
#        circle_interior = patches.Circle((0, 0), Ri_cover, facecolor='lightgray', edgecolor='k', linewidth=2)
#        circle_mould = patches.Circle((0, 0), R_mould, facecolor='white', edgecolor='k', linewidth=2)
#
#        axes.add_patch(circle_exterior)
#        axes.add_patch(circle_interior)
#        
#        if user_settings["on_CastNut"]:
#            circle_nut = patches.Circle((0, 0), self.y3_T3, facecolor="lightgray", edgecolor='k', linewidth=2, linestyle='--')
#            axes.add_patch(circle_nut)
#
#        axes.add_patch(circle_mould)
#
#
#    
#    def sketchCastingEndBurnerProfile(self, axes, user_settings):
#        t_cartridge = user_settings["t_cartridge"]
#        t_factor = user_settings["t_factor"]
#        cover_len = user_settings["cover_len"]
#        t_wall = t_cartridge * t_factor
#
#        self.x1_T1, self.y1_T1 = self.x6 - t_wall, 0
#        self.x2_T1, self.y2_T1 = self.x6, 0
#        self.x3_T1, self.y3_T1 = self.x6, self.y02c
#        self.x4_T1, self.y4_T1 = self.x6 + cover_len, self.y02c
#        self.x5_T1, self.y5_T1 = self.x4_T1, self.y4_T1 + t_wall
#        self.x6_T1, self.y6_T1 = self.x1_T1, self.y5_T1
#
#        self.x1_T2, self.y1_T2 = self.x4 + t_wall, 0
#        self.x2_T2, self.y2_T2 = self.x1_T2, self.y5_T1
#        self.x3_T2, self.y3_T2 = self.x1_T2 - t_wall - cover_len, self.y5_T1
#        self.x4_T2, self.y4_T2 = self.x3_T2, self.y4_T1
#        self.x5_T2, self.y5_T2 = self.x4, self.y3_T1
#        self.x6_T2, self.y6_T2 = self.x4, 0
#
#
#        cover_tool_1_plot_x = np.concatenate((
#            [self.x1_T1, self.x6_T1],
#            [self.x6_T1, self.x5_T1],
#            [self.x5_T1, self.x4_T1],
#            [self.x4_T1, self.x3_T1],
#            [self.x3_T1, self.x3_T1],
#            [self.x3_T1, self.x4_T1],
#            [self.x4_T1, self.x5_T1],
#            [self.x5_T1, self.x6_T1],
#            [self.x6_T1, self.x1_T1]
#        ))
#
#        cover_tool_1_plot_y = np.concatenate((
#            [self.y1_T1, self.y6_T1],
#            [self.y6_T1, self.y5_T1],
#            [self.y5_T1, self.y4_T1],
#            [self.y4_T1, self.y3_T1],
#            [self.y3_T1, -self.y3_T1],
#            [-self.y3_T1, -self.y4_T1],
#            [-self.y4_T1, -self.y5_T1],
#            [-self.y5_T1, -self.y6_T1],
#            [-self.y6_T1, -self.y1_T1]
#        ))
#
#        cover_tool_2_plot_x = np.concatenate((
#            [self.x1_T2, self.x2_T2],
#            [self.x2_T2, self.x3_T2],
#            [self.x3_T2, self.x4_T2],
#            [self.x4_T2, self.x5_T2],
#            [self.x5_T2, self.x5_T2],
#            [self.x5_T2, self.x4_T2],
#            [self.x4_T2, self.x3_T2],
#            [self.x3_T2, self.x2_T2],
#            [self.x2_T2, self.x1_T2]
#        ))
#
#        cover_tool_2_plot_y = np.concatenate((
#            [self.y1_T2, self.y2_T2],
#            [self.y2_T2, self.y3_T2],
#            [self.y3_T2, self.y4_T2],
#            [self.y4_T2, self.y5_T2],
#            [self.y5_T2, -self.y5_T2],
#            [-self.y5_T2, -self.y4_T2],
#            [-self.y4_T2, -self.y3_T2],
#            [-self.y3_T2, -self.y2_T2],
#            [-self.y2_T2, -self.y1_T2]
#        ))
#
#        self.cover_tool_1_x = np.concatenate((
#            [self.x1_T1, self.x2_T1],
#            [self.x2_T1, self.x3_T1],
#            [self.x3_T1, self.x4_T1],
#            [self.x4_T1, self.x5_T1],
#            [self.x5_T1, self.x6_T1],
#            [self.x6_T1, self.x1_T1]
#        ))
#
#        self.cover_tool_1_y = np.concatenate((
#            [self.y1_T1, self.y2_T1],
#            [self.y2_T1, self.y3_T1],
#            [self.y3_T1, self.y4_T1],
#            [self.y4_T1, self.y5_T1],
#            [self.y5_T1, self.y6_T1],
#            [self.y6_T1, self.y1_T1]
#        ))
#
#        self.cover_tool_2_x = np.concatenate((
#            [self.x1_T2, self.x2_T2],
#            [self.x2_T2, self.x3_T2],
#            [self.x3_T2, self.x4_T2],
#            [self.x4_T2, self.x5_T2],
#            [self.x5_T2, self.x6_T2],
#            [self.x6_T2, self.x1_T2]
#        ))
#
#        self.cover_tool_2_y = np.concatenate((
#            [self.y1_T2, self.y2_T2],
#            [self.y2_T2, self.y3_T2],
#            [self.y3_T2, self.y4_T2],
#            [self.y4_T2, self.y5_T2],
#            [self.y5_T2, self.y6_T2],
#            [self.y6_T2, self.y1_T2]
#        ))
#
#        if user_settings["on_Axis"]:
#            axes.plot([self.x1_T1, self.x1_T2], [0, 0], color='tab:red', ls='--')
#        
#        if user_settings["on_CoverCast1"]:
#            axes.fill(cover_tool_1_plot_x, cover_tool_1_plot_y, facecolor='lightgrey', edgecolor='k', lw=1) 
#
#        if user_settings["on_CoverCast2"]:
#            axes.fill(cover_tool_2_plot_x, cover_tool_2_plot_y, facecolor='lightgrey', edgecolor='k', lw=1) 
#
#        
#    def sketchCastingEndBurnerFront_1(self, axes, user_settings):
#
#        Ri_cover = self.y3_T1
#        Rext_cover = self.y6_T1
#
#        circle_exterior = patches.Circle((0, 0), Rext_cover, facecolor='lightgray', edgecolor='k', linewidth=2)
#        circle_interior = patches.Circle((0, 0), Ri_cover, facecolor='lightgray', edgecolor='k', linewidth=2)
#
#        axes.add_patch(circle_exterior)
#        axes.add_patch(circle_interior)
#   
#
#    def sketchCastingEndBurnerFront_2(self, axes, user_settings):
#        
#        Ri_cover = self.y3_T1
#        Rext_cover = self.y6_T1
#
#
#        circle_exterior = patches.Circle((0, 0), Rext_cover, facecolor='lightgray', edgecolor='k', linewidth=2)
#        circle_interior = patches.Circle((0, 0), Ri_cover, facecolor='lightgray', edgecolor='k', linewidth=2, ls='--')
#
#
#        axes.add_patch(circle_exterior)
#        axes.add_patch(circle_interior)
#
#
#
#
#
#
#
#
#
#    # Funciones de ploteo
#
#
#
#    def plot_Engine(self, user_settings):
#
#        fig, ax = plt.subplots(figsize=(16,9))
#        engine_x, engine_y = self.sketchEngine(user_settings)
#        
#        if user_settings["on_Engine"]:
#            ax.fill(engine_x, engine_y, edgecolor='k', facecolor='lightgray', lw=1)
#            ax.fill(engine_x, -engine_y, edgecolor='k', facecolor='lightgray', lw=1)
#
#            if user_settings["on_Background"]:
#                i6 = np.where(engine_x == self.x6)[0][-1]
#                ax.fill_between(engine_x[:i6], engine_y[:i6], -engine_y[:i6], color='grey')
#
#        if user_settings["on_Cartridge"]:
#            self.sketchCartridge(ax, user_settings)
#
#        if user_settings["on_ORing"] and user_settings["oring"]:
#            self.sketchRing_Engine(ax, user_settings)
#
#        if user_settings["on_CRing"] and user_settings["cring"]:
#            self.sketchRing_Cover(ax, user_settings)
#
#        if user_settings["on_Propellant"]:
#            self.sketchPropellant(ax, user_settings)
#
#        if user_settings["on_Cover"]:
#            self.sketchCover(ax, user_settings)
#
#            if user_settings["on_Background"]:
#                i6 = np.where(engine_x == self.x6)[0][-1]
#                ax.fill_between(engine_x[:i6], engine_y[:i6], -engine_y[:i6], alpha=0.3, color='grey')
#        
#        if user_settings["on_Mount"]:
#            self.sketchMountProfile(ax, user_settings)
#
#        if user_settings["on_Axis"]:
#            if user_settings["on_Cover"]:
#                xMin, xMax = self.x6c, self.x1
#            else:
#                xMin, xMax = self.x6, self.x1
#
#            ax.plot([xMin, xMax], [0, 0], ls='--', c='r')
#
#
#
#        ax.axis('equal')
#        ax.set_xlabel("Length (m)")
#        ax.set_ylabel("Radius (m)")
#        ax.set_title("Engine CAD Plot")
#        ax.grid(False)
#        return fig
#
#    def plot_frontCover(self, user_settings):
#
#        fig, ax = plt.subplots(figsize=(9,9))
#        self.sketchEngine(user_settings)
#
#        circle_exterior = patches.Circle((0, 0), self.y9, facecolor='lightgray', edgecolor='k', linewidth=2)
#        circle_nut = patches.Circle((0, 0), self.y8, facecolor='lightgray', edgecolor='k', linewidth=2)
#        ax.add_patch(circle_exterior)
#        ax.add_patch(circle_nut)
#
#        if user_settings["cring"]:
#            interior_ring = patches.Circle((0, 0), self.y01c, facecolor='grey', edgecolor='k', linewidth=2)
#            exterior_ring = patches.Circle((0, 0), self.y02c, facecolor='grey', edgecolor='k', linewidth=2)
#            aux_ring = patches.Circle((0, 0), self.y01c, facecolor='lightgray', edgecolor='k', linewidth=2)
#            ax.add_patch(exterior_ring)
#            ax.add_patch(interior_ring)
#            if user_settings["on_CRing"]:
#                ring_interior = patches.Circle((0, 0), self.y01c, facecolor='r', edgecolor='k', linewidth=2)
#                ring_exterior = patches.Circle((0, 0), self.y02c, facecolor='r', edgecolor='k', linewidth=2)
#                aux_ring = patches.Circle((0, 0), self.y01c, facecolor='lightgray', edgecolor='k', linewidth=2)
#                ax.add_patch(ring_interior)
#                ax.add_patch(ring_exterior)
#            
#            ax.add_patch(aux_ring)
#
#        y = user_settings["r_elect"]
#        r = user_settings["d_elect"]/2
#
#        elect1 = patches.Circle((0, y), r, facecolor='white', edgecolor='k', linewidth=2)
#        elect2 = patches.Circle((0, -y), r, facecolor='white', edgecolor='k', linewidth=2)
#        ax.add_patch(elect1)
#        ax.add_patch(elect2)
#
#
#        ax.axis('equal')
#        ax.set_xlabel("Length (m)")
#        ax.set_ylabel("Radius (m)")
#        ax.set_title("Engine CAD Plot")
#        ax.grid(False)
#        return fig
#    
#    def plot_mount_front(self, user_settings):
#        
#        self.sketchEngine(user_settings)
#
#        tan_x1, tan_y1 = self.find_tangent_points(self.x1m, self.y1m, self.y10)
#        tan_x2, tan_y2 = -tan_x1, tan_y1
#
#        theta_1 = np.arctan2(tan_y1, tan_x1)
#        theta_2 = np.arctan2(tan_y2, tan_x2)
#
#        arcPoints_x, arcPoints_y = self.create_arc(0, 0, theta_1, theta_2 , self.y10, num_points=100, turn=1)
#
#        self.mount_skecth_x = np.concatenate((
#            [self.x10m, arcPoints_x[-1]],
#            np.flip(arcPoints_x),
#            [arcPoints_x[0],self.x1m]
#        ))
#
#        self.mount_skecth_y = np.concatenate((
#            [self.y10m, arcPoints_y[-1]],
#            np.flip(arcPoints_y),
#            [arcPoints_y[0],self.y1m]
#        ))
#
#        self.T_Sketch_x = np.concatenate((
#            [self.x1m, self.x2m],
#            [self.x2m, self.x3m],
#            [self.x3m, self.x4m],
#            [self.x4m, self.x5m],
#            [self.x5m, self.x6m],
#            [self.x6m, self.x7m],
#            [self.x7m, self.x8m],
#            [self.x8m, self.x9m],
#            [self.x9m, self.x10m],
#            self.mount_skecth_x
#        ))
#
#        self.T_Sketch_y = np.concatenate((
#            [self.y1m, self.y2m],
#            [self.y2m, self.y3m],
#            [self.y3m, self.y4m],
#            [self.y4m, self.y5m],
#            [self.y5m, self.y6m],
#            [self.y6m, self.y7m],
#            [self.y7m, self.y8m],
#            [self.y8m, self.y9m],
#            [self.y9m, self.y10m],
#            self.mount_skecth_y
#        ))
#
#
#        fig, ax = plt.subplots(figsize=(9,9))
#        self.sketchEngine(user_settings)
#
#        circle_exterior = patches.Circle((0, 0), self.y9, facecolor='lightgray', edgecolor='k', linewidth=2)
#        circle_nut = patches.Circle((0, 0), self.y8, facecolor='lightgray', edgecolor='k', linewidth=2, linestyle='--')
#        ax.add_patch(circle_exterior)
#        ax.add_patch(circle_nut)
#
#        
#
#        y = user_settings["r_elect"]
#        r = user_settings["d_elect"]/2
#
#        elect1 = patches.Circle((0, y), r, facecolor='white', edgecolor='k', linewidth=2)
#        elect2 = patches.Circle((0, -y), r, facecolor='white', edgecolor='k', linewidth=2)
#        ax.add_patch(elect1)
#        ax.add_patch(elect2)
#
#        ax.fill(self.T_Sketch_x, self.T_Sketch_y, facecolor='lightgreen', edgecolor='k', lw=2)
#
#        if user_settings["on_Background"]:
#
#            Back_x = np.concatenate((
#                [self.x2m, self.x3m],
#                [self.x3m, self.x4m],
#                [self.x4m, self.x5m],
#                [self.x5m, self.x6m],
#                [self.x6m, self.x7m],
#                [self.x7m, self.x8m],
#                [self.x8m, self.x9m],
#                [self.x9m, self.x2m]
#            ))
#
#            Back_y = np.concatenate((
#                [self.y2m, self.y3m],
#                [self.y3m, self.y4m],
#                [self.y4m, self.y5m],
#                [self.y5m, self.y6m],
#                [self.y6m, self.y7m],
#                [self.y7m, self.y8m],
#                [self.y8m, self.y9m],
#                [self.y9m, self.y2m]
#            ))
#
#            ax.fill(Back_x, Back_y, facecolor='tab:green', edgecolor='k', lw=2)
#
#
#        ax.axis('equal')
#        ax.set_xlabel("Length (m)")
#        ax.set_ylabel("Radius (m)")
#        ax.set_title("Engine CAD Plot")
#        ax.grid(False)
#        return fig
#    
#    
#    def plot_Tools(self, user_settings):
#
#        fig, ax = plt.subplots(figsize=(16,9))
#        self.sketchEngine(user_settings)
#
#        if user_settings["on_Cartridge"]:
#            self.sketchCartridge(ax, user_settings)
#
#        if user_settings["on_Propellant"]:
#            self.sketchPropellant(ax, user_settings)
#
#
#
#        if self.geometry == 'Tubular':
#            self.sketchCastingTubularProfile(ax, user_settings)
#        elif self.geometry == 'End-Burner':
#            self.sketchCastingEndBurnerProfile(ax, user_settings)
#
#
#
#        ax.axis('equal')
#        ax.set_xlabel("Length (m)")
#        ax.set_ylabel("Radius (m)")
#        ax.set_title("Engine CAD Plot")
#        ax.grid(False)
#        return fig
#    
#    def plot_Front1_Tools(self, user_settings):
#
#        fig, ax = plt.subplots(figsize=(9,9))
#        self.sketchEngine(user_settings)
#
#        if self.geometry == 'Tubular':
#            self.sketchCastingTubularFront_1(ax, user_settings)
#        elif self.geometry == 'End-Burner':
#            self.sketchCastingEndBurnerFront_1(ax, user_settings)
#
#        ax.axis('equal')
#        ax.set_xlabel("Length (m)")
#        ax.set_ylabel("Radius (m)")
#        ax.set_title("Engine CAD Plot")
#        ax.grid(False)
#        return fig
#    
#    def plot_Front2_Tools(self, user_settings):
#
#        fig, ax = plt.subplots(figsize=(9,9))
#        self.sketchEngine(user_settings)
#
#        if self.geometry == 'Tubular':
#            self.sketchCastingTubularFront_2(ax, user_settings)
#        elif self.geometry == 'End-Burner':
#            self.sketchCastingEndBurnerFront_2(ax, user_settings)
#
#        ax.axis('equal')
#        ax.set_xlabel("Length (m)")
#        ax.set_ylabel("Radius (m)")
#        ax.set_title("Engine CAD Plot")
#        ax.grid(False)
#        return fig
#
#
#
#
#
#
#
#
#
#
#
#
#    # Funciones de exportar
#
#    def export_engine(self, user_settings, file_path):
#        x, y = self.sketchEngine(user_settings) 
#        z = np.zeros(len(x))
#
#        for i in range(len(x)):
#            if x[i] == self.x3 and y[i] == self.y3:
#                int_index = i
#                break 
#        
#        for i in range(len(x)):
#            if x[i] == self.x11 and y[i] == self.y11:
#                ext_index = i
#                break 
#
#        x0 = x[:int_index+1]
#        y0 = y[:int_index+1]
#        z0 = z[:int_index+1]
#
#        x1 = x[int_index:ext_index+1]
#        y1 = y[int_index:ext_index+1]
#        z1 = z[int_index:ext_index+1]
#
#        x2 = x[ext_index:-2]
#        y2 = y[ext_index:-2]
#        z2 = z[ext_index:-2] 
#
#        x3 = x[-2:]
#        y3 = y[-2:]
#        z3 = z[-2:] 
#
#
#
#
#        with open(file_path, mode='w', newline='') as file:
#            writer = csv.writer(file)
#            writer.writerow(['Sketch', 'Plane', 'x', 'y', 'z'])
#
#            for i in range(len(x0)):
#                writer.writerow([0, 'XY' ,x[i] * 100, y[i] * 100, z[i] * 100])
#            
#            #for i in range(len(x0)):
#            #    writer.writerow([0, 'XY', 'Spline' ,x0[i] * 100, y0[i] * 100, z0[i] * 100])
#            #for i in range(len(x1)):
#            #    writer.writerow([0, 'XY', 'Line' ,x1[i] * 100, y1[i] * 100, z1[i] * 100])
#            #for i in range(len(x2)):
#            #    writer.writerow([0, 'XY', 'Spline' ,x2[i] * 100, y2[i] * 100, z2[i] * 100])
#            #for i in range(len(x3)):
#            #    writer.writerow([0, 'XY', 'Line' ,x3[i] * 100, y3[i] * 100, z3[i] * 100])
#        
#
#    def export_cover(self, user_settings, file_path):
#        self.cover_y[0]     = 0
#        self.cover_y[-1]    = 0
#        self.cover_y[-2]    = 0
#
#        x0 = self.cover_x
#        y0 = self.cover_y
#        z0 = np.zeros(len(x0))
#
#        zC = user_settings["r_elect"]
#        r = user_settings["d_elect"]/2
#        y1, z1 = self.create_arc(0, zC, 0, 2*np.pi , r, num_points=100, turn=1)
#        x1 = np.full(len(y1), self.x6c)
#    
#        with open(file_path, mode='w', newline='') as file:
#            writer = csv.writer(file)
#
#            writer.writerow(['Sketch', 'Plane' , 'x', 'y', 'z'])
#
#            for i in range(len(x0)):
#                writer.writerow([0, 'XY' ,x0[i] * 100, y0[i] * 100, z0[i] * 100])
#
#            for i in range(len(x1)):
#                writer.writerow([1, 'YZ' ,x1[i] * 100, y1[i] * 100, z1[i] * 100])
#
#            for i in range(len(x1)):
#                writer.writerow([2, 'YZ' ,x1[i] * 100, y1[i] * 100, - z1[i] * 100])
#
#    def export_mount(self, user_settings, file_path):
#
#        x0 = self.mountP_sketch_x
#        y0 = self.mountP_sketch_y
#        z0 = np.zeros(len(x0))
#
#        y1 = self.T_Sketch_x
#        z1 = self.T_Sketch_y
#        x1 = np.full(len(y1), self.xe)
#
#
#        with open(file_path, mode='w', newline='') as file:
#            writer = csv.writer(file)
#
#            writer.writerow(['Sketch', 'Plane' , 'x', 'y', 'z'])
#
#            for i in range(len(x0)):
#                writer.writerow([0, 'XY' ,x0[i] * 100, y0[i] * 100, z0[i] * 100])
#
#            for i in range(len(x1)):
#                writer.writerow([1, 'YZ' ,x1[i] * 100, y1[i] * 100, z1[i] * 100])
#
#    def export_tools(self, user_settings, file_path):
#
#        x0 = self.cover_tool_1_x
#        y0 = self.cover_tool_1_y
#        z0 = np.zeros(len(x0))
#
#        x1 = self.cover_tool_2_x
#        y1 = self.cover_tool_2_y
#        z1 = np.zeros(len(x1))
#
#        if not self.geometry == 'End-Burner':
#            x2 = self.cover_tool_3_x
#            y2 = self.cover_tool_3_y
#            z2 = np.zeros(len(x2))
#
#        with open(file_path, mode='w', newline='') as file:
#            writer = csv.writer(file)
#
#            writer.writerow(['Sketch', 'Plane' , 'x', 'y', 'z'])
#
#            for i in range(len(x0)):
#                writer.writerow([0, 'XY' ,x0[i] * 100, y0[i] * 100, z0[i] * 100])
#
#            for i in range(len(x1)):
#                writer.writerow([1, 'XY' ,x1[i] * 100, y1[i] * 100, z1[i] * 100])
#
#            if not self.geometry == 'End-Burner':
#                for i in range(len(x2)):
#                    writer.writerow([1, 'XY' ,x2[i] * 100, y2[i] * 100, z2[i] * 100])