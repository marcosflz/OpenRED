from imports import *
from functions import *

#from back_0 import *
#from back_1 import *

from front_0 import *
from front_1 import *
from front_2 import *
from front_3 import *
from front_4 import *
from front_5 import *
from front_6 import *
from front_7 import *

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
            messagebox.showerror(
                "Error de directorio", "Ya existe un archivo de configuración, por favor selecciona otro directorio.", parent=main_frame)
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
    


    tab_1_config = {
        "propellant": engineDesing_module_instance.propellant_selector.get(),
        "geoConfig": engineDesing_module_instance.grainGeo_selector.get(),
        "P0":       get_entry_value(engineDesing_module_instance.ambientPressureEntry),
        "Rt":       get_entry_value(engineDesing_module_instance.throatRadiEntry),
        "Rc":       get_entry_value(engineDesing_module_instance.caseRadiEntry),
        "Lc":       get_entry_value(engineDesing_module_instance.lCombEntry),
        "dt":       get_entry_value(engineDesing_module_instance.timeStepEntry),
        "dh":       get_entry_value(engineDesing_module_instance.spaceStepEntry),
        "ItMax":    get_entry_value(engineDesing_module_instance.maxItersEntry),
    }
    # Loop over all nozzle types and collect input entries for each type
    for grain_type, entries in engineDesing_module_instance.specInputs_entries.items():
        for entry_name, entry_widget in entries.items():
            tab_1_config[f"{grain_type}_{entry_name}"] = get_entry_value(entry_widget[1])  # The entry widget is in position 1

    # Tab 2 Configuration (Nozzle Design Module)
    tab_2_config = {
        "engine_config": nozzleDesing_module_instance.file_path_label.cget("text"),
        "SwitchState": nozzleDesing_module_instance.pressureCheck_Box.get(),
        "P1": get_entry_value(nozzleDesing_module_instance.pressure_entry),
        "n_res": get_entry_value(nozzleDesing_module_instance.nPoints_entry),
        "nozzle_type": nozzleDesing_module_instance.nozzleTypeMenu.get(),
    }

    # Loop over all nozzle types and collect input entries for each type
    for nozzle_type, entries in nozzleDesing_module_instance.specInputs_entries.items():
        for entry_name, entry_widget in entries.items():
            tab_2_config[f"{nozzle_type}_{entry_name}"] = get_entry_value(entry_widget[1])  # The entry widget is in position 1

        # Tab 3 Configuration (Engine CAD Design Module)
    try:
        tab_3_config = {
            "NozzleConfig": EngineCADDesing_module_instance.file_name
        }
        # Update with the entries present in the dynamic widgets dict
        tab_3_config.update({
            key: widget.get() if isinstance(widget, (ctk.CTkEntry, ctk.CTkOptionMenu, ctk.CTkCheckBox)) else widget.get() 
            for key, widget in EngineCADDesing_module_instance.widgets_dict.items()
        })
    except Exception as e:
        print(f"Error in Tab 3 configuration: {e}")
        tab_3_config = {"None": None}

    

    # Tab 0 and Tab 1 configurations
    config = {
        "tabs": {
            "tab_0": {
                "reactivos": [(get_entry_value(entry), combo.get()) for entry, combo in adiabatic_module_instance.reactivos_widgets],
                "productos": [(get_entry_value(entry), combo.get()) for entry, combo in adiabatic_module_instance.productos_widgets],
                "initial_temp": get_entry_value(adiabatic_module_instance.initial_temp),
                "temp_Int_step": get_entry_value(adiabatic_module_instance.temp_Int_step),
                "temp_guess": get_entry_value(adiabatic_module_instance.temp_guess)
            },
            "tab_1": tab_1_config,
            "tab_2": tab_2_config,
            "tab_3": tab_3_config
        }
    }

    # Save the configuration to a JSON file
    with open(file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)

    messagebox.showinfo("Guardar archivo", f"Configuración guardada en {file_path}")




