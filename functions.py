from imports import *

#def global_exception_handler(exc_type, exc_value, exc_traceback):
#    if issubclass(exc_type, KeyboardInterrupt):
#        # Permite la salida con Ctrl+C sin el trace del error
#        sys.__excepthook__(exc_type, exc_value, exc_traceback)
#        return
#    error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
#    messagebox.showinfo("Error", f"Error:\n{error_message}")
#
## Establece la función global para manejar excepciones no controladas
#sys.excepthook = global_exception_handler

def get_data(type, file):
        with open('temp_dir.txt', 'r') as txt:
            dir = txt.readline()
        file_path = dir + f'\\{type}\\' + file
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

def get_entry_value(entry):
        return entry.get() if entry.get() else '0'

def validate_scientific_notation(value):
    pattern = r'^-?\d*\.?\d+(?:[eE][-+]?\d+)?$'
    return re.match(pattern, value) is not None

def get_database_components():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Component FROM termoquimica")
    components = [row[0] for row in cursor.fetchall()]
    conn.close()
    latex_components = [convert_to_latex(component) for component in components]  # Crear diccionario para mapeo
    latex_map = dict(zip(components, latex_components))
    return [components, latex_map]

def get_propellant_value(column_name, cell_value):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Define the SQL query to fetch the components based on the criteria
    query = f"""
    SELECT DISTINCT {column_name} 
    FROM propelente 
    WHERE propelente.Propelente = ?"""  # Assuming "column2" is the second column's name

    cursor.execute(query, (cell_value,))
    components = [row[0] for row in cursor.fetchall()]
    
    # Close the connection
    conn.close()

    return components

def convert_to_latex(component):
    # Remove any text in parentheses
    component = re.sub(r'\(.*?\)', '', component).strip()

    # Replace numbers with subscript format
    component = re.sub(r'(\d+)', r'_{\1}', component)
    
    return component

# Función para guardar el directorio en un archivo temporal
def save_dir_path(dir_path):
    with open("temp_dir.txt", "w") as file:
        file.write(dir_path)

# Función para leer el directorio desde el archivo temporal
def get_dir_path():
    if os.path.exists("temp_dir.txt"):
        with open("temp_dir.txt", "r") as file:
            return file.read().strip()
    return None

# Función para eliminar el archivo temporal
def clear_dir_path():
    if os.path.exists("temp_dir.txt"):
        os.remove("temp_dir.txt")




def newtonRaph(f, x0, tol, max_iter, h):
    """
    Método de Newton-Raphson para encontrar las raíces de una función.
    Args:
    f: función objetivo.
    x0: valor inicial para la raíz.
    tol: tolerancia para la convergencia.
    max_iter: número máximo de iteraciones.
    h: paso pequeño para la derivada numérica.
    Returns:
    La raíz aproximada de la función.
    """
    def fp(f, x, h):
        return (f(x + h) - f(x - h)) / (2 * h)

    x = x0
    for i in range(max_iter):
        fx = f(x)
        dfx = fp(f, x, h)

        if dfx == 0:
            return messagebox.showinfo("Error", "Derivada nula. El método de Newton-Raphson no puede continuar.")

        x_new = x - fx / dfx

        if abs(x_new - x) < tol:
            return x_new

        x = x_new

    return messagebox.showinfo("Error", "El método de Newton-Raphson no convergió en el número máximo de iteraciones.")

def integration(f,a,b,h):
    return h * ( (f(a) + f(b))/2 + sum([f(a + k*h) for k in range(1, int((b - a)/h))]))

def discreteIntegration(fs, xs):
    return sum([(xs[i+1] - xs[i]) * (fs[i+1] + fs[i]) / 2 for i in range(len(fs)-1)])

