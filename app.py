from imports import *
#Hola
# Llamar a la función para inicializar la base de datos al iniciar el programa
back_end_modules.initialize_database()

# Inicializar la aplicación
main_frame = ctk.CTk()
main_frame.geometry("1920x1080")
main_frame.title("Display de la Reacción")

# Diccionario para guardar las pestañas
tabs_content = {}
adiabatic_module_instance = None

# Función para obtener el valor del Entry con un valor por defecto de 0 si está vacío
def get_entry_value(entry):
    return entry.get() if entry.get() else '0'

# Función para guardar la configuración
def save_configuration():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        config = {
            "tabs": {
                "tab_0": {
                    "reactivos": [(get_entry_value(entry), combo.get()) for entry, combo in adiabatic_module_instance.reactivos_widgets],
                    "productos": [(get_entry_value(entry), combo.get()) for entry, combo in adiabatic_module_instance.productos_widgets],
                    "initial_temp": get_entry_value(adiabatic_module_instance.initial_temp),
                    "temp_Int_step": get_entry_value(adiabatic_module_instance.temp_Int_step),
                    "temp_guess": get_entry_value(adiabatic_module_instance.temp_guess)
                }
            }
        }
        with open(file_path, 'w') as config_file:
            json.dump(config, config_file)

# Función para cargar la configuración
def load_configuration():
    file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        try:
            with open(file_path, 'r') as config_file:
                config = json.load(config_file)

            # Restaurar la configuración de las pestañas
            tab_0_config = config["tabs"]["tab_0"]

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

        except FileNotFoundError:
            print("No previous configuration found. Starting with default values.")

# Crear el menú usando tkinter
menu = tk.Menu(main_frame)
main_frame.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Archivo", menu=file_menu)
file_menu.add_command(label="Abrir", command=load_configuration)
file_menu.add_command(label="Guardar", command=save_configuration)
file_menu.add_separator()
file_menu.add_command(label="Salir", command=main_frame.quit)

preferences_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Preferencias", menu=preferences_menu)


database_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Base de Datos", menu=database_menu)
database_menu.add_command(label="Termoquímica", command=lambda: front_end_modules.TermoquimicaWindow(main_frame))
database_menu.add_command(label="Propelentes", command=lambda: front_end_modules.PropellantWindow(main_frame))

# Crear el marco izquierdo para los botones
tabs_frame = ctk.CTkFrame(main_frame)
tabs_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Crear el marco derecho para el contenido dinámico
content_frame = ctk.CTkFrame(main_frame)
content_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Configurar pesos para el grid
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)
content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=1)
content_frame.grid_columnconfigure(2, weight=2)  
content_frame.grid_columnconfigure(3, weight=2)

# Función para cambiar el contenido
def change_tab(tab_name):
    for tab in tabs_content.values():
        tab.pack_forget()
    tabs_content[tab_name].pack(expand=True, fill="both")

# Crear contenido para las pestañas
tabs_content["tab_0"] = ctk.CTkFrame(content_frame)
adiabatic_module_instance = front_end_modules.AdiabaticTempModule(tabs_content["tab_0"])

tabs_content["tab_1"] = ctk.CTkFrame(content_frame)
engineDesing_module_instance = front_end_modules.PropellantDesignModule(tabs_content["tab_1"])

tabs_content["tab_2"] = ctk.CTkLabel(content_frame, text="Contenido de la pestaña 3")

# Crear botones para las pestañas
tabsList = [
    ("Adiabatic Flame\n Temperature", "tab_0"),
    ("Engine Design", "tab_1"),
    ("2", "tab_2")
]

for tab, tag in tabsList:
    ctk.CTkButton(tabs_frame, text=tab, command=lambda tag=tag: change_tab(tag)).pack(pady=10, padx=10, fill="x")

# Mostrar el contenido de la primera pestaña por defecto
change_tab(tabsList[0][1])

# Vincular la función de guardado al evento de cierre de la ventana
main_frame.protocol("WM_DELETE_WINDOW", main_frame.quit)

# Ejecutar la aplicación
main_frame.mainloop()
