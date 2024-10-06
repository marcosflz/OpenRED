from imports import *
from functions import *


class NozzleDesingModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=20)
        self.content_frame.grid_rowconfigure(2, weight=20)
        self.content_frame.grid_rowconfigure(3, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=2)

        self.nozzleClasses = importLibraries(lib='NozzleLibrary')

        self.image_label = None
        self.updateIteration = 0

        self.inputs_frame = ctk.CTkFrame(self.content_frame, height=500, width=600)
        self.inputs_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.inputs_frame.grid_propagate(False)
        self.inputs_frame.grid_rowconfigure(0,weight=1)
        self.inputs_frame.grid_rowconfigure(1,weight=1)
        self.inputs_frame.grid_rowconfigure(2,weight=1)
        self.inputs_frame.grid_rowconfigure(3,weight=1)
        self.inputs_frame.grid_rowconfigure(4,weight=1)
        self.inputs_frame.grid_rowconfigure(5,weight=1)
        self.inputs_frame.grid_rowconfigure(6,weight=1)
        self.inputs_frame.grid_rowconfigure(7,weight=1)
        self.inputs_frame.grid_columnconfigure(0,weight=1)
        self.inputs_frame.grid_columnconfigure(1,weight=1)
        self.inputs_frame.grid_columnconfigure(2,weight=15)


        self.inputsLabel = ctk.CTkLabel(self.inputs_frame, text="Inputs")
        self.inputsLabel.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='nswe')

        inputsPad = 5

        self.load_file_button = ctk.CTkButton(self.inputs_frame, text="Cargar Motor", command=self.get_engine_data)
        self.load_file_button.grid(row=1, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')
        
        self.file_path_label = ctk.CTkLabel(self.inputs_frame, text="No se ha cargado ningún archivo")
        self.file_path_label.grid(row=1, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')

        self.pressureCheck_Box = ctk.CTkSwitch(self.inputs_frame, text="P1 - Media", command=self.toggle_slider, state="disabled")
        self.pressureCheck_Box.grid(row=2, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')

        self.pressureSlide_Bar = ctk.CTkSlider(self.inputs_frame, from_=0, to=100, command=self.update_entry)
        self.pressureSlide_Bar.grid(row=2, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")

        self.pressure_label = ctk.CTkLabel(self.inputs_frame, text="P1 - Punto Diseño (Pa): ")
        self.pressure_label.grid(row=3, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.pressure_entry = ctk.CTkEntry(self.inputs_frame)
        self.pressure_entry.grid(row=3, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.pressure_entry.bind("<Return>", self.update_from_entry)

        self.nPoints_label = ctk.CTkLabel(self.inputs_frame, text="Puntos - Resolución: ")
        self.nPoints_label.grid(row=4, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.nPoints_entry = ctk.CTkEntry(self.inputs_frame)
        self.nPoints_entry.grid(row=4, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')

        self.timeNormalization_label = ctk.CTkLabel(self.inputs_frame, text="Paso Temporal (s): ")
        self.timeNormalization_label.grid(row=5, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.timeNormalization_entry = ctk.CTkEntry(self.inputs_frame)
        self.timeNormalization_entry.grid(row=5, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')

        #nozzles = ["TOPN-BN", "CONE-LN"]
        nozzle_types = list(self.nozzleClasses.keys())
        self.nozzleTypeMenu = ctk.CTkOptionMenu(self.inputs_frame, values=nozzle_types, command=self.update_options)
        self.nozzleTypeMenu.grid(row=6, column=0, columnspan=2, padx=inputsPad, pady=inputsPad, sticky='nswe')

        self.nozzleOptions = ctk.CTkScrollableFrame(self.inputs_frame)
        self.nozzleOptions.grid(row=7, column=0, columnspan=2, padx=inputsPad, pady=inputsPad, sticky='nswe')

        self.pressureGraph_Frame = ctk.CTkFrame(self.inputs_frame)
        self.pressureGraph_Frame.grid(row=1, column=2, rowspan=7, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.pressureGraph_Frame.grid_rowconfigure(0, weight=1)
        self.pressureGraph_Frame.configure(fg_color="white")
        self.pressureGraph_Frame.grid_propagate(False)
        self.pressureGraph_Frame.bind("<Button-1>", self.update_plot)
        

        self.resultsTabs = ctk.CTkTabview(self.content_frame)
        self.resultsTabs.grid(row=0, rowspan=3, column=1, padx=10, pady=10, sticky='nswe')
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
        self.thrustGraph_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.thrustGraph_frame.grid_propagate(False)
        self.thrustGraph_frame.configure(fg_color='white')

        self.thrustCoefGraph_frame = ctk.CTkFrame(self.characteristics_frame)
        self.thrustCoefGraph_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')
        self.thrustCoefGraph_frame.grid_propagate(False)
        self.thrustCoefGraph_frame.configure(fg_color='white')

        self.nozzleGeoGraph_frame = ctk.CTkFrame(self.characteristics_frame)
        self.nozzleGeoGraph_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.nozzleGeoGraph_frame.grid_propagate(False)
        self.nozzleGeoGraph_frame.configure(fg_color='white')



        self.operating_points_frame = ctk.CTkFrame(self.resultsTabs.tab("Puntos de Operación"))
        self.operating_points_frame.pack(fill="both", expand=True)
        self.operating_points_frame.grid_propagate(False)
        self.operating_points_frame.grid_columnconfigure(0, weight=100)
        self.operating_points_frame.grid_columnconfigure(1, weight=1)
        self.operating_points_frame.grid_rowconfigure(0, weight=50)
        self.operating_points_frame.grid_rowconfigure(1, weight=50)
        self.operating_points_frame.grid_rowconfigure(2, weight=1)
        

        self.presMap_frame = ctk.CTkFrame(self.operating_points_frame)
        self.presMap_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.presMap_frame.grid_propagate(False)
        self.presMap_frame.configure(fg_color='white')

        self.machMap_frame = ctk.CTkFrame(self.operating_points_frame)
        self.machMap_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.machMap_frame.grid_propagate(False)
        self.machMap_frame.configure(fg_color='white')

        self.numericFrame = ctk.CTkFrame(self.operating_points_frame, height=50)
        self.numericFrame.grid(row=2, column=0, padx=5, pady=5, sticky='nswe')
        self.numericFrame.grid_rowconfigure(0, weight=1)
        self.numericFrame.grid_rowconfigure(1, weight=1)
        self.numericFrame.grid_rowconfigure(2, weight=1)
        self.numericFrame.grid_rowconfigure(3, weight=1)
        self.numericFrame.grid_columnconfigure(0, weight=10)
        self.numericFrame.grid_columnconfigure(1, weight=10)
        self.numericFrame.grid_columnconfigure(2, weight=10)
        self.numericFrame.grid_columnconfigure(3, weight=10)
        self.numericFrame.grid_columnconfigure(4, weight=1)

        entry_height = 5
        pad = 10

        

        self.PR_Crit_1_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - Subsónico")
        self.PR_Crit_1_Label.grid(row=0, column=0, padx=pad, pady=pad, sticky='nswe')
        self.PR_Crit_1_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR_Crit_1_Entry.grid(row=0, column=1, padx=pad, pady=pad, sticky='nswe')

        self.PR_Crit_2_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - NS Salida")
        self.PR_Crit_2_Label.grid(row=1, column=0, padx=pad, pady=pad, sticky='nswe')
        self.PR_Crit_2_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR_Crit_2_Entry.grid(row=1, column=1, padx=pad, pady=pad, sticky='nswe')

        self.PR_Crit_3_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - Optimo")
        self.PR_Crit_3_Label.grid(row=2, column=0, padx=pad, pady=pad, sticky='nswe')
        self.PR_Crit_3_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR_Crit_3_Entry.grid(row=2, column=1, padx=pad, pady=pad, sticky='nswe')

        self.PR1_Label = ctk.CTkLabel(self.numericFrame, text="P0/P1t (Cap. Exp.)")
        self.PR1_Label.grid(row=0, column=2, padx=pad, pady=pad, sticky='nswe')
        self.PR1_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR1_Entry.grid(row=0, column=3, padx=pad, pady=pad, sticky='nswe')

        self.PR2_Label = ctk.CTkLabel(self.numericFrame, text="Pe/P1t (Salida/Comb.)")
        self.PR2_Label.grid(row=1, column=2, padx=pad, pady=pad, sticky='nswe')
        self.PR2_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR2_Entry.grid(row=1, column=3, padx=pad, pady=pad, sticky='nswe')

        self.PR3_Label = ctk.CTkLabel(self.numericFrame, text="Pe/P0 (Salida/Amb.)")
        self.PR3_Label.grid(row=2, column=2, padx=pad, pady=pad, sticky='nswe')
        self.PR3_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR3_Entry.grid(row=2, column=3, padx=pad, pady=pad, sticky='nswe')


        self.PR_Crit_0_Label = ctk.CTkLabel(self.numericFrame, text="(P0/P1t) - Choked")
        self.PR_Crit_0_Label.grid(row=0, column=4, padx=pad, pady=pad, sticky='nswe')
        self.PR_Crit_0_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR_Crit_0_Entry.grid(row=0, column=5, padx=pad, pady=pad, sticky='nswe')

        self.OperationPoint_Label = ctk.CTkLabel(self.numericFrame, text="Operation:")
        self.OperationPoint_Label.grid(row=1, column=4, padx=pad, pady=pad, sticky='nswe')
        self.OperationPoint_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.OperationPoint_Entry.grid(row=1, column=5, padx=pad, pady=pad, sticky='nswe')

        self.ThrustOff_Label = ctk.CTkLabel(self.numericFrame, text="Operation:")
        self.ThrustOff_Label.grid(row=2, column=4, padx=pad, pady=pad, sticky='nswe')
        self.ThrustOff_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.ThrustOff_Entry.grid(row=2, column=5, padx=pad, pady=pad, sticky='nswe')



        self.pressureSlider_frame = ctk.CTkFrame(self.numericFrame, height=75)  # Set height here
        self.pressureSlider_frame.grid(row=3,column=0, columnspan=6, padx=5, pady=5, sticky='nswe')
        self.pressureSlider_frame.grid_rowconfigure(0, weight=1)
        self.pressureSlider_frame.grid_rowconfigure(1, weight=1)
        self.pressureSlider_frame.grid_columnconfigure(0, weight=1)
        self.pressureSlider_frame.grid_columnconfigure(1, weight=10)
        self.pressureSlider_frame.grid_columnconfigure(2, weight=1)
        self.pressureSlider_frame.grid_propagate(False)  # Prevent resizing

        self.offDesingPressure_label = ctk.CTkLabel(self.pressureSlider_frame, text="P1t")
        self.offDesingPressure_label.grid(row=0, column=0, padx=pad, pady=pad, sticky='nswe')
        self.offDesingPressureSlider = ctk.CTkSlider(self.pressureSlider_frame, from_=1e-3, to=1, orientation='horizontal', number_of_steps=1000)
        self.offDesingPressureSlider.set(1)
        self.offDesingPressureSlider.bind('<B1-Motion>', self.updatePercentLabels)
        #self.offDesingPressureSlider.bind('<ButtonRelease-1>', self.updateMapPlots)
        self.offDesingPressureSlider.bind('<B1-Motion>', self.updateMapPlots)
        self.offDesingPressureSlider.grid(row=0, column=1, padx=pad, pady=pad, sticky='nswe')

        self.offDesingPressure0_label = ctk.CTkLabel(self.pressureSlider_frame, text="P0")
        self.offDesingPressure0_label.grid(row=1, column=0, padx=pad, pady=pad, sticky='nswe')
        self.offDesingPressure0Slider = ctk.CTkSlider(self.pressureSlider_frame, from_=1e-3, to=1, orientation='horizontal', number_of_steps=1000)
        self.offDesingPressure0Slider.grid(row=1, column=1, padx=pad, pady=pad, sticky='nswe')
        self.offDesingPressure0Slider.set(1)
        self.offDesingPressure0Slider.bind('<B1-Motion>', self.updatePercentLabels)
        #self.offDesingPressure0Slider.bind('<ButtonRelease-1>', self.updateMapPlots)
        self.offDesingPressure0Slider.bind('<B1-Motion>', self.updateMapPlots)

        p1p_init = f"{self.offDesingPressureSlider.get():.2f}"
        p0p_init = f"{self.offDesingPressure0Slider.get():.2f}"
        self.offDesingPressurePercent_label = ctk.CTkLabel(self.pressureSlider_frame, text=p1p_init)
        self.offDesingPressurePercent_label.grid(row=0, column=2, padx=pad, pady=pad, sticky='nswe')
        self.offDesingPressure0Percent_label = ctk.CTkLabel(self.pressureSlider_frame, text=p0p_init)
        self.offDesingPressure0Percent_label.grid(row=1, column=2, padx=pad, pady=pad, sticky='nswe')


    

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

        #self.results_TOPBNLabels = [
        #    "DP. Thrust (kg)", "Med. Thrust (kg)", 
        #    "CF (DP.)", "CF (Med.)",
        #    "Vs (DP.)", "Vs (Med.)",
        #    "Ts (DP.)", "Ts (Med.)",
        #    "Ps (DP.)", "Ps (Med.)",
        #    "It", "Isp",
        #    "AR", "MS",
        #    "Longitud (m)",
        #    "Rt (m)", "R2 (m)"
        #    ]
        
        #self.results_CONELabels = [
        #    "DP. Thrust (kg)", "Med. Thrust (kg)", 
        #    "CF (DP.)", "CF (Med.)",
        #    "It", "Isp",
        #    "Vs (DP.)", "Vs (Med.)",
        #    "Ts (DP.)", "Ts (Med.)",
        #    "Ps (DP.)", "Ps (Med.)",
        #    "AR", "MS",
        #    "Longitud (m)",
        #    "Yt (m)", "Y2 (m)"
        #    ]
        

        ## Llamar a la función para añadir labels y entries
        #self.add_labels_and_entries(self.numericResults_frame, self.results_TOPBNLabels)
    
  

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

        self.exportData =  ctk.CTkButton(self.calcExport_frame, text="Exportar Datos", command=self.export_results)
        self.exportData.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        

        #self.TOPN_widgets = []
        #self.CONE_widgets = []
        self.specInputs_entries = {}
        self.create_widgets_for_all_nozzle_types()

        self.selection = nozzle_types[0]  # Initialize selection
        self.update_options(self.selection)

        #self.create_TOPN_entries()
        #self.create_CONE_entries()
        #self.update_options('TOPN-BN')























    def calculate_n_show(self):
        self.create_progress_window()
        self.progress_var.set(0)


        self.engine_config = self.file_path_label.cget("text")
        self.nozzle_config = self.nozzleTypeMenu.get()
        self.P1 = float(self.pressure_entry.get())
        self.n = float(self.nPoints_entry.get())
        self.dt = float(get_entry_value(self.timeNormalization_entry))
        self.defaultState = self.pressureCheck_Box.get()


        if not self.dt:
            self.total_steps = len(self.P) 
        else:
            self.total_steps = len(np.arange(self.t[0], self.t[-1], self.dt))

        self.current_step = 0
        self.calculation_running = True

        #nozzleClasses = {
        #    "TOPN-BN": BellNozzle,
        #    "CONE-LN": ConeNozzle
        #}
        


        
        #self.specInputs = []

        selected_nozzle_class = self.nozzleClasses.get(self.nozzle_config)

#        if self.nozzle_config == "TOPN-BN":
#            nozzleEntries = self.TOPN_entries
#        elif self.nozzle_config == "CONE-LN":
#            nozzleEntries = self.CONE_entries

#        for entry in nozzleEntries:
#            self.specInputs.append(float(entry.get()))

        # Obtener las entradas dinámicas
        self.specInputs = {}
        for entry_name, widget_info in self.specInputs_entries[self.selection].items():
            entry_widget = widget_info[1]  # Extraer el entry (segundo elemento de la tupla)
            try:
                self.specInputs[entry_name] = float(entry_widget.get())  # Obtener el valor del entry
            except ValueError:
                messagebox.showerror("Error", "Por favor, introduce valores numéricos válidos.", parent=self.content_frame)
                return

        self.calculatedNozzle = selected_nozzle_class(self.defaultState, self.P1, self.n, self.dt, self.engine_config, self.specInputs)
        self.calculatedNozzle.calculation_running = self.calculation_running  # Pasar la variable de control

#        if self.nozzle_config == "TOPN-BN":
#            loop_func = self.calculatedNozzle.run_TOPBN_step 
#        elif self.nozzle_config == "CONE-LN":
#            loop_func = self.calculatedNozzle.run_CONE_step 

        # Ejecutar el cálculo paso a paso
        loop_func = self.calculatedNozzle.run_step
        self.run_calculations_step(loop_func)

    def run_calculations_step(self, loop_func):
        if self.current_step < self.total_steps and self.calculation_running:
            loop_func(self.current_step)

            # Actualizar la barra de progreso
            progress = (self.current_step + 1) / self.total_steps if self.total_steps > 0 else 1
            self.progress_var.set(progress)
            self.progress_label.configure(text=f"{int(progress * 100)}%")

            self.current_step += 1
            self.content_frame.after(1, lambda: self.run_calculations_step(loop_func))
        else:
            self.on_calculations_done()

    def on_calculations_done(self):
        if self.calculation_running:
            self.progress_window.destroy()
            self.calculation_running = False

            thrust_fig = self.calculatedNozzle.thrust_plot()
            thrustCoeff_fig = self.calculatedNozzle.thrustCoeff_plot()
            geometry_fig = self.calculatedNozzle.geom_plot()

            P_Off = self.calculatedNozzle.P1
            presMap_fig = self.calculatedNozzle.pres_plot(P_Off)
            machMap_fig = self.calculatedNozzle.mach_plot(P_Off)

            figs = [thrust_fig, thrustCoeff_fig, geometry_fig, presMap_fig, machMap_fig]
            frames = [
                self.thrustGraph_frame, 
                self.thrustCoefGraph_frame, 
                self.nozzleGeoGraph_frame, 
                self.presMap_frame,
                self.machMap_frame
            ]

            self.graph_labels = [None] * 3

            for i, (fig, frame) in enumerate(zip(figs, frames)):
                insert_fig(fig, frame)

        self.result_array = self.calculatedNozzle.calculated_results()
        self.update_results_entries(self.result_array)










    def on_progress_window_close(self):
        self.calculation_running = False
        self.progress_window.destroy()

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
        frame_width = self.progress_frame.winfo_width() * 1.3
        frame_height = self.progress_frame.winfo_height() * 2

        # Calcular el centro de la pantalla
        screen_width = self.progress_window.winfo_screenwidth()
        screen_height = self.progress_window.winfo_screenheight()
        position_top = int(screen_height / 2 - frame_height / 2)
        position_right = int(screen_width / 2 - frame_width / 2)

        self.progress_window.geometry(f"{frame_width}x{frame_height}+{position_right}+{position_top}")

        self.progress_window.transient(self.content_frame)
        self.progress_window.grab_set()

        # Manejar el cierre de la ventana de progreso
        self.progress_window.protocol("WM_DELETE_WINDOW", self.on_progress_window_close)

    def update_progress(self, progress):
        self.progress_var.set(progress)
        self.progress_label.configure(text=f"{int(progress * 100)}%")

   























    def updatePercentLabels(self, event=None):
        p1p_update = f"{float(self.offDesingPressureSlider.get()):.3f}"
        p0p_update = f"{float(self.offDesingPressure0Slider.get()):.3f}"
        self.offDesingPressurePercent_label.configure(text=p1p_update)
        self.offDesingPressure0Percent_label.configure(text=p0p_update)

        
    def updateMapPlots(self, event=None):
        try:
            p0_value = self.offDesingPressure0Slider.get() * self.calculatedNozzle.P0
            slider_value = self.offDesingPressureSlider.get()  # Obtiene el valor del slider, entre 0 y 1
            min_pressure = min(self.calculatedNozzle.P_t)  # Obtiene el valor mínimo de P_t
            max_pressure = max(self.calculatedNozzle.P_t)  # Obtiene el valor máximo de P_t

            # Interpolación lineal entre el mínimo y el máximo
            p1_value = min_pressure + slider_value * (max_pressure - min_pressure)
            #p1_value = self.offDesingPressureSlider.get() * max(self.calculatedNozzle.P_t)
            thrust_value = self.calculatedNozzle.opPoint_plot(p1_value, p0_value)["F"]
            pe_value = self.calculatedNozzle.opPoint_plot(p1_value, p0_value)["Pe"]
            pres_fig = self.calculatedNozzle.pres_plot(p1_value, p0_value)
            mach_fig = self.calculatedNozzle.mach_plot(p1_value, p0_value) 

            p0_p1_update = f"{(p0_value / p1_value):.4f}"
            pe_p1_update = f"{(pe_value / p1_value):.4f}"
            pe_p0_update = f"{(pe_value / p0_value):.4f}"
            thrst_update = f"{thrust_value:.4f}"

            PRC0_value = float(self.PR_Crit_0_Entry.get())
            PRC1_value = float(self.PR_Crit_1_Entry.get())
            PRC2_value = float(self.PR_Crit_2_Entry.get())
            PRC3_value = float(self.PR_Crit_3_Entry.get())

            self.PR1_Entry.delete(0, tk.END)
            self.PR1_Entry.insert(0, p0_p1_update)
            self.PR2_Entry.delete(0, tk.END)
            self.PR2_Entry.insert(0, pe_p1_update)
            self.PR3_Entry.delete(0, tk.END)
            self.PR3_Entry.insert(0, pe_p0_update)
            self.ThrustOff_Entry.delete(0, tk.END)
            self.ThrustOff_Entry.insert(0, thrst_update)


            if float(p0_p1_update) > PRC0_value:
                operation_tag = 'Subsonic'  
            elif PRC2_value < float(pe_p1_update) < PRC1_value:
                operation_tag = 'Normal Shock Inside'
            elif abs(float(pe_p1_update) - PRC3_value) < 1e-2 and pe_value < p0_value:
                operation_tag = 'Over-Expanded'
            elif abs(float(pe_p1_update) - PRC3_value) < 1e-2 and pe_value == p0_value:
                operation_tag = 'Desing-Point'
            elif abs(float(pe_p1_update) - PRC3_value) < 1e-2 and pe_value > p0_value:
                operation_tag = 'Under-Expanded'
            else:
                operation_tag = 'Normal Shock Exit'

            self.OperationPoint_Entry.delete(0, tk.END)
            self.OperationPoint_Entry.insert(0, operation_tag)

            insert_fig(pres_fig, self.presMap_frame, resize='Auto')
            insert_fig(mach_fig, self.machMap_frame, resize='Auto')

        except Exception as e:
            print("An error occurred:", e)
            traceback.print_exc()

    
#    def add_labels_and_entries(self, frame, data_list):
#        for i, text in enumerate(data_list):
#            label = ctk.CTkLabel(frame, text=text)
#            label.grid(row=i+1, column=0, padx=5, pady=5, sticky='w')
#            entry = ctk.CTkEntry(frame)
#            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky='we')
#            # Guardar la referencia del entry en el diccionario
#            self.resultsEntries[text] = entry

#    def add_labels_and_entries(self, frame, result_labels):
#        self.resultsEntries = {}
#        for i, label_text in enumerate(result_labels):
#            label = ctk.CTkLabel(frame, text=label_text)
#            label.grid(row=i+1, column=0, padx=5, pady=5, sticky='w')
#            entry = ctk.CTkEntry(frame)
#            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky='we')
#            self.resultsEntries[label_text] = entry

    def add_labels_and_entries(self, frame, data_list):
        # Limpiar los resultados anteriores
        if hasattr(self, 'result_labels'):
            for widget in self.result_labels:
                widget.grid_forget()

        self.result_labels = []
        self.resultsEntries = {}

        # Crear los labels de resultados
        for i, label_text in enumerate(data_list):
            label = ctk.CTkLabel(frame, text=label_text)
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky='w')

            entry = ctk.CTkEntry(frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky='we')
            self.resultsEntries[label_text] = entry

            # Guardar los widgets para luego poder ocultarlos o mostrarlos
            self.result_labels.append(label)
            self.result_labels.append(entry)

#    def update_results_entries(self, result_array):
#        # Actualizar los entries
#        for i, key in enumerate(self.results_tempLabels):
#            entry = self.resultsEntries.get(key)
#            if entry:
#                entry.delete(0, tk.END)  # Limpiar el contenido actual del entry
#                value = result_array[0][i]
#                formatted_value = f"{value:.4e}" if value >= 1e6 else f"{value:.4f}"
#                entry.insert(0, formatted_value)  # Insertar el nuevo valor formateado

    def update_results_entries(self, result_array):
        # Actualizar las entradas de resultados dinámicamente

        for i, key in enumerate(self.resultsEntries):
            entry = self.resultsEntries.get(key)
            if entry:
                entry.delete(0, tk.END)
                value = result_array[0][i]  # El primer índice depende de tu estructura de datos
                formatted_value = f"{value:.4e}" if value >= 1e6 else f"{value:.4f}"
                entry.insert(0, formatted_value)

        rightResults_entries = [
            self.PR_Crit_0_Entry,
            self.PR_Crit_1_Entry,
            self.PR_Crit_2_Entry,
            self.PR_Crit_3_Entry
        ]

        for i, entry in enumerate(rightResults_entries):
            entry.delete(0, tk.END)  # Limpiar el contenido actual del entry
            value = result_array[3][i]
            entry.insert(0, f"{value:.4f}")  # Insertar el nuevo valor formateado

        # Actualizar el Treeview de "Resultados"
        results_treeview = self.tabview.tab("Resultados").winfo_children()[0].winfo_children()[0]
        # Limpiar el Treeview de "Resultados"
        for item in results_treeview.get_children():
            results_treeview.delete(item)

        for row in zip(*result_array[1]):
            formatted_row = [f"{value:.4e}" if value >= 1e6 else f"{value:.4f}" for value in row]
            results_treeview.insert("", "end", values=formatted_row)

        # Actualizar el Treeview de "Geometria"
        geometry_treeview = self.tabview.tab("Geometria").winfo_children()[0].winfo_children()[0]
        # Limpiar el Treeview de "Geometria"
        for item in geometry_treeview.get_children():
            geometry_treeview.delete(item)

        for row in zip(*result_array[2]):
            formatted_row = [f"{value:.6f}" for value in row]
            geometry_treeview.insert("", "end", values=formatted_row)

            


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




    def get_engine_data(self, on_load=False, file=None):

        if not on_load:
            file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        else:
            file_path = file

        if file_path:
            self.file_name = os.path.basename(file_path)


            with open(file_path, 'r') as file:
                self.engine_Data = json.load(file)

            try:
                self.propellant = self.engine_Data["inputs"]["Propellant"]
                self.P0         = self.engine_Data["inputs"]["P0"]
                self.Rt         = self.engine_Data["inputs"]["Rt"]

                self.meanP      = self.engine_Data["results"]["meanPressure"]
                self.maxP       = self.engine_Data["results"]["maxPressure"]
                self.minP       = self.engine_Data["results"]["minPressure"]

                self.meanG      = self.engine_Data["results"]["meanMassFlow"]
                self.maxG       = self.engine_Data["results"]["maxMassFlow"]
                self.minG       = self.engine_Data["results"]["minMassFlow"]
                
                self.mass       = self.engine_Data["results"]["totalMass"]
                self.time       = self.engine_Data["results"]["totalTime"]

                self.t          = self.engine_Data["results"]["tree_data"]["Tiempo (s)"]
                self.P          = self.engine_Data["results"]["tree_data"]["Presi\u00f3n (Pa)"]
                self.G          = self.engine_Data["results"]["tree_data"]["Flujo M\u00e1sico (kg/s)"]
                self.M          = self.engine_Data["results"]["tree_data"]["Masa (kg)"]

                self.file_path_label.configure(text=self.file_name)
            except Exception as e:
                messagebox.showerror("Error", "Archivo no válido.", parent=self.content_frame)
                self.file_path_label.configure(text="Archivo Inválido")
                return

            if not on_load:
                self.update_slider()
                self.pressureCheck_Box.configure(state="normal")
                self.pressureCheck_Box.select()
                self.toggle_slider()
            else:
                self.pressureSlide_Bar.configure(from_= self.minP, to=self.maxP)
            


   
            

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
            

















#    def update_options(self, selection):
#        self.selection = selection
#        # Ocultar todos los widgets actuales
#        allWidgets = self.TOPN_widgets + self.CONE_widgets
#        for widget in allWidgets:
#            widget.grid_forget()
#
#         # Mostrar los widgets seleccionados
#        if selection == "TOPN-BN":
#            for i, widget in enumerate(self.TOPN_widgets):
#                row, col = divmod(i, 2)
#                widget.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
#                self.results_tempLabels = self.results_TOPBNLabels
#        elif selection == "CONE-LN":
#            for i, widget in enumerate(self.CONE_widgets):
#                row, col = divmod(i, 2)
#                widget.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
#                self.results_tempLabels = self.results_CONELabels
#
#        self.add_labels_and_entries(self.numericResults_frame, self.results_tempLabels)

    def create_widgets_for_all_nozzle_types(self):
        """Crea los widgets para cada tipo de tobera una sola vez y los almacena."""
        for nozzle_type in self.nozzleClasses.keys():
            self.specInputs_entries[nozzle_type] = {}
            selected_nozzle_class = self.nozzleClasses.get(nozzle_type)
            input_labels = selected_nozzle_class.get_input_labels()

            # Crear y almacenar widgets (ocultos inicialmente)
            for i, (label_text, entry_name) in enumerate(input_labels.items()):
                label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
                entry = ctk.CTkEntry(self.nozzleOptions)
                self.specInputs_entries[nozzle_type][entry_name] = (label, entry, i)

                # Inicialmente ocultar los widgets
                label.grid_forget()
                entry.grid_forget()


    def update_options(self, selection):
        # Ocultar los widgets de la opción actual si existen
        if self.selection:
            self.hide_widgets()
            self.hide_result_labels()  # Ocultar los labels de resultados anteriores

        # Actualizar la selección actual
        self.selection = selection


        # Si ya hemos creado los widgets para esta opción, simplemente los mostramos
        if self.selection in self.specInputs_entries:
            self.show_widgets()
        else:
            # Crear los widgets para esta nueva opción
            self.create_widgets_for_option()

        # Crear etiquetas de resultados dinámicamente para la nueva opción
        selected_nozzle_class = self.nozzleClasses.get(self.selection)
        result_labels = selected_nozzle_class.get_result_labels()
        self.add_labels_and_entries(self.numericResults_frame, result_labels)



    def hide_result_labels(self):
        """ Ocultar los labels de resultados previos. """
        if hasattr(self, 'result_labels'):
            for widget in self.result_labels:
                widget.grid_forget()


    def hide_widgets(self):
        """ Ocultar los widgets (labels y entries) de la opción actual usando grid_forget(). """
        if self.selection in self.specInputs_entries:
            for widget_info in self.specInputs_entries[self.selection].values():
                label_widget = widget_info[0]  # Extraer el label
                entry_widget = widget_info[1]  # Extraer el entry
                label_widget.grid_forget()  # Ocultar el label
                entry_widget.grid_forget()  # Ocultar el entry

    def show_widgets(self):
        """ Mostrar los widgets (labels y entries) de la opción actual usando grid(). """
        if self.selection in self.specInputs_entries:
            for widget_info in self.specInputs_entries[self.selection].values():
                label_widget, entry_widget, row = widget_info  # Extraer label, entry y fila
                label_widget.grid(row=row, column=0, padx=10, pady=5, sticky="nsew")
                entry_widget.grid(row=row, column=1, padx=10, pady=5, sticky="nsew")

    def create_widgets_for_option(self):
        """ Crear los widgets (labels y entries) para la opción seleccionada y mostrarlos. """
        # Obtener la clase seleccionada desde el diccionario
        selected_nozzle_class = self.nozzleClasses.get(self.selection)

        if not selected_nozzle_class:
            messagebox.showerror("Error", "No se encontró la clase correspondiente.", parent=self.content_frame)
            return

        # Crear entradas dinámicamente basadas en las etiquetas proporcionadas
        input_labels = selected_nozzle_class.get_input_labels()

        # Crear un diccionario para almacenar los labels y entradas de la nueva opción
        self.specInputs_entries[self.selection] = {}

        for i, (label_text, entry_name) in enumerate(input_labels.items()):
            label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
            entry = ctk.CTkEntry(self.nozzleOptions)

            # Colocar los widgets y almacenarlos en el diccionario
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")

            # Guardar la referencia del label, entry y su fila
            self.specInputs_entries[self.selection][entry_name] = (label, entry, i)

        # Añadir etiquetas de resultados dinámicamente
        result_labels = selected_nozzle_class.get_result_labels()
        self.add_labels_and_entries(self.numericResults_frame, result_labels)

        
                

#    def create_TOPN_entries(self):
#        # Crear entradas específicas para Tubular
#        self.TOPN_entries = []
#        self.TOPN_labels = [
#            "K (Factor Garganta):",
#            "theta_t (deg):",
#            "theta_e (deg):",
#            "% (L. Cono):"
#        ]
#
#        for i, label_text in enumerate(self.TOPN_labels):
#            label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
#            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
#            entry = ctk.CTkEntry(self.nozzleOptions)
#            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
#            self.TOPN_entries.append(entry)
#            self.TOPN_widgets.append(label)
#            self.TOPN_widgets.append(entry)
#
#    def create_CONE_entries(self):
#        # Crear entradas específicas para End-Burner
#        self.CONE_entries = []
#        self.CONE_labels = [
#            "K (Factor Garganta):",
#            "theta_t (deg):",
#        ]
#
#        for i, label_text in enumerate(self.CONE_labels):
#            label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
#            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
#            entry = ctk.CTkEntry(self.nozzleOptions)
#            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
#            self.CONE_entries.append(entry)
#            self.CONE_widgets.append(label)
#            self.CONE_widgets.append(entry)
























    def update_plot(self, event=None):
        try:
            # Crear una figura y un eje
            height, width = self.pressureGraph_Frame.winfo_height() / 100, self.pressureGraph_Frame.winfo_width() / 100
            fig, ax = plt.subplots(figsize=(width, height))

            # Dibujar los círculos exteriores e interiores
            ax.plot(self.t, self.P)


            # Añadir título y etiquetas
            ax.set_title(f"Pressure Profile (Pa)")
            ax.set_xlabel("Time (s)")
            ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
            ax.set_aspect('auto')

            # Obtener el valor del slider
            pressure_value = float(self.pressure_entry.get())

            # Interpolar el valor del tiempo correspondiente a la presión seleccionada
            interpolate_time = interp1d(self.P, self.t, bounds_error=False, fill_value="extrapolate")
            time_value = interpolate_time(pressure_value)

            # Dibujar el punto rojo
            ax.plot(time_value, pressure_value, 'ro', label=f"{(pressure_value / self.maxP):.3f}")
            ax.legend()
            # Ajustar el aspecto del gráfico para evitar la distorsión
            #ax.set_aspect('equal')
            # Añadir título y leyenda
        except Exception:
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()

        insert_fig(fig, frame=self.pressureGraph_Frame, resize='Auto')
        

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
            results_folder = os.path.join(working_path, "Nozzles")
            os.makedirs(results_folder, exist_ok=True)

            # Construir la ruta completa del archivo
            file_path = os.path.join(results_folder, file_name)

            # Obtener los datos del Treeview de la pestaña "Geometria"
            geo_tree = self.tabview.tab("Geometria").winfo_children()[0].winfo_children()[0]
            geo_data = {
                "X (m)": [],
                "Y (m)": [],
                "AR (m)": []
            }

            for item in geo_tree.get_children():
                values = geo_tree.item(item)["values"]
                geo_data["X (m)"].append(float(values[0]))
                geo_data["Y (m)"].append(float(values[1]))
                geo_data["AR (m)"].append(float(values[2]))

            # Obtener los datos del Treeview de la pestaña "Resultados"
            results_tree = self.tabview.tab("Resultados").winfo_children()[0].winfo_children()[0]
            timeResults_data = {
                "Tiempo (s)": [],
                "Empuje (kg)": [],
                "CF": []
            }

            for item in results_tree.get_children():
                values = results_tree.item(item)["values"]
                timeResults_data["Tiempo (s)"].append(float(values[0]))
                timeResults_data["Empuje (kg)"].append(float(values[1]))
                timeResults_data["CF"].append(float(values[2]))


            # Recopilar datos adicionales
            inputs = {
                "NozzleConfig": self.nozzle_config,
                "DefaultCheck": self.defaultState,
                "P1": self.P1,
                "n": self.n,
                "EngineConfig": self.engine_config,
                "specInputs": self.specInputs
            }

            # Suponiendo que self.specInputs es un diccionario
            #inputs.update(self.specInputs)

            calculatedResults = {}
            for i, key in enumerate(self.resultsEntries):
                entry = self.resultsEntries.get(key)
                if entry:
                    # Añadiendo la entrada al diccionario calculatedResults
                    calculatedResults[key] = float(get_entry_value(entry))
           
            calculatedResults["PR_Crit0"] = float(get_entry_value(self.PR_Crit_0_Entry))
            calculatedResults["PR_Crit1"] = float(get_entry_value(self.PR_Crit_1_Entry))
            calculatedResults["PR_Crit2"] = float(get_entry_value(self.PR_Crit_2_Entry))
            calculatedResults["PR_Crit3"] = float(get_entry_value(self.PR_Crit_3_Entry))


            results = {
                "Inputs": inputs,
                "geometry_data": geo_data,
                "timeResults_data": timeResults_data,
                "calculatedResults": calculatedResults
            }   

            # Guardar datos en un archivo JSON
            with open(file_path, 'w') as json_file:
                json.dump(results, json_file, indent=4)
            
            messagebox.showinfo("Guardar archivo", f"Resultados guardados en {file_path}", parent=self.content_frame)