def initialize_database():
    db_filename = 'database.db'
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS termoquimica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Component TEXT,
            MolWeight NUMERIC,
            Hf0 NUMERIC,
            minColdTemp NUMERIC,
            maxColdTemp NUMERIC,
            minHotTemp NUMERIC,
            maxHotTemp NUMERIC,
            a1_cold NUMERIC,
            a2_cold NUMERIC,
            a3_cold NUMERIC,
            a4_cold NUMERIC,
            a5_cold NUMERIC,
            a1_hot NUMERIC,
            a2_hot NUMERIC,
            a3_hot NUMERIC,
            a4_hot NUMERIC,
            a5_hot NUMERIC
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS propelente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Propelente TEXT,
            T_ad NUMERIC,
            MolWeight NUMERIC,
            Cp NUMERIC,
            Cv NUMERIC,
            R NUMERIC,
            gamma NUMERIC,
            cChar NUMERIC,
            Density NUMERIC,
            P1_min NUMERIC,
            P1_max NUMERIC,
            a NUMERIC,
            n NUMERIC
        )
    ''')

    conn.commit()
    conn.close()

def insert_fig(fig, frame, resize='Manual', l=0.1, r=0.9, t=0.9, b=0.2):
    # Crear un nuevo canvas de FigureCanvasTkAgg pero no mostrarlo aún
    new_canvas = FigureCanvasTkAgg(fig, master=frame)
    new_widget = new_canvas.get_tk_widget()

    # Redimensionar la figura para ajustarse al tamaño del frame
    def on_resize(event=None, canvas=new_canvas, widget=new_widget, force_resize=False):
        if event is None:
            width, height = frame.winfo_width(), frame.winfo_height()
        else:
            width, height = event.width, event.height

        fig.set_size_inches(width / fig.dpi, height / fig.dpi)
        if resize != 'Auto':
            fig.subplots_adjust(left=l, right=r, top=t, bottom=b)
        canvas.draw()

        if force_resize:
            # Mostrar el nuevo canvas
            widget.pack(side=ctk.TOP, fill=ctk.BOTH, expand=1)
            widget.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            # Eliminar el canvas anterior si existe
            if hasattr(frame, 'canvas'):
                old_canvas = frame.canvas
                old_widget = old_canvas.get_tk_widget()
                old_widget.destroy()

            # Asignar el nuevo canvas al frame
            frame.canvas = canvas

            # Cerrar la figura para liberar memoria
            plt.close(fig)

    # Si el frame no tiene el bind de redimensionar, lo agrega
    if not hasattr(frame, 'resize_bound'):
        frame.bind("<Configure>", on_resize)
        frame.resize_bound = True

    # Llamar al on_resize manualmente para redimensionar inmediatamente
    frame.update_idletasks()
    on_resize(force_resize=True)
    plt.close(fig)


def gaugePlot(instValues, maxValues=[0,0,0,0]):
    fig, ax = plt.subplots(figsize=(16, 16))

    # Create a color gradient around the outer circle edge
    n = 25  # Number of segments for the gradient
    cmap = plt.get_cmap('plasma')  # Color map
    delta = 0
    theta = np.linspace(0 - delta, np.pi + delta, n)  # Divide the semicircle into 'n' segments

    x = 1
    y = 0.6
    ri = 0.75
    w = 0.25
    edgCol = 'k'

    instValues = np.array(instValues)
    maxValues = np.array(maxValues)
    percValues = instValues / maxValues

    # Loop over the four positions to plot the gauges
    for j, perc in enumerate(percValues):
        # Determine the number of wedges to fill based on the percentage
        num_fill = int(n * perc)  # Calculate the number of wedges to fill

        # Determine the position offsets for each gauge
        if j == 0:
            x_pos, y_pos = -x, y
        elif j == 1:
            x_pos, y_pos = x, y
        elif j == 2:
            x_pos, y_pos = -x, -y
        else:
            x_pos, y_pos = x, -y

        for i in range(n - 1):
            # Set the color for each wedge
            if num_fill > 0 and i >= (n - num_fill):
                color = cmap(i / (n - 1))  # Fill wedges in reverse order
            else:
                color = 'lightgrey'  # Set the remaining wedges to light grey

            # Create the wedges with the corresponding color
            wedge = patches.Wedge(center=(x_pos, y_pos), r=ri + 0.05, theta1=np.degrees(theta[i]),
                                  theta2=np.degrees(theta[i + 1]), width=w, facecolor=color, edgecolor=edgCol, linewidth=2)
            ax.add_patch(wedge)
  

    # Add text to the rectangles
    ax.text(-x, 1.6 * y + 0.02 * ri    , f"{instValues[0]:.2f}", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(x, 1.6 * y + 0.02 * ri     , f"{instValues[1]:.2f}", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(-x, 0.4 * -y + 0.02 * ri   , f"{instValues[2]:.2f}", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(x, 0.4 * -y + 0.02 * ri    , f"{instValues[3]:.2f}", ha='center', va='center', fontsize=10, fontweight='bold')

    ax.text(-x, 1.6 * y + 0.02 * ri    - 0.2, "THRUST (KG)"       , ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(x, 1.6 * y + 0.02 * ri     - 0.2, "TEMPERATURE (K)"   , ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(-x, 0.4 * -y + 0.02 * ri   - 0.2, "BATTERY LEVEL (%)" , ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(x, 0.4 * -y + 0.02 * ri    - 0.2, "WATER LEVEL (%)"   , ha='center', va='center', fontsize=9, fontweight='bold')

    # Fix the percentage to the range [0, 1] so it does not exceed the maximum angle

    # Adjust axis scales so the circle does not get deformed
    ax.set_aspect('equal', 'box')

    # Set axis limits
    ax.set_xlim(-2, 2)
    ax.set_ylim(-0.6, 1.5)
    fig.tight_layout()
    ax.set_axis_off()
    
    return fig





class TempSchemes:
    
    @staticmethod
    def Euler(f, u, h):
        k1 = np.array([fi(u) for fi in f])
        return u + h * k1
    
    @staticmethod
    def Heun(f, u, h):
        k1 = np.array([fi(u) for fi in f])
        k2 = np.array([fi(u + k1 * h) for fi in f])
        return u + h * (k1 + k2) / 2
    
    @staticmethod
    def RK4(f, u, h):
        k1 = np.array([fi(u) for fi in f])
        k2 = np.array([fi(u + 0.5 * k1 * h) for fi in f])
        k3 = np.array([fi(u + 0.5 * k2 * h) for fi in f])
        k4 = np.array([fi(u + k3 * h) for fi in f])
        return u + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6

def numerical_derivative(x, f):
    """
    Computes the numerical derivative of a function given by arrays of x and f values.
    
    Parameters:
    - x: array of x values (independent variable).
    - f: array of f values (dependent variable).
    
    Returns:
    - df_dx: array of the numerical derivative df/dx.
    """
    if len(x) != len(f):
        raise ValueError("The length of x and f must be the same")
    
    df_dx = np.zeros_like(f)
    
    # Central difference for the interior points
    df_dx[1:-1] = (f[2:] - f[:-2]) / (x[2:] - x[:-2])
    
    # Forward difference for the first point
    df_dx[0] = (f[1] - f[0]) / (x[1] - x[0])
    
    # Backward difference for the last point
    df_dx[-1] = (f[-1] - f[-2]) / (x[-1] - x[-2])
    
    return df_dx

def solve_ode_system(f_system, u0, h, method, t_max, divergence_threshold=1e6, stop_conditions=None, indefinite=False):
    """
    General solver for a system of differential equations.
    
    Parameters:
    - f_system: list of functions defining the system of ODEs.
    - u0: initial conditions as a list or numpy array.
    - h: step size.
    - method: string, "Euler", "Heun", or "RK4".
    - t_max: maximum time for the simulation.
    - divergence_threshold: optional float, threshold for divergence detection.
    - stop_conditions: optional list of functions, each taking the current state as input and returning a boolean.
    - indefinite: boolean, if True the simulation will run indefinitely until a stop condition is met.
    
    Returns:
    - sol: numpy array with the solution for each variable over time.
    - t: numpy array with the time points.
    """
    schemes = {
        "Euler": TempSchemes.Euler,
        "Heun": TempSchemes.Heun,
        "RK4": TempSchemes.RK4
    }
    
    if method not in schemes:
        raise messagebox.showinfo("Error", "Method should be 'Euler', 'Heun', or 'RK4'")
        return
    
    try:
        num_steps = int(t_max / h) + 1 if t_max else 1000  # Initial allocation, will expand if indefinite is True
        sol = np.zeros((num_steps, len(u0)))
        sol[0] = u0

        t = np.zeros(num_steps)
        
        i = 1
        while True:
            if not indefinite and i >= num_steps:
                break
            
            if indefinite and i >= num_steps:
                # Expand arrays if running indefinitely
                sol = np.vstack([sol, np.zeros((1000, len(u0)))])
                t = np.hstack([t, np.zeros(1000)])
                num_steps += 1000

            sol[i] = schemes[method](f_system, sol[i-1], h)
            t[i] = t[i-1] + h
  
            # Check for divergence
            if np.any(np.abs(sol[i] - sol[i-1]) > divergence_threshold):
                messagebox.showinfo("Divergence stop", "Simulation stopped due to divergence.")
                break
            
            # Check for custom stop conditions
            if stop_conditions:
                if any(condition(sol[i]) for condition in stop_conditions):
                    messagebox.showinfo("Conditional stop", f"Simulation stopped due to custom stop condition")
                    break
            
            i += 1
        
        # Trim the arrays to the actual size
        sol = sol[:i]
        t = t[:i]
    except Exception or RuntimeError:
        messagebox.showinfo("Error", f"Error de cálculo:\n{traceback.format_exc()}")
        return 
    
    return sol, t


def getSerialValues(line):
    """
    Extrae los valores de tiempo, fuerza y temperatura de una línea de texto 
    con el formato "t(s): <valor>\t F(kg): <valor>\t T(K): <valor>".

    Args:
    line (str): Línea de texto que contiene los valores.

    Returns:
    tuple: Una tupla con los valores de tiempo, fuerza y temperatura como floats.
           Devuelve None si no se encuentran los valores en el formato esperado.
    """
    # Expresión regular para capturar los tres valores específicos en el formato correcto
    match = re.match(r"t\(s\):\s*([-+]?\d*\.\d+|\d+)\s*F\(kg\):\s*([-+]?\d*\.\d+|\d+)\s*T\(K\):\s*([-+]?\d*\.\d+|\d+)", line)

    if match:  # Si la línea coincide con el formato esperado
        # Extraer los tres valores y convertirlos a flotantes
        return tuple(map(float, match.groups()))
    else:
        # Retornar None si no se encuentra el formato esperado
        return None


def importLibraries(lib):
    root = os.getcwd()
    libraryDir = os.path.join(root, lib)

    if not os.path.isdir(libraryDir):
        print(f"La ruta {libraryDir} no existe.")
        return {}

    if libraryDir not in sys.path:
        sys.path.append(libraryDir)

    nozzleClasses = {}
    for fileName in os.listdir(libraryDir):
        if fileName.endswith('.py') and fileName != '__init__.py':
            modName = fileName[:-3]
            try:
                modulo = importlib.import_module(modName)
                # Obtener todas las clases definidas en el módulo
                classes = [obj for name, obj in inspect.getmembers(modulo, inspect.isclass) if obj.__module__ == modulo.__name__]
                for classs in classes:
                    # Verificar si la clase tiene el atributo 'nozzle_type'
                    if hasattr(classs, 'nozzle_type'):
                        nozzle_type = getattr(classs, 'nozzle_type')
                        nozzleClasses[nozzle_type] = classs
            except ImportError as e:
                print(f"No se pudo importar el módulo {modName}: {e}")
    return nozzleClasses



