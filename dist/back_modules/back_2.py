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
            (-self.engineData["inputs"]["Lc"] + xConvCon)
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



