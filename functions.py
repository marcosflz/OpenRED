import os


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




