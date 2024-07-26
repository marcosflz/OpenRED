from imports import *
from functions import *

from back_0 import *

from front_0 import *
from front_1 import *
from front_2 import *
from front_3 import *
from front_4 import *


# Llamar a la función para inicializar la base de datos al iniciar el programa
initialize_database()

global working_path
global file_path
closing = False

working_path = None
file_path = None

# Función para obtener el valor del Entry con un valor por defecto de 0 si está vacío
def get_entry_value(entry):
    return entry.get() if entry.get() else '0'


def open_directory():
    global working_path
    global file_path
    working_path = filedialog.askdirectory()
    if working_path:
        file_path = os.path.join(working_path, "config.json")
        save_dir_path(working_path)
        load_configuration(working_path)


def open_on_saving_directory():
    global working_path
    global file_path
    working_path = filedialog.askdirectory()
    if working_path:
        file_path = os.path.join(working_path, "config.json")
        if os.path.isfile(file_path):
            messagebox.showerror("Error de directorio", "Ya existe un archivo de configuración, por favor selecciona otro directorio.", parent=main_frame)
            return False
        else:
            save_dir_path(working_path)
            return True


def save_configuration():
    try:
        file_path = os.path.join(working_path, "config.json")
    except Exception:
        if open_on_saving_directory():
            file_path = os.path.join(working_path, "config.json")
        else:
            return

    if file_path:
        config = {
            "tabs": {
                "tab_0": {
                    "reactivos": [(get_entry_value(entry), combo.get()) for entry, combo in adiabatic_module_instance.reactivos_widgets],
                    "productos": [(get_entry_value(entry), combo.get()) for entry, combo in adiabatic_module_instance.productos_widgets],
                    "initial_temp": get_entry_value(adiabatic_module_instance.initial_temp),
                    "temp_Int_step": get_entry_value(adiabatic_module_instance.temp_Int_step),
                    "temp_guess": get_entry_value(adiabatic_module_instance.temp_guess)
                },
                "tab_1": {
                    "propellant": engineDesing_module_instance.propellant_selector.get(),
                    "geoConfig": engineDesing_module_instance.grainGeo_selector.get(),
                    "tubular_rIn": get_entry_value(engineDesing_module_instance.tubular_entries[0]),
                    "tubular_rOut": get_entry_value(engineDesing_module_instance.tubular_entries[1]),
                    "tubular_rt": get_entry_value(engineDesing_module_instance.tubular_entries[2]),
                    "tubular_lComb": get_entry_value(engineDesing_module_instance.tubular_entries[3]),
                    "tubular_P0": get_entry_value(engineDesing_module_instance.tubular_entries[4]),
                    "tubular_dr": get_entry_value(engineDesing_module_instance.tubular_entries[5]),
                },
            }
        }
        with open(file_path, 'w') as config_file:
            json.dump(config, config_file)


