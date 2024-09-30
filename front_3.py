from imports import *
from functions import *

from back_0 import *
from back_1 import *

class PropellantDesignModule:
    def __init__(self, content_frame):

        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=15)
        self.content_frame.grid_rowconfigure(1, weight=6)
        self.content_frame.grid_rowconfigure(2, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=6)

        self.image_label = None

        self.grainClasses = {
            "Tubular": TubularGrain,
            "End-Burner": EndBurnerGrain
        }

        # Crear frames dentro de content_frame
        self.inputs_frame = ctk.CTkFrame(self.content_frame, height=350)
        self.inputs_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.inputs_frame.grid_columnconfigure(0, weight=1)
        self.inputs_frame.grid_columnconfigure(1, weight=1)
        self.inputs_frame.grid_columnconfigure(2, weight=4)
        self.inputs_frame.grid_rowconfigure(0, weight=1)
        self.inputs_frame.grid_rowconfigure(1, weight=1)
        self.inputs_frame.grid_rowconfigure(2, weight=1)
        self.inputs_frame.grid_rowconfigure(3, weight=1)
        self.inputs_frame.grid_rowconfigure(4, weight=1)
        self.inputs_frame.grid_propagate(False)

        #self.inputsLabel = ctk.CTkLabel(self.inputs_frame, text="Inputs")
        #self.inputsLabel.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        
        # Obtener los propelentes iniciales y configurar el OptionMenu
        self.get_propellants()
        self.propellant_label = ctk.CTkLabel(self.inputs_frame, text="Propelente")
        self.propellant_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.propellant_selector = ctk.CTkOptionMenu(self.inputs_frame, values=self.propellants)
        self.propellant_selector.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.propellant_selector.bind("<Enter>", self.update_propellant_menu)

        grains = ["Tubular", "End-Burner"]
        self.grainGeo_label = ctk.CTkLabel(self.inputs_frame, text="Geometría del grano")
        self.grainGeo_label.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.grainGeo_selector = ctk.CTkOptionMenu(self.inputs_frame, values=grains, command=self.update_entries)
        self.grainGeo_selector.grid(row=1, column=1, padx=(5, 10), pady=10, sticky="nsew")

        self.subInputsFrame = ctk.CTkScrollableFrame(self.inputs_frame)
        self.subInputsFrame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")


        self.ambientPressureEntry = ctk.CTkLabel(self.inputs_frame, text="Presión Ambiente (Pa):")
        self.ambientPressureEntry.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.ambientPressureEntry = ctk.CTkEntry(self.inputs_frame)
        self.ambientPressureEntry.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.timeStepEntry = ctk.CTkLabel(self.inputs_frame, text="Paso temporal (s):")
        self.timeStepEntry.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.timeStepEntry = ctk.CTkEntry(self.inputs_frame)
        self.timeStepEntry.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")
        

        # Crear un Tabview
        self.inputImageTabview = ctk.CTkTabview(self.inputs_frame)
        self.inputImageTabview.grid(row=0, column=2, rowspan=5, padx=10, pady=10, sticky="nsew")

        # Añadir dos pestañas al Tabview
        self.inputImage_frontSection = self.inputImageTabview.add("Sección Frontal")
        self.inputImage_profileSection = self.inputImageTabview.add("Sección Lateral")

        self.inputImageTabview.tab("Sección Frontal").grid_columnconfigure(0, weight=1)
        self.inputImageTabview.tab("Sección Frontal").grid_rowconfigure(0, weight=1)

        self.inputImageTabview.tab("Sección Lateral").grid_columnconfigure(0, weight=1)
        self.inputImageTabview.tab("Sección Lateral").grid_rowconfigure(0, weight=1)


        # Frame en la primera pestaña
        self.inputImageFrame1 = ctk.CTkFrame(self.inputImage_frontSection)
        self.inputImageFrame1.grid(row=0, column=0, rowspan=5, padx=10, pady=10, sticky="nsew")
        self.inputImageFrame1.grid_propagate(False)
        self.inputImageFrame1.configure(fg_color="white")
        self.inputImageFrame1.bind("<Button-1>", self.update_plot)

        # Frame en la segunda pestaña
        self.inputImageFrame2 = ctk.CTkFrame(self.inputImage_profileSection)
        self.inputImageFrame2.grid(row=0, column=0, rowspan=5, padx=10, pady=10, sticky="nsew")
        self.inputImageFrame2.grid_propagate(False)
        self.inputImageFrame2.configure(fg_color="white")
        self.inputImageFrame2.bind("<Button-1>", self.update_plot)


        #self.inputImageFrame = ctk.CTkFrame(self.inputs_frame)
        #self.inputImageFrame.grid(row=0, column=2, rowspan=5, padx=10, pady=10, sticky="nsew")
        #self.inputImageFrame.grid_propagate(False)
        #self.inputImageFrame.configure(fg_color="white")
        #self.inputImageFrame.bind("<Button-1>", self.update_plot)



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
        self.outputs_frame.grid_columnconfigure(2, weight=1)
        self.outputs_frame.grid_columnconfigure(3, weight=1)


        self.outputs_label = ctk.CTkLabel(self.outputs_frame, text="Resultados Numéricos")
        self.outputs_label.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        

        self.meanPressure_label = ctk.CTkLabel(self.outputs_frame, text="Presión Media (Pa):")
        self.meanPressure_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.meanPressure_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.meanPressure_entry.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.maxPressure_label = ctk.CTkLabel(self.outputs_frame, text="Presión Máxima (Pa):")
        self.maxPressure_label.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.maxPressure_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.maxPressure_entry.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.minPressure_label = ctk.CTkLabel(self.outputs_frame, text="Presión Mínima (Pa):")
        self.minPressure_label.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.minPressure_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.minPressure_entry.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.totalTime_label = ctk.CTkLabel(self.outputs_frame, text="Tiempo total de combustión (s): ")
        self.totalTime_label.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.totalTime_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.totalTime_entry.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

        
        self.meanMassFlow_label = ctk.CTkLabel(self.outputs_frame, text="Flujo másico medio (kg/s):")
        self.meanMassFlow_label.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        self.meanMassFlow_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.meanMassFlow_entry.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")

        self.maxMassFlow_label = ctk.CTkLabel(self.outputs_frame, text="Flujo másico máximo (kg/s):")
        self.maxMassFlow_label.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")
        self.maxMassFlow_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.maxMassFlow_entry.grid(row=2, column=3, padx=10, pady=10, sticky="nsew")

        self.minMassFlow_label = ctk.CTkLabel(self.outputs_frame, text="Flujo másico mínimo (kg/s):")
        self.minMassFlow_label.grid(row=3, column=2, padx=10, pady=10, sticky="nsew")
        self.minMassFlow_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.minMassFlow_entry.grid(row=3, column=3, padx=10, pady=10, sticky="nsew")

        self.totalMass_label = ctk.CTkLabel(self.outputs_frame, text="Masa de propelente quemada (kg):")
        self.totalMass_label.grid(row=4, column=2, padx=10, pady=10, sticky="nsew")
        self.totalMass_entry = ctk.CTkEntry(self.outputs_frame, state="readonly" )
        self.totalMass_entry.grid(row=4, column=3, padx=10, pady=10, sticky="nsew")


        self.tree_frame = ctk.CTkFrame(self.outputs_frame)
        self.tree_frame.grid(row=5, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Tiempo (s)", "Presión (Pa)", "Flujo Másico (kg/s)", "Masa (kg)"), show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=100)

        self.tree_scrollbar = ctk.CTkScrollbar(self.tree_frame, orientation="vertical", command=self.tree.yview)
        self.tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)

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

        self.buttonsFrame = ctk.CTkFrame(self.content_frame, height=5)
        self.buttonsFrame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.buttonsFrame.grid_rowconfigure(0, weight=1)  # Ensure buttons frame rows and columns expand correctly
        self.buttonsFrame.grid_columnconfigure(0, weight=1)
        self.buttonsFrame.grid_columnconfigure(1, weight=1)
        self.buttonsFrame.grid_columnconfigure(2, weight=1)
        self.buttonsFrame.grid_propagate(False)

        self.calcButton = ctk.CTkButton(self.buttonsFrame, text="Calcular combustión", command=self.calculate_n_show)
        self.calcButton.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.exportDataButton = ctk.CTkButton(self.buttonsFrame, text="Exportar Resultados", command=self.export_results)
        self.exportDataButton.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.tubular_widgets = []
        self.end_burner_widgets = []
        self.selection = 'Tubular'  # Initialize selection

        self.create_tubular_entries()
        self.create_end_burner_entries()

    
        self.update_entries("Tubular")

        
        


    def get_inputs(self):

        grain_config = self.grainGeo_selector.get()
        propellant_type = self.propellant_selector.get()
        propellant_type = re.sub(r'\s*\(\d+\)\s*', '', propellant_type)

        if grain_config == 'Tubular':

            rIn_0b  = float(get_entry_value(self.tubular_entries[0]))
            rOut    = float(get_entry_value(self.tubular_entries[1]))
            rt      = float(get_entry_value(self.tubular_entries[2]))
            lComb   = float(get_entry_value(self.tubular_entries[3]))
            geo_Inputs = [rIn_0b, rOut, rt, lComb]   
        
        elif grain_config == 'End-Burner':

            lTube   = float(get_entry_value(self.end_burner_entries[0]))
            lProp   = float(get_entry_value(self.end_burner_entries[1]))
            rOut    = float(get_entry_value(self.end_burner_entries[2]))
            rThrt   = float(get_entry_value(self.end_burner_entries[3]))
            geo_Inputs = [lTube, lProp, rOut, rThrt]  

        P0 = float(get_entry_value(self.ambientPressureEntry))
        delta_t = float(get_entry_value(self.timeStepEntry))

        prop_Inputs = self.get_propellants_props(propellant_type) + [delta_t, P0]
        inputs = geo_Inputs + prop_Inputs

        return grain_config, inputs

    def calculate_n_show(self):

        grain_config, inputs = self.get_inputs()
        tempClass = self.grainClasses[grain_config](inputs)
        tempClass.calcResults()

        pressure_fig = tempClass.pressureGraph()
        massflow_fig = tempClass.massFlowGraph()
        masstime_fig = tempClass.massTimeGraph()

        figs = [pressure_fig, massflow_fig, masstime_fig]
        frames = [self.pressureFrame, self.massFlowFrame, self.massTimeFrame]

        self.graph_labels = [None] * 3

        for i, (fig, frame) in enumerate(zip(figs, frames)):
            insert_fig(fig, frame)

        # Mostrar resultados en los Entry
        self.meanPressure_entry.configure(state="normal")
        self.meanPressure_entry.delete(0, tk.END)
        self.meanPressure_entry.insert(0, tempClass.meanPressure)
        self.meanPressure_entry.configure(state="readonly")

        self.meanMassFlow_entry.configure(state="normal")
        self.meanMassFlow_entry.delete(0, tk.END)
        self.meanMassFlow_entry.insert(0, tempClass.meanMassFlow)
        self.meanMassFlow_entry.configure(state="readonly")

        self.totalTime_entry.configure(state="normal")
        self.totalTime_entry.delete(0, tk.END)
        self.totalTime_entry.insert(0, tempClass.combustion_time)
        self.totalTime_entry.configure(state="readonly")

        self.totalMass_entry.configure(state="normal")
        self.totalMass_entry.delete(0, tk.END)
        self.totalMass_entry.insert(0, tempClass.combustion_mass)
        self.totalMass_entry.configure(state="readonly")

        self.maxPressure_entry.configure(state="normal")
        self.maxPressure_entry.delete(0, tk.END)
        self.maxPressure_entry.insert(0, tempClass.Pmax)
        self.maxPressure_entry.configure(state="readonly")

        self.minPressure_entry.configure(state="normal")
        self.minPressure_entry.delete(0, tk.END)
        self.minPressure_entry.insert(0, tempClass.Pmin)
        self.minPressure_entry.configure(state="readonly")

        self.maxMassFlow_entry.configure(state="normal")
        self.maxMassFlow_entry.delete(0, tk.END)
        self.maxMassFlow_entry.insert(0, tempClass.Gmax)
        self.maxMassFlow_entry.configure(state="readonly")

        self.minMassFlow_entry.configure(state="normal")
        self.minMassFlow_entry.delete(0, tk.END)
        self.minMassFlow_entry.insert(0, tempClass.Gmin)
        self.minMassFlow_entry.configure(state="readonly")

        # Limpiar Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insertar nuevos datos en el Treeview
        tree_data = [tempClass.t, tempClass.P, tempClass.G, tempClass.M]
        decimal_places = len(str(tempClass.delta_t).split('.')[-1])
        for i in range(len(tree_data[0])):  # Asumiendo que todos los vectores tienen la misma longitud
            # Formatear el tiempo con el número de decimales adecuado
            formatted_time = f"{tree_data[0][i]:.{decimal_places}f}"
            row_data = [formatted_time] + [col[i] for col in tree_data[1:]]  # Crear una fila con elementos de cada vector en la misma posición
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

        query = "SELECT Density, a, n, gamma, R, T_ad, P1_min, P1_max, cChar FROM propelente WHERE Propelente = ?"
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
                resultado[7],
                resultado[8]
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
            "Longitud Cámara (m):"
        ]

        for i, label_text in enumerate(labels):
            label = ctk.CTkLabel(self.subInputsFrame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry = ctk.CTkEntry(self.subInputsFrame)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            entry.bind("<FocusOut>", self.update_plot)
            self.tubular_entries.append(entry)
            self.tubular_widgets.append(label)
            self.tubular_widgets.append(entry)

    def create_end_burner_entries(self):
        # Crear entradas específicas para End-Burner

        self.end_burner_entries = []
        labels = [
            "Longitud Cartucho (m):",
            "Longitud Propelente (m):",
            "Radio Cartucho (m):",
            "Radio Garganta (m):"
        ]

        for i, label_text in enumerate(labels):
            label = ctk.CTkLabel(self.subInputsFrame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry = ctk.CTkEntry(self.subInputsFrame)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            entry.bind("<FocusOut>", self.update_plot)
            self.end_burner_entries.append(entry)
            self.end_burner_widgets.append(label)
            self.end_burner_widgets.append(entry)



    

    def update_plot(self, event=None):
        
        grain_config, inputs = self.get_inputs()
        tempClass = self.grainClasses[grain_config](inputs)

        fig_front = tempClass.frontSection_plot()
        fig_profile = tempClass.profileSection_plot()
        insert_fig(fig_front, frame=self.inputImageFrame1, resize='Auto')
        insert_fig(fig_profile, frame=self.inputImageFrame2, resize='Auto')



    

    
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

            # Crear una carpeta llamada "resultados" dentro del directorio de trabajo
            results_folder = os.path.join(working_path, "Engines")
            os.makedirs(results_folder, exist_ok=True)

            # Construir la ruta completa del archivo
            file_path = os.path.join(results_folder, file_name)

            # Recopilar datos a guardar
            tree_data = {
                "Tiempo (s)": [],
                "Presión (Pa)": [],
                "Flujo Másico (kg/s)": [],
                "Masa (kg)": []
            }

            # Guardar datos del Treeview en columnas separadas
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                tree_data["Tiempo (s)"].append(float(values[0]))
                tree_data["Presión (Pa)"].append(float(values[1]))
                tree_data["Flujo Másico (kg/s)"].append(float(values[2]))
                tree_data["Masa (kg)"].append(float(values[3]))
            
            grain_config, inputs = self.get_inputs()

            # Recopilar datos a guardar
            results = {
                "Propellant": re.sub(r'\s*\(\d+\)\s*', '', self.propellant_selector.get()),
                "GrainGeo": grain_config,
                "P0": inputs[-1],
                "meanPressure": float(self.meanPressure_entry.get()),
                "maxPressure": float(self.maxPressure_entry.get()),
                "minPressure": float(self.minPressure_entry.get()),
                "meanMassFlow": float(self.meanMassFlow_entry.get()),
                "maxMassFlow": float(self.maxMassFlow_entry.get()),
                "minMassFlow": float(self.minMassFlow_entry.get()),
                "totalTime": float(self.totalTime_entry.get()),
                "totalMass": float(self.totalMass_entry.get()),
                "tree_data": tree_data
            }

            if grain_config == 'Tubular':
                results["Ri"] = inputs[0]
                results["Re"] = inputs[1]
                results["Rt"] = inputs[2]
                results["Lc"] = inputs[3]
            elif grain_config == 'End-Burner':
                results["Lt"] = inputs[0]
                results["Lp"] = inputs[1]
                results["Re"] = inputs[2]
                results["Rt"] = inputs[3]

            
            # Guardar datos en un archivo JSON
            with open(file_path, 'w') as json_file:
                json.dump(results, json_file, indent=4)
            
            messagebox.showinfo("Guardar archivo", f"Resultados guardados en {file_path}", parent=self.content_frame)