def load_configuration(working_path):
    file_path = os.path.join(working_path, "config.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as config_file:
                config = json.load(config_file)

            # Load Tab 0 Configuration
            tab_0_config = config["tabs"]["tab_0"]
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

            for mole, reactivo in tab_0_config["reactivos"]:
                adiabatic_module_instance.add_reactivo()
                adiabatic_module_instance.reactivos_widgets[-1][0].insert(0, mole)
                adiabatic_module_instance.reactivos_widgets[-1][1].set(reactivo)

            for mole, producto in tab_0_config["productos"]:
                adiabatic_module_instance.add_producto()
                adiabatic_module_instance.productos_widgets[-1][0].insert(0, mole)
                adiabatic_module_instance.productos_widgets[-1][1].set(producto)

            adiabatic_module_instance.initial_temp.delete(0, tk.END)
            adiabatic_module_instance.initial_temp.insert(0, tab_0_config["initial_temp"])
            adiabatic_module_instance.temp_Int_step.delete(0, tk.END)
            adiabatic_module_instance.temp_Int_step.insert(0, tab_0_config["temp_Int_step"])
            adiabatic_module_instance.temp_guess.delete(0, tk.END)
            adiabatic_module_instance.temp_guess.insert(0, tab_0_config["temp_guess"])
            adiabatic_module_instance.update_reaction_label()

            # Load Tab 1 Configuration
            tab_1_config = config["tabs"]["tab_1"]
            engineDesing_module_instance.propellant_selector.set(tab_1_config["propellant"])
            engineDesing_module_instance.grainGeo_selector.set(tab_1_config["geoConfig"])
            engineDesing_module_instance.update_options(tab_1_config["geoConfig"])

            engineDesing_module_instance.ambientPressureEntry.delete(0, tk.END)
            engineDesing_module_instance.ambientPressureEntry.insert(0, tab_1_config["P0"])
            engineDesing_module_instance.throatRadiEntry.delete(0, tk.END)
            engineDesing_module_instance.throatRadiEntry.insert(0, tab_1_config["Rt"])
            engineDesing_module_instance.caseRadiEntry.delete(0, tk.END)
            engineDesing_module_instance.caseRadiEntry.insert(0, tab_1_config["Rc"])
            engineDesing_module_instance.lCombEntry.delete(0, tk.END)
            engineDesing_module_instance.lCombEntry.insert(0, tab_1_config["Lc"])
            engineDesing_module_instance.timeStepEntry.delete(0, tk.END)
            engineDesing_module_instance.timeStepEntry.insert(0, tab_1_config["dt"])
            engineDesing_module_instance.spaceStepEntry.delete(0, tk.END)
            engineDesing_module_instance.spaceStepEntry.insert(0, tab_1_config["dh"])
            engineDesing_module_instance.maxItersEntry.delete(0, tk.END)
            engineDesing_module_instance.maxItersEntry.insert(0, tab_1_config["ItMax"])

            # Loop over all nozzle types and load input entries for each type
            for grain_type, entries in engineDesing_module_instance.specInputs_entries.items():
                for entry_name, entry_widget in entries.items():
                    full_key = f"{grain_type}_{entry_name}"
                    if full_key in tab_1_config:
                        entry_widget[1].delete(0, tk.END)
                        entry_widget[1].insert(0, tab_1_config[full_key])

            engineDesing_module_instance.update_plot()


            # Load Tab 2 Configuration (Nozzle Design)
            tab_2_config = config["tabs"]["tab_2"]
            engine_path = os.path.join(working_path, "Engines", tab_2_config["engine_config"])
            nozzleDesing_module_instance.get_engine_data(on_load=True, file=engine_path)
            nozzleDesing_module_instance.pressure_entry.delete(0, tk.END)
            nozzleDesing_module_instance.pressure_entry.insert(0, tab_2_config["P1"])

            if tab_2_config["SwitchState"] == 1:
                nozzleDesing_module_instance.pressureCheck_Box.configure(state="normal")
                nozzleDesing_module_instance.pressureCheck_Box.select()  
                nozzleDesing_module_instance.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")
                nozzleDesing_module_instance.pressure_entry.delete(0, tk.END)
                nozzleDesing_module_instance.pressure_entry.insert(0, str(nozzleDesing_module_instance.meanP))
                nozzleDesing_module_instance.pressure_entry.configure(state="disabled")
                nozzleDesing_module_instance.pressureSlide_Bar.set(nozzleDesing_module_instance.meanP)
            else:
                nozzleDesing_module_instance.pressureCheck_Box.configure(state="normal")
                nozzleDesing_module_instance.pressureCheck_Box.deselect()    
                nozzleDesing_module_instance.pressureSlide_Bar.configure(state="normal", button_color="#1F6AA5", button_hover_color="#144870")
                nozzleDesing_module_instance.pressureSlide_Bar.set(float(tab_2_config["P1"]))
                nozzleDesing_module_instance.pressure_entry.delete(0, tk.END)
                nozzleDesing_module_instance.pressure_entry.insert(0, str(tab_2_config["P1"]))
                nozzleDesing_module_instance.pressure_entry.configure(state="normal")

            nozzleDesing_module_instance.update_plot()
            nozzleDesing_module_instance.nPoints_entry.delete(0, tk.END)
            nozzleDesing_module_instance.nPoints_entry.insert(0, tab_2_config["n_res"])

            # Establecer la selección guardada del OptionMenu
            nozzleDesing_module_instance.nozzleTypeMenu.set(tab_2_config["nozzle_type"])
            nozzleDesing_module_instance.update_options(tab_2_config["nozzle_type"])

            # Loop over all nozzle types and load input entries for each type
            for nozzle_type, entries in nozzleDesing_module_instance.specInputs_entries.items():
                for entry_name, entry_widget in entries.items():
                    full_key = f"{nozzle_type}_{entry_name}"
                    if full_key in tab_2_config:
                        entry_widget[1].delete(0, tk.END)
                        entry_widget[1].insert(0, tab_2_config[full_key])

            # Load Tab 3 Configuration
            tab_3_config = config["tabs"]["tab_3"]
            EngineCADDesing_module_instance.build_entries(on_load=True, file=tab_3_config["NozzleConfig"])
            print('llamada')
            for key, value in tab_3_config.items():
                if key in EngineCADDesing_module_instance.widgets_dict:
                    widget = EngineCADDesing_module_instance.widgets_dict[key]
                    if isinstance(widget, ctk.CTkOptionMenu):
                        widget.set(value)
                    elif isinstance(widget, ctk.CTkEntry):
                        widget.delete(0, tk.END)
                        widget.insert(0, value)
                    elif isinstance(widget, ctk.CTkCheckBox):
                        if value:
                            widget.select()
                        else:
                            widget.deselect()

            EngineCADDesing_module_instance.update_plots()
            TestingBed_module_instance.create_checklist()

        except FileNotFoundError as e:
            print(e)
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
        TestingBed_module_instance.on_close()
        main_frame.after(100, main_frame.quit)  # Usar after para permitir que se completen las tareas pendientes
        main_frame.quit()


# Inicializar la aplicación
main_frame = ctk.CTk()
main_frame.geometry("1920x1080")
main_frame.title("Display de la Reacción")

# Configurar pesos para el grid
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

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


# Crear contenido para las pestañas
tabs_content["tab_0"] = ctk.CTkFrame(content_frame)
adiabatic_module_instance = AdiabaticTempModule(tabs_content["tab_0"])

tabs_content["tab_1"] = ctk.CTkFrame(content_frame)
engineDesing_module_instance = PropellantDesignModule(tabs_content["tab_1"], main_frame)

tabs_content["tab_2"] = ctk.CTkFrame(content_frame)
nozzleDesing_module_instance = NozzleDesingModule(tabs_content["tab_2"])

tabs_content["tab_3"] = ctk.CTkFrame(content_frame)
EngineCADDesing_module_instance = EngineCADModule(tabs_content["tab_3"])

tabs_content["tab_4"] = ctk.CTkFrame(content_frame)
TestingBed_module_instance = TestingBedModule(tabs_content["tab_4"])

tabs_content["tab_5"] = ctk.CTkFrame(content_frame)
CFD_module_instance = CFD_Module(tabs_content["tab_5"])

## Función recursiva para cambiar el color de todos los frames
#def change_color_scheme_recursive(widget, color):
#    if isinstance(widget, ctk.CTkFrame):  # Verifica si el widget es un frame
#        widget.configure(fg_color=color)
#    # Recorre todos los hijos del widget actual (si los tiene)
#    for child in widget.winfo_children():
#        change_color_scheme_recursive(child, color)
#
## Función para cambiar el color de todos los frames dentro de main_frame
#def change_color_scheme(color):
#    change_color_scheme_recursive(main_frame, color)
#
## Agregar la opción de cambiar el color en el menú de preferencias
#preferences_menu.add_command(label="Color Azul", command=lambda: change_color_scheme("#1F6AA5"))
#preferences_menu.add_command(label="Color Rojo", command=lambda: change_color_scheme("#E74C3C"))
#preferences_menu.add_command(label="Color Verde", command=lambda: change_color_scheme("#27AE60"))
#
## Inicializar la aplicación con un color por defecto
#initial_color = "#1F6AA5"
#change_color_scheme(initial_color)


# Diccionario para almacenar referencias a los botones
tab_buttons = {}

# Crear botones para las pestañas
tabsList = [
    ("Adiabatic Flame\n Temperature", "tab_0"),
    ("Engine Design", "tab_1"),
    ("Nozzle Desing", "tab_2"),
    ("CAD Design", "tab_3"),
    ("Test Bed", "tab_4"),
    ("OpenFOAM Maker", "tab_5")
]

# Color cuando un botón está seleccionado y el color por defecto
selected_color = "#3498db"  # Color azul claro
default_color = "#2c3e50"  # Color gris oscuro

# Función para cambiar el color de los botones
def update_button_colors(selected_tag):
    for tag, button in tab_buttons.items():
        if tag == selected_tag:
            button.configure(fg_color=selected_color)  # Cambiar al color seleccionado
        else:
            button.configure(fg_color=default_color)   # Restaurar el color por defecto

# Modificación en la creación de los botones para almacenar referencias
for tab, tag in tabsList:
    button = ctk.CTkButton(tabs_frame, text=tab, command=lambda tag=tag: change_tab(tag))
    button.pack(pady=10, padx=10, fill="x")
    tab_buttons[tag] = button  # Guardar referencia al botón en el diccionario

# Actualizar la función de cambio de pestañas
def change_tab(tab_name):
    for tab in tabs_content.values():
        tab.pack_forget()
    tabs_content[tab_name].pack(expand=True, fill="both")
    update_button_colors(tab_name)  # Cambiar el color del botón seleccionado

# Mostrar el contenido de la primera pestaña por defecto y actualizar el color del botón
change_tab(tabsList[0][1])

# Vincular la función de guardado al evento de cierre de la ventana
main_frame.protocol("WM_DELETE_WINDOW", on_closing)

# Ejecutar la aplicación
main_frame.mainloop()
