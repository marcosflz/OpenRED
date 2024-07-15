from imports import *
from functions import *

from back_0 import *

class PropellantDesignModule:
    def __init__(self, content_frame):

        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=15)
        self.content_frame.grid_rowconfigure(1, weight=6)
        self.content_frame.grid_rowconfigure(2, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)

        self.image_label = None

        # Crear frames dentro de content_frame
        self.inputs_frame = ctk.CTkFrame(self.content_frame)
        self.inputs_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.inputs_frame.grid_columnconfigure(0, weight=1)
        self.inputs_frame.grid_columnconfigure(1, weight=1)
        self.inputs_frame.grid_columnconfigure(2, weight=4)
        self.inputs_frame.grid_rowconfigure(0, weight=1)
        self.inputs_frame.grid_rowconfigure(1, weight=1)
        self.inputs_frame.grid_rowconfigure(2, weight=1)
        self.inputs_frame.grid_rowconfigure(3, weight=4)
        self.inputs_frame.grid_propagate(False)

        self.inputsLabel = ctk.CTkLabel(self.inputs_frame, text="Inputs")
        self.inputsLabel.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        
        # Obtener los propelentes iniciales y configurar el OptionMenu
        self.get_propellants()
        self.propellant_label = ctk.CTkLabel(self.inputs_frame, text="Propelente")
        self.propellant_label.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.propellant_selector = ctk.CTkOptionMenu(self.inputs_frame, values=self.propellants)
        self.propellant_selector.grid(row=1, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.propellant_selector.bind("<Enter>", self.update_propellant_menu)

        grains = ["Tubular", "End-Burner"]
        self.grainGeo_label = ctk.CTkLabel(self.inputs_frame, text="Geometría del grano")
        self.grainGeo_label.grid(row=2, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.grainGeo_selector = ctk.CTkOptionMenu(self.inputs_frame, values=grains, command=self.update_entries)
        self.grainGeo_selector.grid(row=2, column=1, padx=(5, 10), pady=10, sticky="nsew")

        self.subInputsFrame = ctk.CTkScrollableFrame(self.inputs_frame)
        self.subInputsFrame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        self.inputImageFrame = ctk.CTkFrame(self.inputs_frame)
        self.inputImageFrame.grid(row=1, column=2, rowspan=3, padx=10, pady=10, sticky="nsew")
        self.inputImageFrame.grid_propagate(False)
        self.inputImageFrame.configure(fg_color="white")
        self.inputImageFrame.bind("<Enter>", lambda event: self.update_plot)


        self.outputs_frame = ctk.CTkFrame(self.content_frame)
        self.outputs_frame.grid(row=1, rowspan=2, column=0, padx=10, pady=10, sticky="nsew")
        self.outputs_frame.grid_rowconfigure(0, weight=1)
        self.outputs_frame.grid_rowconfigure(1, weight=1)
        self.outputs_frame.grid_rowconfigure(2, weight=1)
        self.outputs_frame.grid_rowconfigure(3, weight=1)
        self.outputs_frame.grid_rowconfigure(4, weight=1)
        self.outputs_frame.grid_rowconfigure(5, weight=5)
        self.outputs_frame.grid_columnconfigure(0, weight=1)
        self.outputs_frame.grid_columnconfigure(1, weight=1)


        self.outputs_label = ctk.CTkLabel(self.outputs_frame, text="Resultados Numéricos")
        self.outputs_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        

        self.meanPressure_label = ctk.CTkLabel(self.outputs_frame, text="Presión Media (Pa):")
        self.meanPressure_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.meanPressure_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.meanPressure_entry.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.meanMassFlow_label = ctk.CTkLabel(self.outputs_frame, text="Flujo másico medio (kg/s):")
        self.meanMassFlow_label.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.meanMassFlow_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.meanMassFlow_entry.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.totalTime_label = ctk.CTkLabel(self.outputs_frame, text="Tiempo total de combustión (s): ")
        self.totalTime_label.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.totalTime_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.totalTime_entry.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.totalMass_label = ctk.CTkLabel(self.outputs_frame, text="Masa de propelente quemada (kg):")
        self.totalMass_label.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.totalMass_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.totalMass_entry.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

        self.tree_frame = ctk.CTkFrame(self.outputs_frame)
        self.tree_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        # Crear Treeview con Scrollbar
        self.tree_scrollbar = tk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree = ttk.Treeview(self.tree_frame, columns=("Tiempo (s)", "Presión (Pa)", "Flujo Másico (kg/s)", "Masa (kg)"), show="headings", yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.config(command=self.tree.yview)
        self.tree_scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=100)

        self.graphs_frame = ctk.CTkFrame(self.content_frame)
        self.graphs_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.graphs_frame.grid_rowconfigure(0, weight=1)
        self.graphs_frame.grid_rowconfigure(1, weight=1)
        self.graphs_frame.grid_rowconfigure(2, weight=1)
        self.graphs_frame.grid_columnconfigure(0, weight=1)

        self.pressureFrame = ctk.CTkFrame(self.graphs_frame)
        self.pressureFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.pressureFrame.grid_propagate(False)
        self.pressureFrame.configure(fg_color="white")

        self.massFlowFrame = ctk.CTkFrame(self.graphs_frame)
        self.massFlowFrame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.massFlowFrame.grid_propagate(False)
        self.massFlowFrame.configure(fg_color="white")

        self.massTimeFrame = ctk.CTkFrame(self.graphs_frame)
        self.massTimeFrame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.massTimeFrame.grid_propagate(False)
        self.massTimeFrame.configure(fg_color="white")

        self.buttonsFrame = ctk.CTkFrame(self.content_frame)
        self.buttonsFrame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.buttonsFrame.grid_rowconfigure(0, weight=1)  # Ensure buttons frame rows and columns expand correctly
        self.buttonsFrame.grid_columnconfigure(0, weight=1)
        self.buttonsFrame.grid_columnconfigure(1, weight=1)
        self.buttonsFrame.grid_columnconfigure(2, weight=4)

        self.calcButton = ctk.CTkButton(self.buttonsFrame, text="Calcular combustión", command=self.calculate_n_show)
        self.calcButton.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        self.exportDataButton = ctk.CTkButton(self.buttonsFrame, text="Exportar Resultados", command=self.export_results)
        self.exportDataButton.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.tubular_widgets = []
        self.end_burner_widgets = []
        self.selection = 'Tubular'  # Initialize selection

        self.create_tubular_entries()
        self.create_end_burner_entries()

        
        self.update_plot()
        self.update_entries("Tubular")
        


    def calculate_n_show(self):

        grainClasses = {
            "Tubular": TubularGrain
        }

        grain_config = self.grainGeo_selector.get()
        propellant_type = self.propellant_selector.get()

        geo_Inputs = [
            self.rIn_0b,
            self.rOut,
            self.rt,
            self.lComb
            ]

        prop_Inputs = self.get_propellants_props(propellant_type) + [self.delta_r, self.P0]
        inputs = geo_Inputs + prop_Inputs

        combResults = grainClasses[grain_config](inputs)

        pressure_fig = combResults.pressureGraph()
        massflow_fig = combResults.massFlowGraph()
        masstime_fig = combResults.massTimeGraph()

        figs = [pressure_fig, massflow_fig, masstime_fig]
        frames = [self.pressureFrame, self.massFlowFrame, self.massTimeFrame]

        self.graph_labels = [None] * 3

        for i, (fig, frame) in enumerate(zip(figs, frames)):
            # Obtener el tamaño del frame
            frame.update_idletasks()  # Asegurarse de que los tamaños están actualizados
            width, height = frame.winfo_width(), frame.winfo_height()

            # Ajustar el tamaño de la figura
            fig.set_size_inches(width / fig.dpi, height / fig.dpi)

            # Limpiar el canvas antes de dibujar
            for widget in frame.winfo_children():
                widget.destroy()

            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
            plt.close(fig)
            buf.seek(0)
            image = Image.open(buf)

            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(width, height))

            if self.graph_labels[i]:
                self.graph_labels[i].destroy()

            self.graph_labels[i] = ctk.CTkLabel(frame, text="", image=ctk_image)
            self.graph_labels[i].image = ctk_image
            self.graph_labels[i].grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        # Mostrar resultados en los Entry
        self.meanPressure_entry.configure(state="normal")
        self.meanPressure_entry.delete(0, tk.END)
        self.meanPressure_entry.insert(0, combResults.meanPressure)
        self.meanPressure_entry.configure(state="readonly")

        self.meanMassFlow_entry.configure(state="normal")
        self.meanMassFlow_entry.delete(0, tk.END)
        self.meanMassFlow_entry.insert(0, combResults.meanMassFlow)
        self.meanMassFlow_entry.configure(state="readonly")

        self.totalTime_entry.configure(state="normal")
        self.totalTime_entry.delete(0, tk.END)
        self.totalTime_entry.insert(0, combResults.combustion_time)
        self.totalTime_entry.configure(state="readonly")

        self.totalMass_entry.configure(state="normal")
        self.totalMass_entry.delete(0, tk.END)
        self.totalMass_entry.insert(0, combResults.combustion_mass)
        self.totalMass_entry.configure(state="readonly")

        # Limpiar Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insertar nuevos datos en el Treeview
        tree_data = [combResults.t, combResults.P, combResults.G, combResults.M]
        for i in range(len(tree_data[0])):  # Asumiendo que todos los vectores tienen la misma longitud
            row_data = [col[i] for col in tree_data]  # Crear una fila con elementos de cada vector en la misma posición
            self.tree.insert("", "end", values=row_data)

    def get_propellants(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, Propelente FROM propelente")
        results = cursor.fetchall()
        conn.close()
        self.propellants = [f"{row[1]} ({row[0]})" for row in results]


    def update_propellant_menu(self, event=None):
        self.get_propellants()
        self.propellant_selector.configure(values=self.propellants)

    
    def get_propellants_props(self, propellant):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        query = "SELECT Density, a, n, gamma, R, T_ad, P1_min, P1_max FROM propelente WHERE Propelente = ?"
        cursor.execute(query, (propellant,))
        
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            props = [
                resultado[0],
                resultado[1],
                resultado[2],
                resultado[3],
                resultado[4],
                resultado[5],
                resultado[6],
                resultado[7]
            ]
            return props
        else:
            # Retornar None si no se encuentra el propelente
            return None
    
    def update_entries(self, selection):
        self.selection = selection
        # Ocultar todos los widgets actuales
        allWidgets = self.tubular_widgets + self.end_burner_widgets
        for widget in allWidgets:
            widget.grid_forget()

         # Mostrar los widgets seleccionados
        if selection == "Tubular":
            for i, widget in enumerate(self.tubular_widgets):
                row, col = divmod(i, 2)
                widget.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
        elif selection == "End-Burner":
            for i, widget in enumerate(self.end_burner_widgets):
                row, col = divmod(i, 2)
                widget.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")


        # Actualizar el gráfico
        self.update_plot()

    def create_tubular_entries(self):
        # Crear entradas específicas para Tubular
        self.tubular_entries = []
        labels = [
            "Radio Interior (m):",
            "Radio Exterior (m):",
            "Radio Garganta (m):",
            "Longitud Cámara (m):",
            "Presión Ambiental (Pa):",
            "Paso radial (m):"
        ]

        for i, label_text in enumerate(labels):
            label = ctk.CTkLabel(self.subInputsFrame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry = ctk.CTkEntry(self.subInputsFrame)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            entry.bind("<KeyRelease>", self.update_plot)
            self.tubular_entries.append(entry)
            self.tubular_widgets.append(label)
            self.tubular_widgets.append(entry)

    def create_end_burner_entries(self):
        # Crear entradas específicas para End-Burner

        self.end_burner_entries = []
        labels = [
            "End-Burner Param 1:",
            "End-Burner Param 2:",
            "End-Burner Param 3:"
        ]

        for i, label_text in enumerate(labels):
            label = ctk.CTkLabel(self.subInputsFrame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry = ctk.CTkEntry(self.subInputsFrame)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            entry.bind("<KeyRelease>", self.update_plot)
            self.end_burner_entries.append(entry)
            self.end_burner_widgets.append(label)
            self.end_burner_widgets.append(entry)

    def update_plot(self, event=None):
        if self.selection == 'Tubular':
            fig = self.tubular_plot()
        
        # Limpiar el canvas antes de dibujar
        for widget in self.inputImageFrame.winfo_children():
            widget.destroy()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
        plt.close(fig)
        buf.seek(0)
        image = Image.open(buf)

        display_width, display_height = self.inputImageFrame.winfo_width(), self.inputImageFrame.winfo_height()
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(display_height, display_height))

        if self.image_label:
            self.image_label.destroy()

        self.image_label = ctk.CTkLabel(self.inputImageFrame, text="", image=ctk_image)
        self.image_label.image = ctk_image
        pad4x = (display_width-display_height)/2 - 0.05 * (display_width-display_height)/2
        self.image_label.grid(row=0, column=0, padx=(pad4x, pad4x), pady=0, sticky="nsew")

    def tubular_plot(self):
        try:
            self.rIn_0b  = float(get_entry_value(self.tubular_entries[0]))
            self.rOut    = float(get_entry_value(self.tubular_entries[1]))
            self.rt    = float(get_entry_value(self.tubular_entries[2]))
            self.lComb    = float(get_entry_value(self.tubular_entries[3]))
            self.P0    = float(get_entry_value(self.tubular_entries[4]))
            self.delta_r = float(get_entry_value(self.tubular_entries[5]))

            # Crear una figura y un eje
            height = self.inputImageFrame.winfo_height() / 100
            fig, ax = plt.subplots(figsize=(height, height))

            # Dibujar los círculos exteriores e interiores
            outer_circle = plt.Circle((0, 0), self.rOut, color='r', fill=False, label='Outer Radius')
            inner_circle = plt.Circle((0, 0), self.rIn_0b, color='b', fill=False, label='Initial Inner Radius')

            # Añadir los círculos al gráfico
            ax.add_artist(outer_circle)
            ax.add_artist(inner_circle)

            # Rellenar el área entre el círculo interior y exterior
            theta = np.linspace(0, 2 * np.pi, 100)
            x_outer = self.rOut * np.cos(theta)
            y_outer = self.rOut * np.sin(theta)
            x_inner = self.rIn_0b * np.cos(theta)
            y_inner = self.rIn_0b * np.sin(theta)
            ax.fill(np.concatenate([x_outer, x_inner[::-1]]),
                    np.concatenate([y_outer, y_inner[::-1]]),
                    color='gray', alpha=0.5)

            # Definir un conjunto de colores
            colors = ['tab:red', 'tab:blue', 'tab:green']
            num_colors = len(colors)
            # Dibujar las líneas radiales internas
            radii = np.linspace(self.rIn_0b, self.rOut, int(1 / self.delta_r))
            for i, r in enumerate(radii):
                color = colors[i % num_colors]
                #circle = plt.Circle((0, 0), r, color=color, linestyle='-', fill=False)
                #ax.add_artist(circle)

            # Establecer los límites del gráfico
            ax.set_xlim(-self.rOut * 1.1, self.rOut * 1.1)
            ax.set_ylim(-self.rOut * 1.1, self.rOut * 1.1)
            # Establecer el aspecto del gráfico para que sea igual
            ax.set_aspect('equal')
            # Añadir título y leyenda
            ax.set_title(self.selection)
        except Exception:
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()

        return fig
    
    def export_results(self):
        working_path = get_dir_path()
        if not working_path:
            messagebox.showerror("Error", "No se ha seleccionado un directorio de trabajo.", parent=self.content_frame)
            return
        # Preguntar al usuario el nombre del archivo
        file_name = simpledialog.askstring("Guardar archivo", "Introduce el nombre del archivo:", parent=self.content_frame)
        
        if file_name:
            # Asegurarse de que el nombre del archivo termine con '.json'
            if not file_name.endswith('.json'):
                file_name += '.json'
            
            # Construir la ruta completa del archivo
            file_path = os.path.join(working_path, file_name)
            
            # Recopilar datos a guardar
            results = {
            "meanPressure": float(self.meanPressure_entry.get()),
            "meanMassFlow": float(self.meanMassFlow_entry.get()),
            "totalTime": float(self.totalTime_entry.get()),
            "totalMass": float(self.totalMass_entry.get()),
            "tree_data": {
                "Tiempo (s)": [float(self.tree.item(item)["values"][0]) for item in self.tree.get_children()],
                "Presión (Pa)": [float(self.tree.item(item)["values"][1]) for item in self.tree.get_children()],
                "Flujo Másico (kg/s)": [float(self.tree.item(item)["values"][2]) for item in self.tree.get_children()],
                "Masa (kg)": [float(self.tree.item(item)["values"][3]) for item in self.tree.get_children()]
            }
        }

            # Guardar datos del Treeview en columnas separadas
            for item in self.tree.get_children():
                item_values = self.tree.item(item)["values"]
                results["tree_data"]["Tiempo (s)"].append(item_values[0])
                results["tree_data"]["Presión (Pa)"].append(item_values[1])
                results["tree_data"]["Flujo Másico (kg/s)"].append(item_values[2])
                results["tree_data"]["Masa (kg)"].append(item_values[3])
            
            # Guardar datos en un archivo JSON
            with open(file_path, 'w') as json_file:
                json.dump(results, json_file)
            
            messagebox.showinfo("Guardar archivo", f"Resultados guardados en {file_path}", parent=self.content_frame)