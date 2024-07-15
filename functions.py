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




