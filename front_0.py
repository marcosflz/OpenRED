from imports import *
from functions import *

from back_0 import *
from back_1 import *

class AdiabaticTempModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=0)  # Row with fixed height
        self.content_frame.grid_rowconfigure(2, weight=1)
        self.content_frame.grid_rowconfigure(3, weight=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(2, weight=1)
        self.content_frame.grid_columnconfigure(3, weight=1)

        #self.temp_label = ctk.CTkLabel(content_frame, text="TEMPERATURA ADIABÁTICA DE LLAMA", font=ctk.CTkFont(size=15, weight="bold"))
        #self.temp_label.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        self.display_frame = ctk.CTkFrame(content_frame, height=100)
        self.display_frame.grid(row=0, column=0, rowspan=2, columnspan=4, padx=10, pady=10, sticky="ew")
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
        self.reassign_ids()


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

        self.reassign_ids()
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

        insert_fig(fig, self.display_frame)

#        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
#
#        buf = io.BytesIO()
#        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
#        plt.close(fig)
#        buf.seek(0)
#        image = Image.open(buf)
#
#        display_width, display_height = self.display_frame.winfo_width(), self.display_frame.winfo_height()
#        image = image.resize((display_width, display_height), Image.LANCZOS)
#
#        radius = 10
#        mask = Image.new('L', (display_width, display_height), 0)
#        draw = ImageDraw.Draw(mask)
#        draw.rounded_rectangle([(0, 0), (display_width, display_height)], radius, fill=255)
#
#        rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
#        rounded_image.putalpha(mask)
#
#        ctk_image = ctk.CTkImage(light_image=rounded_image, dark_image=rounded_image, size=(display_width, display_height))
#
#        if self.label:
#            self.label.destroy()
#
#        self.label = ctk.CTkLabel(self.display_frame, text="", image=ctk_image)
#        self.label.image = ctk_image
#        self.label.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

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

    def reassign_ids(self):
        self.conn = sqlite3.connect('database.db')  # Cambiar el nombre del archivo de base de datos
        self.c = self.conn.cursor()
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