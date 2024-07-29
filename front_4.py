from imports import *
from functions import *

from back_0 import *
from back_1 import *
from back_2 import *

class NozzleDesingModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=20)
        self.content_frame.grid_rowconfigure(2, weight=20)
        self.content_frame.grid_rowconfigure(3, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=2)

        self.image_label = None
        self.updateIteration = 0

        self.inputs_frame = ctk.CTkFrame(self.content_frame)
        self.inputs_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.inputs_frame.grid_rowconfigure(0,weight=1)
        self.inputs_frame.grid_rowconfigure(1,weight=1)
        self.inputs_frame.grid_rowconfigure(2,weight=1)
        self.inputs_frame.grid_rowconfigure(3,weight=1)
        self.inputs_frame.grid_rowconfigure(4,weight=1)
        self.inputs_frame.grid_rowconfigure(5,weight=1)
        self.inputs_frame.grid_rowconfigure(6,weight=1)
        self.inputs_frame.grid_columnconfigure(0,weight=1)
        self.inputs_frame.grid_columnconfigure(1,weight=1)
        self.inputs_frame.grid_columnconfigure(2,weight=15)


        self.inputsLabel = ctk.CTkLabel(self.inputs_frame, text="Inputs")
        self.inputsLabel.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='nswe')

        

        self.load_file_button = ctk.CTkButton(self.inputs_frame, text="Cargar Motor", command=self.get_engine_data)
        self.load_file_button.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        
        self.file_path_label = ctk.CTkLabel(self.inputs_frame, text="No se ha cargado ningún archivo")
        self.file_path_label.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')

        self.pressureCheck_Box = ctk.CTkSwitch(self.inputs_frame, text="P1 - Media", command=self.toggle_slider, state="disabled")
        self.pressureCheck_Box.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')

        self.pressureSlide_Bar = ctk.CTkSlider(self.inputs_frame, from_=0, to=100, command=self.update_entry)
        self.pressureSlide_Bar.grid(row=2, column=1, padx=10, pady=10, sticky='nswe')
        self.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")

        self.pressure_label = ctk.CTkLabel(self.inputs_frame, text="P1 - Punto Diseño (Pa): ")
        self.pressure_label.grid(row=3, column=0, padx=10, pady=10, sticky='nswe')
        self.pressure_entry = ctk.CTkEntry(self.inputs_frame)
        self.pressure_entry.grid(row=3, column=1, padx=10, pady=10, sticky='nswe')
        self.pressure_entry.bind("<Return>", self.update_from_entry)

        self.nPoints_label = ctk.CTkLabel(self.inputs_frame, text="Puntos - Resolución: ")
        self.nPoints_label.grid(row=4, column=0, padx=10, pady=10, sticky='nswe')
        self.nPoints_entry = ctk.CTkEntry(self.inputs_frame)
        self.nPoints_entry.grid(row=4, column=1, padx=10, pady=10, sticky='nswe')

        nozzles = ["TOPN-BN", "MOC-2D"]
        self.nozzleTypeMenu = ctk.CTkOptionMenu(self.inputs_frame, values=nozzles, command=self.update_options)
        self.nozzleTypeMenu.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')

        self.nozzleOptions = ctk.CTkScrollableFrame(self.inputs_frame)
        self.nozzleOptions.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')

        self.pressureGraph_Frame = ctk.CTkFrame(self.inputs_frame)
        self.pressureGraph_Frame.grid(row=1, column=2, rowspan=6, padx=10, pady=10, sticky='nswe')
        self.pressureGraph_Frame.grid_rowconfigure(0, weight=1)
        self.pressureGraph_Frame.configure(fg_color="white")
        self.pressureGraph_Frame.grid_propagate(False)
        self.pressureGraph_Frame.bind("<Enter>", command=self.update_plot)

        


        self.graphs_frame = ctk.CTkFrame(self.content_frame)
        self.graphs_frame.grid(row=0, rowspan=3, column=1, padx=10, pady=10, sticky='nswe')
        self.graphs_frame.grid_columnconfigure(0, weight=1)
        self.graphs_frame.grid_rowconfigure(0, weight=1)

        self.resultsTabs = ctk.CTkTabview(self.graphs_frame)
        self.resultsTabs.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.resultsTabs.add("Características") 
        self.resultsTabs.add("Puntos de Operación") 



        self.characteristics_frame = ctk.CTkFrame(self.resultsTabs.tab("Características"))
        self.characteristics_frame.pack(fill="both", expand=True)
        self.characteristics_frame.grid_propagate(False)
        self.characteristics_frame.grid_columnconfigure(0, weight=1)
        self.characteristics_frame.grid_rowconfigure(0, weight=1)
        self.characteristics_frame.grid_rowconfigure(1, weight=1)
        self.characteristics_frame.grid_rowconfigure(2, weight=1)

        self.thrustGraph_frame = ctk.CTkFrame(self.characteristics_frame)
        self.thrustGraph_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.thrustGraph_frame.configure(fg_color='white')

        self.thrustCoefGraph_frame = ctk.CTkFrame(self.characteristics_frame)
        self.thrustCoefGraph_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.thrustCoefGraph_frame.configure(fg_color='white')

        self.nozzleMapGraph_frame = ctk.CTkFrame(self.characteristics_frame)
        self.nozzleMapGraph_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')
        self.nozzleMapGraph_frame.configure(fg_color='white')



        self.operating_points_frame = ctk.CTkFrame(self.resultsTabs.tab("Puntos de Operación"))
        self.operating_points_frame.pack(fill="both", expand=True)
        self.operating_points_frame.grid_propagate(False)
        self.operating_points_frame.grid_columnconfigure(0, weight=1)
        self.operating_points_frame.grid_rowconfigure(0, weight=8)
        self.operating_points_frame.grid_rowconfigure(1, weight=8)
        self.operating_points_frame.grid_rowconfigure(2, weight=8)
        self.operating_points_frame.grid_rowconfigure(3, weight=1)

        self.presMap_frame = ctk.CTkFrame(self.operating_points_frame)
        self.presMap_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.presMap_frame.configure(fg_color='white')

        self.machMap_frame = ctk.CTkFrame(self.operating_points_frame)
        self.machMap_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.machMap_frame.configure(fg_color='white')

        self.numericFrame = ctk.CTkFrame(self.operating_points_frame)
        self.numericFrame.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')
        self.numericFrame.grid_rowconfigure(0, weight=1)
        self.numericFrame.grid_rowconfigure(1, weight=1)
        self.numericFrame.grid_rowconfigure(2, weight=1)
        self.numericFrame.grid_rowconfigure(3, weight=1)
        self.numericFrame.grid_columnconfigure(0, weight=1)
        self.numericFrame.grid_columnconfigure(1, weight=1)
        self.numericFrame.grid_columnconfigure(2, weight=1)
        self.numericFrame.grid_columnconfigure(3, weight=1)


        self.PR_Crit_0_Label = ctk.CTkLabel(self.numericFrame, text="(P0/P1t) - Choked")
        self.PR_Crit_0_Label.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.PR_Crit_0_Entry = ctk.CTkEntry(self.numericFrame)
        self.PR_Crit_0_Entry.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        self.PR_Crit_1_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - Subsónico")
        self.PR_Crit_1_Label.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.PR_Crit_1_Entry = ctk.CTkEntry(self.numericFrame)
        self.PR_Crit_1_Entry.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')

        self.PR_Crit_2_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - NS Salida")
        self.PR_Crit_2_Label.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')
        self.PR_Crit_2_Entry = ctk.CTkEntry(self.numericFrame)
        self.PR_Crit_2_Entry.grid(row=2, column=1, padx=10, pady=10, sticky='nswe')

        self.PR_Crit_3_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - Optimo")
        self.PR_Crit_3_Label.grid(row=3, column=0, padx=10, pady=10, sticky='nswe')
        self.PR_Crit_3_Entry = ctk.CTkEntry(self.numericFrame)
        self.PR_Crit_3_Entry.grid(row=3, column=1, padx=10, pady=10, sticky='nswe')



        self.PR1_Label = ctk.CTkLabel(self.numericFrame, text="P0/P1t")
        self.PR1_Label.grid(row=0, column=2, padx=10, pady=10, sticky='nswe')
        self.PR1_Entry = ctk.CTkEntry(self.numericFrame)
        self.PR1_Entry.grid(row=0, column=3, padx=10, pady=10, sticky='nswe')

        self.PR2_Label = ctk.CTkLabel(self.numericFrame, text="Pe/P1t")
        self.PR2_Label.grid(row=1, column=2, padx=10, pady=10, sticky='nswe')
        self.PR2_Entry = ctk.CTkEntry(self.numericFrame)
        self.PR2_Entry.grid(row=1, column=3, padx=10, pady=10, sticky='nswe')

        self.PR3_Label = ctk.CTkLabel(self.numericFrame, text="Pe/P0")
        self.PR3_Label.grid(row=2, column=2, padx=10, pady=10, sticky='nswe')
        self.PR3_Entry = ctk.CTkEntry(self.numericFrame)
        self.PR3_Entry.grid(row=2, column=3, padx=10, pady=10, sticky='nswe')

        self.ThrustPerf_Label = ctk.CTkLabel(self.numericFrame, text="T/T(Op)")
        self.ThrustPerf_Label.grid(row=3, column=2, padx=10, pady=10, sticky='nswe')
        self.ThrustPerf_Entry = ctk.CTkEntry(self.numericFrame)
        self.ThrustPerf_Entry.grid(row=3, column=3, padx=10, pady=10, sticky='nswe')



        self.pressureSlider_frame = ctk.CTkFrame(self.operating_points_frame)
        self.pressureSlider_frame.grid(row=3, column=0, padx=10, pady=10, sticky='nswe')
        self.pressureSlider_frame.grid_rowconfigure(0, weight=1)
        self.pressureSlider_frame.grid_columnconfigure(0, weight=1)
        self.pressureSlider_frame.grid_columnconfigure(1, weight=3)
        self.pressureSlider_frame.grid_columnconfigure(2, weight=1)

        self.pressure2_label = ctk.CTkLabel(self.pressureSlider_frame, text="Presión (Pa)")
        self.pressure2_label.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        self.pressureSlider = ctk.CTkSlider(self.pressureSlider_frame, from_=0, to=1)
        self.pressureSlider.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        self.pressure2_entry = ctk.CTkEntry(self.pressureSlider_frame)
        self.pressure2_entry.grid(row=0, column=2, padx=10, pady=10, sticky='nswe')

    

        self.results_frame = ctk.CTkFrame(self.content_frame)
        self.results_frame.grid(row=1, rowspan=3, column=0, padx=10, pady=10, sticky='nswe')
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.results_frame.grid_propagate(False)

        self.numericResults_frame = ctk.CTkScrollableFrame(self.results_frame)
        self.numericResults_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.numericResults_frame.grid_columnconfigure(0, weight=1)
        self.numericResults_frame.grid_columnconfigure(1, weight=1)
        self.numericResults_label = ctk.CTkLabel(self.numericResults_frame, text="Resultados Numéricos")
        self.numericResults_label.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        self.resultsEntries = {}
        data = [
            "DP. Thrust (kg)", "Med. Thrust (kg)", 
            "CF (DP.)", "CF (Med.)",
            "It", "Isp",
            "Vs (DP.)", "Vs (Med.)",
            "Ts (DP.)", "Ts (Med.)",
            "Ps (DP.)", "Ps (Med.)",
            "AR", "MS",
            "Longitud (m)",
            "Rt (m)", "R2 (m)"
            ]
        # Llamar a la función para añadir labels y entries
        self.add_labels_and_entries(self.numericResults_frame, data)
    
  

        # Crear TabView
        self.tabview = ctk.CTkTabview(self.results_frame)
        self.tabview.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        # Añadir pestaña
        self.tabview.add("Resultados")
        self.tabview.add("Geometria")

        # Crear ScrollableFrame y Treeview en la pestaña "Resultados"
        self._create_treeview_in_tab(self.tabview.tab("Resultados"), [("Tiempo (s)", "Empuje (kg)", "CF")])
        
        # Crear ScrollableFrame y Treeview en la pestaña "Geometria"
        self._create_treeview_in_tab(self.tabview.tab("Geometria"), [("X (m)", "Y (m)", "AR")])

    
        self.calcExport_frame = ctk.CTkFrame(self.content_frame)
        self.calcExport_frame.grid(row=3, column=1, padx=10, pady=10, sticky='nswe')
        self.calcExport_frame.grid_columnconfigure(0, weight=1)
        self.calcExport_frame.grid_columnconfigure(1, weight=2)
        self.calcExport_frame.grid_rowconfigure(0, weight=1)

        self.calcButton =  ctk.CTkButton(self.calcExport_frame, text="Calcular Resultados", command=self.calculate_n_show)
        self.calcButton.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        self.exportData =  ctk.CTkButton(self.calcExport_frame, text="Exportar Datos")
        self.exportData.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        

        self.TOPN_widgets = []
        self.MOC2D_widgets = []
        self.selection = 'TOPN-BN'  # Initialize selection

        self.create_TOPN_entries()
        self.create_MOC2D_entries()
        self.update_options('TOPN-BN')

    def start_calculate_n_show(self):
        threading.Thread(target=self.calculate_n_show).start()

    def create_progress_window(self):
        self.progress_window = ctk.CTkToplevel(self.content_frame)
        self.progress_window.title("Progreso")
        
        self.progress_var = ctk.DoubleVar()

        # Frame para la barra de progreso y el porcentaje
        self.progress_frame = ctk.CTkFrame(self.progress_window)
        self.progress_frame.grid(padx=20, pady=20, sticky='nswe')

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

        # Etiqueta de porcentaje
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0%")
        self.progress_label.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        self.progress_frame.grid_columnconfigure(0, weight=1)

        # Calcular el tamaño del progress_frame para ajustar la ventana
        self.progress_frame.update_idletasks()
        frame_width = self.progress_frame.winfo_reqwidth() * 1.4 # Sumar padding
        frame_height = self.progress_frame.winfo_reqheight() * 2  # Sumar padding

        # Calcular el centro de la pantalla
        screen_width = self.progress_window.winfo_screenwidth()
        screen_height = self.progress_window.winfo_screenheight()
        position_top = int(screen_height / 2 - frame_height / 2)
        position_right = int(screen_width / 2 - frame_width / 2)
        
        self.progress_window.geometry(f"{int(frame_width)}x{int(frame_height)}+{position_right}+{position_top}")

        self.progress_window.transient(self.content_frame)
        self.progress_window.grab_set()

        # Manejar el cierre de la ventana de progreso
        self.progress_window.protocol("WM_DELETE_WINDOW", self.on_progress_window_close)


    def on_progress_window_close(self):
        self.calculation_running = False
        self.progress_window.destroy()

    def update_progress(self, progress):
        self.content_frame.after(0, self._update_progress, progress)

    def _update_progress(self, progress):
        self.progress_var.set(progress)
        self.progress_label.configure(text=f"Progreso: {int(progress * 100)}%")
        self.progress_window.update_idletasks()

    def run_TOPBN_loop(self, total_steps):
        for i, P_Off in enumerate(self.calculatedNozzle.P_t):
                if not self.calculation_running:
                    break  # Detener el cálculo si la ventana de progreso se ha cerrado
                
                self.calculatedNozzle.M2_t[i] = self.calculatedNozzle.opPoint_plot(P_Off)["Mach"][-1]
                self.calculatedNozzle.P2_t[i] = P_Off / self.calculatedNozzle.P_ratio(self.calculatedNozzle.M2_t[i])
                self.calculatedNozzle.T2_t[i] = self.calculatedNozzle.T1 / (1 + (self.calculatedNozzle.gamma - 1)/2 * self.calculatedNozzle.M2_t[i]**2)
                self.calculatedNozzle.V2_t[i] = self.calculatedNozzle.M2_t[i] * np.sqrt(self.calculatedNozzle.gamma * self.calculatedNozzle.R * self.calculatedNozzle.T2_t[i])
                
                F1 = self.calculatedNozzle.G_t[i] * self.calculatedNozzle.V2_t[i]
                F2 = self.calculatedNozzle.A2 * (self.calculatedNozzle.P2_t[i] - self.calculatedNozzle.P0)

                self.calculatedNozzle.F_t[i] = F1 + F2
                self.calculatedNozzle.CF_t[i] = self.calculatedNozzle.F_t[i] / (self.calculatedNozzle.At * P_Off)

                # Actualizar la barra de progreso
                progress = (i + 1) / total_steps
                self.update_progress(progress)

    def calculate_n_show(self):
        self.create_progress_window()
        self.progress_var.set(0)
        total_steps = len(self.P)
        self.calculation_running = True

        def run_calculations():
            nozzleClasses = {
                "TOPN-BN": BellNozzle
            }

            engine_config = self.file_path_label.cget("text")
            nozzle_config = self.nozzleTypeMenu.get()
            P1 = float(self.pressure_entry.get())
            n = float(self.nPoints_entry.get())
            defaultState = self.pressureCheck_Box.get()
            specInputs = []

            if nozzle_config == "TOPN-BN":
                nozzleEntries = self.TOPN_entries
                loop_func = self.run_TOPBN_loop

            for entry in nozzleEntries:
                specInputs.append(float(entry.get()))

            self.calculatedNozzle = nozzleClasses[nozzle_config](defaultState, P1, n, engine_config, specInputs)
            loop_func(total_steps)

            # Cerrar la ventana de progreso al completar
            if self.calculation_running:
                self.progress_window.destroy()
                self.calculation_running = False

        threading.Thread(target=run_calculations).start()

    
    def add_labels_and_entries(self, frame, data_list):
        for i, text in enumerate(data_list):
            label = ctk.CTkLabel(frame, text=text)
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky='w')
            entry = ctk.CTkEntry(frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky='we')
            # Guardar la referencia del entry en el diccionario
            self.resultsEntries[text] = entry

    def get_entryResults_values(self):
        # Obtener los valores de los entries guardados en el diccionario
        values = {key: entry.get() for key, entry in self.resultsEntries.items()}
        return values



    def _create_treeview_in_tab(self, tab, columns_list):
        for i, columns in enumerate(columns_list):
            tree_frame = ctk.CTkFrame(tab)
            tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
            tree.grid(row=0, column=0, sticky="nsew")

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=100)

            tree_scrollbar = ctk.CTkScrollbar(tree_frame, orientation="vertical", command=tree.yview)
            tree_scrollbar.grid(row=0, column=1, sticky="ns")
            tree.configure(yscrollcommand=tree_scrollbar.set)

        tab.grid_rowconfigure(len(columns_list) - 1, weight=1)
        tab.grid_columnconfigure(0, weight=1)




    def on_PressureSlide(self, value):
        self.pressure2_entry.delete(0, tk.END)
        self.pressure2_entry.insert(0, str(value))

    def get_engine_data(self, on_load=False, file=None):

        if not on_load:
            file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        else:
            file_path = file

        if file_path:
            file_name = os.path.basename(file_path)

            with open(file_path, 'r') as file:
                self.engine_Data = json.load(file)

            try:
                self.propellant = self.engine_Data["Propellant"]
                self.P0         = self.engine_Data["P0"]
                self.Rt         = self.engine_Data["Rt"]

                self.meanP      = self.engine_Data["meanPressure"]
                self.maxP       = self.engine_Data["maxPressure"]
                self.minP       = self.engine_Data["minPressure"]

                self.meanG      = self.engine_Data["meanMassFlow"]
                self.maxG       = self.engine_Data["maxMassFlow"]
                self.minG       = self.engine_Data["minMassFlow"]
                
                self.mass       = self.engine_Data["totalMass"]
                self.time       = self.engine_Data["totalTime"]

                self.t          = self.engine_Data["tree_data"]["Tiempo (s)"]
                self.P          = self.engine_Data["tree_data"]["Presi\u00f3n (Pa)"]
                self.G          = self.engine_Data["tree_data"]["Flujo M\u00e1sico (kg/s)"]
                self.M          = self.engine_Data["tree_data"]["Masa (kg)"]

                self.file_path_label.configure(text=file_name)
            except Exception:
                messagebox.showerror("Error", "Archivo no válido.", parent=self.content_frame)
                self.file_path_label.configure(text="Archivo Inválido")
                return

            # Actualizar el slider con el valor máximo de la presión
            self.update_slider()
            # Cambiar el switch a activo
            self.pressureCheck_Box.configure(state="normal")
            self.pressureCheck_Box.select()
            self.toggle_slider()

            self.pressureSlider.configure(from_=self.P0, to=self.maxP, state='normal', command=self.on_PressureSlide)
            self.pressureSlider.set(self.P0)
            self.pressure2_entry.delete(0, tk.END)
            self.pressure2_entry.insert(0, str(self.P0))

   
            

    def update_slider(self):
        if self.P:
            self.pressureSlide_Bar.configure(from_= self.minP, to=self.maxP)
            self.pressureSlide_Bar.set(self.meanP)
            self.update_entry()

    def update_entry(self, value=None):
        if self.pressureCheck_Box.get() == 1:
            self.pressure_entry.delete(0, tk.END)
            self.pressure_entry.insert(0, str(self.meanP))
        else:
            self.pressure_entry.delete(0, tk.END)
            self.pressure_entry.insert(0, str(self.pressureSlide_Bar.get()))

        self.update_plot()

    def update_from_entry(self, event):
        try:
            pressure_value = float(self.pressure_entry.get())
            if pressure_value < self.minP or pressure_value > self.maxP:
                messagebox.showerror("Valor introducido inválido", f"El valor debe estar entre {self.minP} y {self.maxP}.")
            else:
                self.pressureSlide_Bar.set(pressure_value)
                self.update_plot()
        except ValueError:
            messagebox.showerror("Valor introducido inválido", "Por favor, introduce un número válido.")

    def toggle_slider(self):
        if self.pressureCheck_Box.get() == 1:
            self.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")
            self.update_entry()
            self.pressure_entry.configure(state="disabled")
            self.pressureSlide_Bar.set(self.meanP)
            
        else:
            self.pressureSlide_Bar.configure(state="normal", button_color="#1F6AA5", button_hover_color="#144870")
            self.update_entry()
            self.pressure_entry.configure(state="normal")
            

    def update_options(self, selection):
        self.selection = selection
        # Ocultar todos los widgets actuales
        allWidgets = self.TOPN_widgets + self.MOC2D_widgets
        for widget in allWidgets:
            widget.grid_forget()

         # Mostrar los widgets seleccionados
        if selection == "TOPN-BN":
            for i, widget in enumerate(self.TOPN_widgets):
                row, col = divmod(i, 2)
                widget.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
        elif selection == "MOC-2D":
            for i, widget in enumerate(self.MOC2D_widgets):
                row, col = divmod(i, 2)
                widget.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
                

    def create_TOPN_entries(self):
        # Crear entradas específicas para Tubular
        self.TOPN_entries = []
        self.TOPN_labels = [
            "K1 (Factor Entrada):",
            "K2 (Factor Garganta):",
            "θₜ (deg):",
            "θₑ (deg):",
            "% (L. Cono):",
            "% (Entrada):"
        ]

        for i, label_text in enumerate(self.TOPN_labels):
            label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry = ctk.CTkEntry(self.nozzleOptions)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            self.TOPN_entries.append(entry)
            self.TOPN_widgets.append(label)
            self.TOPN_widgets.append(entry)

    def create_MOC2D_entries(self):
        # Crear entradas específicas para End-Burner
        self.MOC2D_entries = []
        self.MOC2D_labels = [
            "End-Burner Param 1:",
            "End-Burner Param 2:",
            "End-Burner Param 3:"
        ]

        for i, label_text in enumerate(self.MOC2D_labels):
            label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry = ctk.CTkEntry(self.nozzleOptions)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            self.MOC2D_entries.append(entry)
            self.MOC2D_widgets.append(label)
            self.MOC2D_widgets.append(entry)



    def update_plot(self, event=None):
        try:
            # Crear una figura y un eje
            height, width = self.pressureGraph_Frame.winfo_height() / 100, self.pressureGraph_Frame.winfo_width() / 100
            fig, ax = plt.subplots(figsize=(width, height))

            # Dibujar los círculos exteriores e interiores
            ax.plot(self.t, self.P)


            # Añadir título y etiquetas
            ax.set_title("Pressure Profile (Pa)")
            ax.set_xlabel("Time (s)")
            ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
            ax.set_aspect('auto')

            # Obtener el valor del slider
            pressure_value = float(self.pressure_entry.get())

            # Interpolar el valor del tiempo correspondiente a la presión seleccionada
            interpolate_time = interp1d(self.P, self.t, bounds_error=False, fill_value="extrapolate")
            time_value = interpolate_time(pressure_value)

            # Dibujar el punto rojo
            ax.plot(time_value, pressure_value, 'ro', label="Selected Pressure")
            # Ajustar el aspecto del gráfico para evitar la distorsión
            #ax.set_aspect('equal')
            # Añadir título y leyenda
        except Exception:
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()
        
        # Limpiar el canvas antes de dibujar
        for widget in self.pressureGraph_Frame.winfo_children():
            widget.destroy()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
        plt.close(fig)
        buf.seek(0)
        image = Image.open(buf)

        display_width, display_height = self.pressureGraph_Frame.winfo_width(), self.pressureGraph_Frame.winfo_height()
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(display_width, display_width))

        if self.image_label:
            self.image_label.destroy()

        self.image_label = ctk.CTkLabel(self.pressureGraph_Frame, text="", image=ctk_image)
        self.image_label.image = ctk_image
        pad4x = abs((display_width-display_height)/2 - 0.05 * (display_width-display_height)/2)
        self.image_label.grid(row=0, column=0, padx=0.05, pady=0, sticky="nsew")