def load_configuration(working_path):
    file_path = os.path.join(working_path, "config.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as config_file:
                config = json.load(config_file)

            # Restaurar la configuración de las pestañas
            tab_0_config = config["tabs"]["tab_0"]
            tab_1_config = config["tabs"]["tab_1"]

            # Clear existing widgets
            for entry, combo in adiabatic_module_instance.reactivos_widgets:
                entry.destroy()
                combo.destroy()
            adiabatic_module_instance.reactivos_widgets.clear()
            adiabatic_module_instance.reactivo_row = 2

            for entry, combo in adiabatic_module_instance.productos_widgets:
                entry.destroy()
                combo.destroy()
            adiabatic_module_instance.productos_widgets.clear()
            adiabatic_module_instance.producto_row = 2

            # Load reactivos
            for mole, reactivo in tab_0_config["reactivos"]:
                adiabatic_module_instance.add_reactivo()
                adiabatic_module_instance.reactivos_widgets[-1][0].insert(0, mole)
                adiabatic_module_instance.reactivos_widgets[-1][1].set(reactivo)

            # Load productos
            for mole, producto in tab_0_config["productos"]:
                adiabatic_module_instance.add_producto()
                adiabatic_module_instance.productos_widgets[-1][0].insert(0, mole)
                adiabatic_module_instance.productos_widgets[-1][1].set(producto)

            # Load initial temperature and combustion performance
            adiabatic_module_instance.initial_temp.delete(0, tk.END)
            adiabatic_module_instance.initial_temp.insert(0, tab_0_config["initial_temp"])
            adiabatic_module_instance.temp_Int_step.delete(0, tk.END)
            adiabatic_module_instance.temp_Int_step.insert(0, tab_0_config["temp_Int_step"])
            adiabatic_module_instance.temp_guess.delete(0, tk.END)
            adiabatic_module_instance.temp_guess.insert(0, tab_0_config["temp_guess"])
            adiabatic_module_instance.update_reaction_label()

            # Cargar configuración de tab_1
            engineDesing_module_instance.propellant_selector.set(tab_1_config["propellant"])
            engineDesing_module_instance.grainGeo_selector.set(tab_1_config["geoConfig"])
            engineDesing_module_instance.update_entries(tab_1_config["geoConfig"])

            engineDesing_module_instance.tubular_entries[0].delete(0, tk.END)
            engineDesing_module_instance.tubular_entries[0].insert(0, tab_1_config["tubular_rIn"])
            engineDesing_module_instance.tubular_entries[1].delete(0, tk.END)
            engineDesing_module_instance.tubular_entries[1].insert(0, tab_1_config["tubular_rOut"])
            engineDesing_module_instance.tubular_entries[2].delete(0, tk.END)
            engineDesing_module_instance.tubular_entries[2].insert(0, tab_1_config["tubular_rt"])
            engineDesing_module_instance.tubular_entries[3].delete(0, tk.END)
            engineDesing_module_instance.tubular_entries[3].insert(0, tab_1_config["tubular_lComb"])
            engineDesing_module_instance.tubular_entries[4].delete(0, tk.END)
            engineDesing_module_instance.tubular_entries[4].insert(0, tab_1_config["tubular_P0"])
            engineDesing_module_instance.tubular_entries[5].delete(0, tk.END)
            engineDesing_module_instance.tubular_entries[5].insert(0, tab_1_config["tubular_dr"])
            engineDesing_module_instance.update_plot()

        except FileNotFoundError:
            print("No previous configuration found. Starting with default values.")
        except Exception as e:
            print(f"Error loading configuration: {e}")


def change_appearance_mode(mode):
    ctk.set_appearance_mode(mode)


def on_closing():
    global closing
    if not closing:
        closing = True
        answer = messagebox.askyesno("Guardar", "¿Deseas guardar la configuración antes de salir?")
        if answer:
            save_configuration()
        clear_dir_path()
        main_frame.after(100, main_frame.quit)  # Usar after para permitir que se completen las tareas pendientes
        main_frame.quit()


# Inicializar la aplicación
main_frame = ctk.CTk()
main_frame.geometry("1920x1080")
main_frame.title("Display de la Reacción")

# Diccionario para guardar las pestañas
tabs_content = {}
adiabatic_module_instance = None

# Crear el menú usando tkinter
menu = tk.Menu(main_frame)
main_frame.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Archivo", menu=file_menu)
file_menu.add_command(label="Abrir", command=open_directory)
file_menu.add_command(label="Guardar", command=save_configuration)
file_menu.add_separator()
file_menu.add_command(label="Salir", command=on_closing)

preferences_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Preferencias", menu=preferences_menu)

preferences_menu.add_command(label="Modo Oscuro", command=lambda: change_appearance_mode("dark"))
preferences_menu.add_command(label="Modo Claro", command=lambda: change_appearance_mode("light"))

database_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Base de Datos", menu=database_menu)
database_menu.add_command(label="Termoquímica", command=lambda: TermoquimicaWindow(main_frame))
database_menu.add_command(label="Propelentes", command=lambda: PropellantWindow(main_frame))

# Crear el marco izquierdo para los botones
tabs_frame = ctk.CTkFrame(main_frame)
tabs_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Crear el marco derecho para el contenido dinámico
content_frame = ctk.CTkFrame(main_frame)
content_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Configurar pesos para el grid
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

# Función para cambiar el contenido
def change_tab(tab_name):
    for tab in tabs_content.values():
        tab.pack_forget()
    tabs_content[tab_name].pack(expand=True, fill="both")


# Crear contenido para las pestañas
tabs_content["tab_0"] = ctk.CTkFrame(content_frame)
adiabatic_module_instance = AdiabaticTempModule(tabs_content["tab_0"])

tabs_content["tab_1"] = ctk.CTkFrame(content_frame)
engineDesing_module_instance = PropellantDesignModule(tabs_content["tab_1"])

tabs_content["tab_2"] = ctk.CTkFrame(content_frame)
nozzleDesing_module_instance = NozzleDesingModule(tabs_content["tab_2"])


# Crear botones para las pestañas
tabsList = [
    ("Adiabatic Flame\n Temperature", "tab_0"),
    ("Engine Design", "tab_1"),
    ("Nozzle Desing", "tab_2")
]

for tab, tag in tabsList:
    ctk.CTkButton(tabs_frame, text=tab, command=lambda tag=tag: change_tab(tag)).pack(pady=10, padx=10, fill="x")

# Mostrar el contenido de la primera pestaña por defecto
change_tab(tabsList[0][1])

# Vincular la función de guardado al evento de cierre de la ventana
main_frame.protocol("WM_DELETE_WINDOW", on_closing)

# Ejecutar la aplicación
main_frame.mainloop()
