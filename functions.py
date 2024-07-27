from imports import *



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


