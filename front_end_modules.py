from imports import *
from back_end_modules import *
from tkinter import messagebox
import matplotlib.pyplot as plt


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

class AdiabaticTempModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=0)
        self.content_frame.grid_rowconfigure(1, weight=0)  # Row with fixed height
        self.content_frame.grid_rowconfigure(2, weight=1)
        self.content_frame.grid_rowconfigure(3, weight=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(2, weight=1)
        self.content_frame.grid_columnconfigure(3, weight=1)

        self.temp_label = ctk.CTkLabel(content_frame, text="TEMPERATURA ADIABÁTICA DE LLAMA", font=ctk.CTkFont(size=15, weight="bold"))
        self.temp_label.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        self.display_frame = ctk.CTkFrame(content_frame, height=100)
        self.display_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        self.display_frame.grid_propagate(False)  # Prevents frame from resizing itself
        self.display_frame.bind("<Enter>", lambda event: self.update_reaction_label)

        self.reactivo_row = 2
        self.producto_row = 2
        self.reactivos_widgets = []
        self.productos_widgets = []
        self.label = None  # Initialize self.label here

        self.reactivos_frame = ctk.CTkScrollableFrame(content_frame)
        self.reactivos_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.productos_frame = ctk.CTkScrollableFrame(content_frame)
        self.productos_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.results_frame = ctk.CTkFrame(content_frame)
        self.results_frame.grid(row=2, column=2, rowspan=3, columnspan=2, padx=10, pady=10, sticky="nsew")
        

        self.numeric_frame = ctk.CTkFrame(self.results_frame)
        self.numeric_frame.grid(row=0, padx=10, columnspan=2, pady=10, sticky="nsew")
        self.numeric_frame.grid_columnconfigure(0, weight=1)
        self.numeric_frame.grid_columnconfigure(1, weight=1)

        # Agregar el título al results_frame
        self.results_title = ctk.CTkLabel(self.numeric_frame, text="Resultados", font=ctk.CTkFont(size=14, weight="bold"))
        self.results_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="n")

        # Labels para mostrar los resultados
        self.results_labels = {}
        results_texts = [
            "Temperatura de solución (K):",
            "Peso Molecular del Producto (kg/mol):",
            "Capacidad Calorífica a Presion Constante (J/(kg*K)):",
            "Capacidad Calorífica a Volumen Constante (J/(kg*K)):",
            "Constante de los Gases del Producto (J/(kg*K)):",
            "Gamma (Cp/Cv):",
            "Velocidad Característica (m/s):"
        ]

        for i, text in enumerate(results_texts):
            label = ctk.CTkLabel(self.numeric_frame, text=text)
            label.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(self.numeric_frame, state="readonly")
            entry.grid(row=i+1, column=1, padx=10, pady=5, sticky="ew")
            self.results_labels[text] = entry

        self.save_reaction_frame = ctk.CTkFrame(self.results_frame)
        self.save_reaction_frame.grid(row=1, padx=10, columnspan=2, pady=10, sticky="nsew")
        self.save_reaction_frame.grid_columnconfigure(0, weight=1)
        self.save_reaction_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.save_reaction_frame, text='Datos adicionales del Propelente', font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")


        self.propellant_name_label = ctk.CTkLabel(self.save_reaction_frame, text='Nombre del Propelente:')
        self.propellant_name_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.propellant_name = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_name.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.propellant_density_label = ctk.CTkLabel(self.save_reaction_frame, text='Densidad Propelente (kg/m^3):')
        self.propellant_density_label.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        self.propellant_density = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_density.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")

    

        self.propellant_P1_min_label = ctk.CTkLabel(self.save_reaction_frame, text='P1 (Min. - Pa):')
        self.propellant_P1_min_label.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.propellant_P1_min = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_P1_min.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.propellant_P1_max_label = ctk.CTkLabel(self.save_reaction_frame, text='P1 (Max. - Pa):')
        self.propellant_P1_max_label.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")

        self.propellant_P1_max = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_P1_max.grid(row=2, column=3, padx=10, pady=10, sticky="nsew")

        self.propellant_a_label = ctk.CTkLabel(self.save_reaction_frame, text='Coeficiente a:')
        self.propellant_a_label.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

        self.propellant_a = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_a.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.propellant_n_label = ctk.CTkLabel(self.save_reaction_frame, text='Coeficiente n:')
        self.propellant_n_label.grid(row=3, column=2, padx=10, pady=10, sticky="nsew")

        self.propellant_n = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_n.grid(row=3, column=3, padx=10, pady=10, sticky="nsew")

        
        self.propellant_button = ctk.CTkButton(self.save_reaction_frame, text='Añadir Propelente', command=self.save_propellant)
        self.propellant_button.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    
        # Configurar Treeview en save_reaction_frame
        self.tree_frame = ctk.CTkScrollableFrame(self.results_frame, orientation='horizontal')
        self.tree_frame.grid(row=2, column=0, rowspan=2, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.bind("<Enter>", lambda event: self.populate_treeview())

        self.tree = ttk.Treeview(self.tree_frame, columns=("id", "Propelente", "T_ad", "MolWeight", "Cp", "Cv", "R", "gamma", "cChar", "Density", "P1_min", "P1_max","a", "n"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")

        # Poblar Treeview con datos de la base de datos
        self.populate_treeview()

        self.inletTemp_frame = ctk.CTkFrame(content_frame)
        self.inletTemp_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

        self.intStep_frame = ctk.CTkFrame(content_frame)
        self.intStep_frame.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.seedTemp_frame = ctk.CTkFrame(content_frame)
        self.seedTemp_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

        self.calcButton_frame = ctk.CTkFrame(content_frame)
        self.calcButton_frame.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

        self.initial_temp = ctk.CTkEntry(self.inletTemp_frame)
        self.initial_temp.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.initial_temp.bind("<KeyRelease>", self.update_reaction_label)

        self.temp_Int_step = ctk.CTkEntry(self.intStep_frame)
        self.temp_Int_step.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.temp_Int_step.bind("<KeyRelease>", self.update_reaction_label)

        self.temp_guess = ctk.CTkEntry(self.seedTemp_frame)
        self.temp_guess.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.temp_guess.bind("<KeyRelease>", self.update_reaction_label)

        ctk.CTkLabel(self.reactivos_frame, text="Reactivos", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(self.productos_frame, text="Productos", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="ew")

        ctk.CTkLabel(self.inletTemp_frame, text="Temperatura de Entrada (K):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(self.intStep_frame, text="Paso de Integración (K):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(self.seedTemp_frame, text="Temperatura Inicial (K):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="ew")

        add_reactivo_button = ctk.CTkButton(self.reactivos_frame, text="Añadir Reactivo", command=self.add_reactivo)
        add_reactivo_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        remove_reactivo_button = ctk.CTkButton(self.reactivos_frame, text="Eliminar Reactivo", command=self.remove_reactivo)
        remove_reactivo_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        add_producto_button = ctk.CTkButton(self.productos_frame, text="Añadir Producto", command=self.add_producto)
        add_producto_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        remove_producto_button = ctk.CTkButton(self.productos_frame, text="Eliminar Producto", command=self.remove_producto)
        remove_producto_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        calc_button = ctk.CTkButton(self.calcButton_frame, text="Calcular", command=self.calculate)
        calc_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Configuración para expandir filas y columnas en reactivos_frame y productos_frame
        for i in range(2, self.reactivo_row + 1):
            self.reactivos_frame.grid_rowconfigure(i, weight=1)
        for i in range(2, self.producto_row + 1):
            self.productos_frame.grid_rowconfigure(i, weight=1)

        self.reactivos_frame.grid_columnconfigure(0, weight=1)
        self.reactivos_frame.grid_columnconfigure(1, weight=1)

        self.productos_frame.grid_columnconfigure(0, weight=1)
        self.productos_frame.grid_columnconfigure(1, weight=1)

        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.results_frame.grid_rowconfigure(2, weight=1)

        self.inletTemp_frame.grid_columnconfigure(0, weight=1)
        self.inletTemp_frame.grid_columnconfigure(1, weight=1)

        self.intStep_frame.grid_columnconfigure(0, weight=1)
        self.intStep_frame.grid_columnconfigure(1, weight=1)

        self.seedTemp_frame.grid_columnconfigure(0, weight=1)
        self.seedTemp_frame.grid_columnconfigure(1, weight=1)

        self.calcButton_frame.grid_columnconfigure(0, weight=1)
        self.calcButton_frame.grid_columnconfigure(1, weight=1)

        self.add_reactivo()
        self.add_producto()

    def save_propellant(self):

        # Abrir la conexión a la base de datos
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Obtener el nombre del propelente
        propellant_name = self.propellant_name.get()

        # Obtener los valores de los entries
        T_ad = self.results_labels["Temperatura de solución (K):"].get()
        Cp = self.results_labels["Capacidad Calorífica a Presion Constante (J/(kg*K)):"].get()
        MolWeight = self.results_labels["Peso Molecular del Producto (kg/mol):"].get()
        Cv = self.results_labels["Capacidad Calorífica a Volumen Constante (J/(kg*K)):"].get()
        R = self.results_labels["Constante de los Gases del Producto (J/(kg*K)):"].get()
        gamma = self.results_labels["Gamma (Cp/Cv):"].get()
        cChar = self.results_labels["Velocidad Característica (m/s):"].get()
        density = self.propellant_density.get()
        a = self.propellant_a.get()
        n = self.propellant_n.get()
        P1min = self.propellant_P1_min.get()
        P1max = self.propellant_P1_max.get()

        # Insertar los datos en la base de datos
        c.execute('''
            INSERT INTO propelente (Propelente, T_ad, Cp, MolWeight, Cv, R, gamma, cChar, Density, P1_min, P1_max, a, n)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (propellant_name, T_ad, Cp, MolWeight, Cv, R, gamma, cChar, density, P1min, P1max, a, n))

        # Confirmar la transacción
        conn.commit()

        # Cerrar la conexión a la base de datos
        conn.close()

        # Actualizar el Treeview
        self.populate_treeview()


    def populate_treeview(self):
        # Conectar a la base de datos
        self.conn = sqlite3.connect('database.db')
        self.c = self.conn.cursor()

        for row in self.tree.get_children():
            self.tree.delete(row)

        # Obtener datos de la tabla propelente
        self.c.execute("SELECT * FROM propelente")
        rows = self.c.fetchall()

        # Insertar datos en el Treeview
        for row in rows:
            self.tree.insert("", "end", values=row)

        # Cerrar la conexión a la base de datos
        self.conn.close()
    
    def calculate(self):
        reactivos = []
        productos = []

        for mole_entry, option_menu in self.reactivos_widgets:
            try:
                mole = float(mole_entry.get())
            except ValueError:
                mole = 0.0
            reactivo = option_menu.get()
            reactivos.append((mole, reactivo))

        for mole_entry, option_menu in self.productos_widgets:
            try:
                mole = float(mole_entry.get())
            except ValueError:
                mole = 0.0
            producto = option_menu.get()
            productos.append((mole, producto))

        try:
            initial_temp = float(self.initial_temp.get())
        except ValueError:
            initial_temp = 0.0

        try:
            temp_step = float(self.temp_Int_step.get())
        except ValueError:
            temp_step = 0.0

        try:
            temp_guess = float(self.temp_guess.get())
        except ValueError:
            temp_guess = 0.0

        self.results = adiabaticTemp_calc(reactivos, productos, initial_temp, temp_guess, temp_step)
        results_texts = [
            "Temperatura de solución (K):",
            "Peso Molecular del Producto (kg/mol):",
            "Capacidad Calorífica a Presion Constante (J/(kg*K)):",
            "Capacidad Calorífica a Volumen Constante (J/(kg*K)):",
            "Constante de los Gases del Producto (J/(kg*K)):",
            "Gamma (Cp/Cv):",
            "Velocidad Característica (m/s):"
        ]

        for text, result in zip(results_texts, self.results):
            self.results_labels[text].configure(state="normal")
            self.results_labels[text].delete(0, "end")
            self.results_labels[text].insert(0, str(result))
            self.results_labels[text].configure(state="readonly")

    def update_reaction_label(self, event=None):
        reactivos = [(entry.get(), option.get()) for entry, option in self.reactivos_widgets]
        productos = [(entry.get(), option.get()) for entry, option in self.productos_widgets]

        reaction_str = " + ".join(f"{mole} {self.latexMap[reactivo]}" for mole, reactivo in reactivos if mole) + r"\longrightarrow" + " + ".join(f"{mole} {self.latexMap[producto]}" for mole, producto in productos if mole)

        width, height = self.display_frame.winfo_width() / 100, self.display_frame.winfo_height() / 100
        fig, ax = plt.subplots(figsize=(width, height))
        fontsize = 20
        fig.patch.set_facecolor('#2b2b2b')

        while True:
            ax.clear()
            ax.text(0.5, 0.5, f"${reaction_str}$", fontsize=fontsize, ha='center', va='center', color='w')
            ax.axis('off')
            fig.canvas.draw()

            bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            text_width, text_height = bbox.width, bbox.height

            if text_width <= width * 0.9 and text_height <= height * 0.9 or fontsize <= 1:
                break

            fontsize -= 1

        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        image = Image.open(buf)

        display_width, display_height = self.display_frame.winfo_width(), self.display_frame.winfo_height()
        image = image.resize((display_width, display_height), Image.LANCZOS)

        radius = 10
        mask = Image.new('L', (display_width, display_height), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), (display_width, display_height)], radius, fill=255)

        rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
        rounded_image.putalpha(mask)

        ctk_image = ctk.CTkImage(light_image=rounded_image, dark_image=rounded_image, size=(display_width, display_height))

        if self.label:
            self.label.destroy()

        self.label = ctk.CTkLabel(self.display_frame, text="", image=ctk_image)
        self.label.image = ctk_image
        self.label.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

    def add_reactivo(self):
        components, self.latexMap = get_database_components()  # Obtén ambos valores

        mole_entry = ctk.CTkEntry(self.reactivos_frame)
        mole_entry.grid(row=self.reactivo_row, column=0, padx=5, pady=5, sticky="ew")
        mole_entry.bind("<KeyRelease>", self.update_reaction_label)
        option_reactivos = ctk.CTkOptionMenu(self.reactivos_frame, values=components, command=lambda x: self.update_reaction_label())
        option_reactivos.grid(row=self.reactivo_row, column=1, padx=5, pady=5, sticky="ew")
        self.reactivos_widgets.append((mole_entry, option_reactivos))
        self.reactivo_row += 1
        self.update_reaction_label()

    def remove_reactivo(self):
        if self.reactivos_widgets:
            mole_entry, option_reactivos = self.reactivos_widgets.pop()
            mole_entry.destroy()
            option_reactivos.destroy()
            self.reactivo_row -= 1
            self.update_reaction_label()

    def add_producto(self):
        components, self.latexMap = get_database_components()  # Obtén ambos valores

        mole_entry = ctk.CTkEntry(self.productos_frame)
        mole_entry.grid(row=self.producto_row, column=0, padx=5, pady=5, sticky="ew")
        mole_entry.bind("<KeyRelease>", self.update_reaction_label)
        option_productos = ctk.CTkOptionMenu(self.productos_frame, values=components, command=lambda x: self.update_reaction_label())
        option_productos.grid(row=self.producto_row, column=1, padx=5, pady=5, sticky="ew")
        self.productos_widgets.append((mole_entry, option_productos))
        self.producto_row += 1
        self.update_reaction_label()

    def remove_producto(self):
        if self.productos_widgets:
            mole_entry, option_productos = self.productos_widgets.pop()
            mole_entry.destroy()
            option_productos.destroy()
            self.producto_row -= 1
            self.update_reaction_label()

class TermoquimicaWindow:
    instance = None  # Variable de clase para rastrear la instancia

    def __init__(self, parent):
        if TermoquimicaWindow.instance is not None:
            # Si ya existe una instancia, mostrar un mensaje y retornar
            messagebox.showinfo("Info", "La ventana de Termoquímica ya está abierta.", parent=parent)
            return
        # Establecer la instancia de la clase
        TermoquimicaWindow.instance = self

        self.conn = sqlite3.connect('database.db')  # Cambiar el nombre del archivo de base de datos
        self.c = self.conn.cursor()

        # Crear tablas si no existen
        # Moved

        self.columnTags = ("id", "Component", "MolWeight", "Hf0 (298K)", "minColdTemp", "maxColdTemp", "minHotTemp", "maxHotTemp",
                      "a1_cold", "a2_cold", "a3_cold", "a4_cold", "a5_cold",
                      "a1_hot", "a2_hot", "a3_hot", "a4_hot", "a5_hot")
        
        self.conn.commit()

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Termoquímica")
        self.window.geometry("1200x600")

        # Asegurarse de que la ventana emergente se mantenga en primer plano
        self.window.transient(parent)
        self.window.grab_set()
        self.window.lift()

        # Asociar el evento de cierre para restablecer la instancia de clase
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Crear la estructura de la nueva ventana
        self.entries_frame = ctk.CTkScrollableFrame(self.window, width=300)
        self.entries_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.buttons_frame = ctk.CTkFrame(self.window)
        self.buttons_frame.grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.list_frame = ctk.CTkScrollableFrame(self.window, orientation='horizontal')
        self.list_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Configurar pesos para el grid
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_columnconfigure(2, weight=1)
        self.window.grid_columnconfigure(3, weight=1)

        self.buttons_frame.grid_rowconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)
        self.buttons_frame.grid_columnconfigure(2, weight=1)

        # Agregar los labels en entries_frame
        ctk.CTkLabel(self.entries_frame, text=f"Datos del Componente").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.labels = [ctk.CTkLabel(self.entries_frame, text=self.columnTags[i]) for i in range(1, len(self.columnTags))]  # Excluir ID
        for i, label in enumerate(self.labels):
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky="ew")

        # Obtener componentes de la base de datos
        self.components = self.get_components()

        # Agregar los elementos en entries_frame
        self.entries = []

        self.combobox_var = tk.StringVar()
        self.combobox = ctk.CTkComboBox(self.entries_frame, values=self.components, variable=self.combobox_var)
        self.combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        #self.combobox.set('Comp.')
        self.combobox_var.trace_add("write", self.fill_entries)  # Añadir el evento
        self.entries.append(self.combobox)


        for i in range(1, len(self.columnTags)-1):
            entry = ctk.CTkEntry(self.entries_frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.validate_entry)
            entry.bind("<KeyRelease>", self.validate_entry)
            self.entries.append(entry)

        # Hacer que el marco se ajuste dinámicamente
        for i in range(len(self.columnTags) - 1):  # Excluir ID
            self.entries_frame.grid_rowconfigure(i, weight=1)
        self.entries_frame.grid_columnconfigure(1, weight=1)

        # Agregar botones en buttons_frame
        ctk.CTkButton(self.buttons_frame, text="Add", command=self.add_record).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Edit", command=self.edit_record).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Delete", command=self.delete_record).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Agregar Treeview en list_frame con barras de desplazamiento
        self.tree = ttk.Treeview(self.list_frame, columns=self.columnTags, show="headings")  # Incluir ID para referencia
        for col in self.columnTags:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=100)

        self.tree.pack(expand=True, fill="both", padx=5, pady=5)
        self.reassign_ids()
        self.update_treeview()

    def validate_entry(self, event):
        entry = event.widget
        value = entry.get()
        corrected_value = value.replace(',', '.')

        # Reemplazar la coma por un punto
        if ',' in value:
            entry.delete(0, tk.END)
            entry.insert(0, corrected_value)
            messagebox.showwarning("Formato de número", "Se ha reemplazado la coma por un punto para mantener el formato numérico.", parent=self.window)

        # Validar la notación científica
        if not validate_scientific_notation(corrected_value):
            entry.configure(fg="red")
        else:
            entry.configure(fg="white")


    def get_clean_component_name(self, component):
        # Elimina números entre paréntesis al final del componente
        return re.sub(r'\(\d+\)$', '', component).strip()

    def on_closing(self):
        # Restablecer la instancia de clase cuando la ventana se cierra
        TermoquimicaWindow.instance = None
        self.window.destroy()

    def get_components(self):
        self.c.execute("SELECT id, Component FROM termoquimica")
        components = [f"{row[1]} ({row[0]})" for row in self.c.fetchall()]
        return components

    def get_entry_value(self, widget):
        if isinstance(widget, ctk.CTkComboBox):
            return widget.get()
        return widget.get() if widget.get() else '0'

    def fill_entries(self, *args):
        # Obtener el componente seleccionado
        selected_component = self.combobox_var.get()

        # Extraer el ID del componente seleccionado
        self.selected_id = selected_component.split('(')[-1].strip(')')

        # Obtener los valores correspondientes de la base de datos
        self.c.execute("SELECT * FROM termoquimica WHERE id=?", (self.selected_id,))
        record = self.c.fetchone()

        if record:
            # Rellenar los campos de entrada con los valores correspondientes
            for i, value in enumerate(record):
                if i < 2:
                    continue  # Saltar el ID ya que está en el combobox
                self.entries[i-1].delete(0, tk.END)
                self.entries[i-1].insert(0, value)

    def validate_component(self, component):
        # Verifica que el componente contiene al menos una letra
        return any(char.isalpha() for char in component)

    def add_record(self):
        component_value = self.get_entry_value(self.entries[0])
        component_value = self.get_clean_component_name(component_value)
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "El componente debe contener al menos una letra.", parent=self.window)
            return

        values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:])
        self.c.execute("INSERT INTO termoquimica (Component, MolWeight, Hf0, minColdTemp, maxColdTemp, minHotTemp, maxHotTemp, "
                       "a1_cold, a2_cold, a3_cold, a4_cold, a5_cold, "
                       "a1_hot, a2_hot, a3_hot, a4_hot, a5_hot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()

    def edit_record(self):
        component_value = self.get_entry_value(self.entries[0])
        component_value = self.get_clean_component_name(component_value)
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "El componente debe contener al menos una letra.", parent=self.window)
            return

        # Verificar que `self.selected_id` esté definido
        if not hasattr(self, 'selected_id'):
            messagebox.showerror("Invalid Operation", "Seleccione un componente para editar.", parent=self.window)
            return

        # Crear la tupla de valores para la actualización
        values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:]) + (self.selected_id,)

        # Ejecutar la sentencia de actualización en la base de datos
        self.c.execute("""UPDATE termoquimica SET 
                          Component=?, MolWeight=?, Hf0=?, minColdTemp=?, maxColdTemp=?, minHotTemp=?, maxHotTemp=?, 
                          a1_cold=?, a2_cold=?, a3_cold=?, a4_cold=?, a5_cold=?, 
                          a1_hot=?, a2_hot=?, a3_hot=?, a4_hot=?, a5_hot=? 
                          WHERE id=?""", values)
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()

    def delete_record(self):
        selected_items = self.tree.selection()
        if selected_items:
            for selected in selected_items:
                item = self.tree.item(selected)
                record_id = item['values'][0]  # Obtener el ID de la fila seleccionada
                self.c.execute("DELETE FROM termoquimica WHERE id=?", (record_id,))
            self.conn.commit()
            self.reassign_ids()
            self.update_treeview()

    def reassign_ids(self):
        # Obtener todos los registros ordenados por el ID actual
        self.c.execute("SELECT * FROM termoquimica ORDER BY id")
        records = self.c.fetchall()

        # Reiniciar el contador de ID
        new_id = 1

        for record in records:
            old_id = record[0]  # El ID actual
            # Actualizar el registro con el nuevo ID
            self.c.execute("""
                UPDATE termoquimica 
                SET id=? 
                WHERE id=?
            """, (new_id, old_id))
            new_id += 1

        self.conn.commit()

    def update_treeview(self):
        # Limpiar el treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insertar datos en el treeview
        self.c.execute("SELECT * FROM termoquimica")
        for row in self.c.fetchall():
            self.tree.insert("", "end", values=row)  # Incluir ID pero no mostrarlo en la interfaz

        # Actualizar valores del combobox
        self.combobox.configure(values=self.get_components())


class PropellantDesignModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=0)
        self.content_frame.grid_rowconfigure(1, weight=0)  # Row with fixed height
        self.content_frame.grid_rowconfigure(2, weight=1)
        self.content_frame.grid_rowconfigure(3, weight=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(2, weight=1)
        self.content_frame.grid_columnconfigure(3, weight=1)

                # Crear frames dentro de content_frame
        self.images_frame = ctk.CTkFrame(content_frame)
        self.images_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.images_frame.grid_columnconfigure(0, weight=1)
        self.images_frame.grid_columnconfigure(1, weight=1)

        self.graphs_frame = ctk.CTkFrame(content_frame)
        self.graphs_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.graphs_frame.grid_columnconfigure(0, weight=1)
        self.graphs_frame.grid_columnconfigure(1, weight=1)

        self.inputs_frame = ctk.CTkFrame(content_frame)
        self.inputs_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.inputs_frame.grid_columnconfigure(0, weight=1)
        self.inputs_frame.grid_columnconfigure(1, weight=1)

        self.outputs_frame = ctk.CTkFrame(content_frame)
        self.outputs_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.outputs_frame.grid_columnconfigure(0, weight=1)
        self.outputs_frame.grid_columnconfigure(1, weight=1)



class PropellantWindow:
    instance = None  # Variable de clase para rastrear la instancia

    def __init__(self, parent):
        if PropellantWindow.instance is not None:
            # Si ya existe una instancia, mostrar un mensaje y retornar
            messagebox.showinfo("Info", "La ventana de Propelente ya está abierta.", parent=parent)
            return
        # Establecer la instancia de la clase
        PropellantWindow.instance = self

        self.conn = sqlite3.connect('database.db')  # Cambiar el nombre del archivo de base de datos
        self.c = self.conn.cursor()

        # Crear tablas si no existen
        # Moved to app

        self.columnTags = ("id", "Propelente", "T_ad", "MolWeight", "Cp", "Cv", "R", "gamma", "cChar", "Density", "P1_min", "P1_max", "a", "n")
        
        self.conn.commit()

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Propelentes")
        self.window.geometry("1200x600")

        # Asegurarse de que la ventana emergente se mantenga en primer plano
        self.window.transient(parent)
        self.window.grab_set()
        self.window.lift()

        # Asociar el evento de cierre para restablecer la instancia de clase
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Crear la estructura de la nueva ventana
        self.entries_frame = ctk.CTkScrollableFrame(self.window, width=350)
        self.entries_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.buttons_frame = ctk.CTkFrame(self.window)
        self.buttons_frame.grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.list_frame = ctk.CTkScrollableFrame(self.window, orientation='horizontal')
        self.list_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Configurar pesos para el grid
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_columnconfigure(2, weight=1)
        self.window.grid_columnconfigure(3, weight=1)

        self.buttons_frame.grid_rowconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)
        self.buttons_frame.grid_columnconfigure(2, weight=1)

        # Agregar los labels en entries_frame
        ctk.CTkLabel(self.entries_frame, text=f"Datos del Propelente").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.labels = [ctk.CTkLabel(self.entries_frame, text=self.columnTags[i]) for i in range(1, len(self.columnTags))]  # Excluir ID
        for i, label in enumerate(self.labels):
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky="ew")

        # Obtener componentes de la base de datos
        self.components = self.get_components()

        # Agregar los elementos en entries_frame
        self.entries = {}

        self.combobox_var = tk.StringVar()
        self.combobox = ctk.CTkComboBox(self.entries_frame, values=self.components, variable=self.combobox_var)
        self.combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        #self.combobox.set('Comp.')
        self.combobox_var.trace_add("write", self.fill_entries)  # Añadir el evento
        self.entries["Propelente"] = self.combobox

        
        # Crear los entries en el entries_frame y almacenarlos en el diccionario
        for i, tag in enumerate(self.columnTags[2:], start=2):  # Excluir "id"
            entry = ctk.CTkEntry(self.entries_frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.validate_entry)
            entry.bind("<KeyRelease>", self.validate_entry)
            self.entries[tag] = entry

        self.burningRateGraph = ctk.CTkButton(self.entries_frame, text="Mostar curva Burning Rate", command=self.display_burning_rate)
        self.burningRateGraph.grid(row=i+1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")


        #for i in range(1, len(self.columnTags)-1):
        #    entry = ctk.CTkEntry(self.entries_frame)
        #    entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="ew")
        #    entry.bind("<FocusOut>", self.validate_entry)
        #    entry.bind("<KeyRelease>", self.validate_entry)
        #    self.entries.append(entry)

        # Hacer que el marco se ajuste dinámicamente
        for i in range(len(self.columnTags) - 1):  # Excluir ID
            self.entries_frame.grid_rowconfigure(i, weight=1)
        self.entries_frame.grid_columnconfigure(1, weight=1)

        # Agregar botones en buttons_frame
        ctk.CTkButton(self.buttons_frame, text="Add", command=self.add_record).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Edit", command=self.edit_record).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Delete", command=self.delete_record).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Agregar Treeview en list_frame con barras de desplazamiento
        self.tree = ttk.Treeview(self.list_frame, columns=self.columnTags, show="headings")  # Incluir ID para referencia
        for col in self.columnTags:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=100)

        self.tree.pack(expand=True, fill="both", padx=5, pady=5)
        self.reassign_ids()
        self.update_treeview()

    def validate_entry(self, event):
        entry = event.widget
        value = entry.get()
        corrected_value = value.replace(',', '.')

        # Reemplazar la coma por un punto
        if ',' in value:
            entry.delete(0, tk.END)
            entry.insert(0, corrected_value)
            messagebox.showwarning("Formato de número", "Se ha reemplazado la coma por un punto para mantener el formato numérico.", parent=self.window)

        # Validar la notación científica
        if not validate_scientific_notation(corrected_value):
            entry.configure(fg="red")
        else:
            entry.configure(fg="white")


    def get_clean_component_name(self, component):
        # Elimina números entre paréntesis al final del componente
        return re.sub(r'\(\d+\)$', '', component).strip()

    def on_closing(self):
        # Restablecer la instancia de clase cuando la ventana se cierra
        PropellantWindow.instance = None
        self.window.destroy()

    def get_components(self):
        self.c.execute("SELECT id, Propelente FROM propelente")
        components = [f"{row[1]} ({row[0]})" for row in self.c.fetchall()]
        return components

    def get_entry_value(self, widget):
        if isinstance(widget, ctk.CTkComboBox):
            return widget.get()
        return widget.get() if widget.get() else '0'

    def fill_entries(self, *args):
        # Obtener el componente seleccionado
        selected_component = self.combobox_var.get()

        # Extraer el ID del componente seleccionado
        self.selected_id = selected_component.split('(')[-1].strip(')')

        # Obtener los valores correspondientes de la base de datos
        self.c.execute("SELECT * FROM propelente WHERE id=?", (self.selected_id,))
        record = self.c.fetchone()

        if record:
            # Rellenar los campos de entrada con los valores correspondientes
            for i, value in enumerate(record):
                if i < 2:
                    continue  # Saltar el ID ya que está en el combobox
                tag = self.columnTags[i]
                self.entries[tag].delete(0, tk.END)
                self.entries[tag].insert(0, value)

    def validate_component(self, component):
        # Verifica que el componente contiene al menos una letra
        return any(char.isalpha() for char in component)

    def add_record(self):
        component_value = self.get_entry_value(self.entries[0])
        component_value = self.get_clean_component_name(component_value)
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "El componente debe contener al menos una letra.", parent=self.window)
            return

        values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:])
        self.c.execute("INSERT INTO propelente (Propelente, T_ad, MolWeight, Cp, Cv, R, gamma, cChar, Density, P1_min, P1_max, a, n)"
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()

    def edit_record(self):
        
        component_value = self.get_entry_value(self.entries[self.columnTags[1]])
        component_value = self.get_clean_component_name(component_value)
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "El componente debe contener al menos una letra.", parent=self.window)
            return

        # Verificar que `self.selected_id` esté definido
        if not hasattr(self, 'selected_id'):
            messagebox.showerror("Invalid Operation", "Seleccione un componente para editar.", parent=self.window)
            return

        # Crear la tupla de valores para la actualización
        # values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:]) + (self.selected_id,)
        values = (component_value,) + tuple(self.get_entry_value(self.entries[tag]) for tag in self.columnTags[2:]) + (self.selected_id,)

        # Ejecutar la sentencia de actualización en la base de datos
        self.c.execute("""UPDATE propelente SET 
                          Propelente=?, T_ad=?, MolWeight=?, Cp=?, Cv=?, R=?, gamma=?, cChar=?, Density=?, P1_min=?, P1_max=?, a=?, n=?
                          WHERE id=?""", values)
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()

    def delete_record(self):
        selected_items = self.tree.selection()
        if selected_items:
            for selected in selected_items:
                item = self.tree.item(selected)
                record_id = item['values'][0]  # Obtener el ID de la fila seleccionada
                self.c.execute("DELETE FROM propelente WHERE id=?", (record_id,))
            self.conn.commit()
            self.reassign_ids()
            self.update_treeview()

    def reassign_ids(self):
        # Obtener todos los registros ordenados por el ID actual
        self.c.execute("SELECT * FROM propelente ORDER BY id")
        records = self.c.fetchall()

        # Reiniciar el contador de ID
        new_id = 1

        for record in records:
            old_id = record[0]  # El ID actual
            # Actualizar el registro con el nuevo ID
            self.c.execute("""
                UPDATE propelente 
                SET id=? 
                WHERE id=?
            """, (new_id, old_id))
            new_id += 1

        self.conn.commit()

    def update_treeview(self):
        # Limpiar el treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insertar datos en el treeview
        self.c.execute("SELECT * FROM propelente")
        for row in self.c.fetchall():
            self.tree.insert("", "end", values=row)  # Incluir ID pero no mostrarlo en la interfaz

        # Actualizar valores del combobox
        self.combobox.configure(values=self.get_components())

    def display_burning_rate(self):
        try:
            name = self.combobox_var.get()
            a = float(self.entries["a"].get())
            n = float(self.entries["n"].get())
            P1_min = float(self.entries["P1_min"].get())
            P1_max = float(self.entries["P1_max"].get())
        except ValueError:
            messagebox.showwarning("Aviso", "Por favor, ingrese valores válidos.")
            return

        def r(P1, aCoef = a, nCoef = n):
            return a * P1 ** n
        
        Pvalues = np.linspace(P1_min, P1_max, 1000)
        rValues = r(Pvalues)
    

        # Crear el gráfico y guardarlo en un buffer
        fig, ax = plt.subplots()
        ax.plot(Pvalues, rValues)
        ax.set_xlabel(r'Chamber Pressure $P_1$ ($Pa$)')
        ax.set_ylabel(r'Burning Rate $r$ ($cm/s$)')
        ax.grid(True)
        ax.set_title(f'Propelente: {name}')

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        image = Image.open(buf)

        # Crear una nueva ventana para mostrar la imagen
        plot_window = ctk.CTkToplevel(self.window)
        plot_window.title("Tasa de Combustión")

        # Asegurarse de que la ventana emergente se mantenga en primer plano
        plot_window.transient(self.window)
        plot_window.grab_set()
        plot_window.lift()

        # Mostrar la imagen en la nueva ventana usando CTkImage
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
        img_label = ctk.CTkLabel(plot_window, image=ctk_image)
        img_label.image = ctk_image  # Mantener una referencia a la imagen
        img_label.pack(fill=tk.BOTH, expand=True)



