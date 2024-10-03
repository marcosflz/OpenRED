from imports import *
from functions import *

from back_0 import *
from back_1 import *

class PropellantDesignModule:
    def __init__(self, content_frame, main_frame):
        self.main_frame = main_frame

        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)

        self.image_label = None
        self.grainClasses = importLibraries(lib='GrainLibrary')

        # Crear frames dentro de content_frame
        self.inputs_frame = ctk.CTkFrame(self.content_frame)
        self.inputs_frame.grid(row=0, rowspan=2, column=0, padx=10, pady=10, sticky="nsew")
        self.inputs_frame.grid_columnconfigure(0, weight=1)
        self.inputs_frame.grid_rowconfigure(0, weight=1)
        self.inputs_frame.grid_rowconfigure(1, weight=1)
        self.inputs_frame.grid_propagate(False)
        
        # Obtener los propelentes iniciales y configurar el OptionMenu

        self.numeric_inputs = ctk.CTkFrame(self.inputs_frame, height=80)
        self.numeric_inputs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.numeric_inputs.grid_columnconfigure(0, weight=1)
        self.numeric_inputs.grid_columnconfigure(1, weight=1)
        self.numeric_inputs.grid_columnconfigure(2, weight=1)
        self.numeric_inputs.grid_columnconfigure(3, weight=1)
        self.numeric_inputs.grid_rowconfigure(0, weight=1)
        self.numeric_inputs.grid_rowconfigure(1, weight=1)
        self.numeric_inputs.grid_rowconfigure(2, weight=10)
        #self.numeric_inputs.grid_rowconfigure(3, weight=1)
        #self.numeric_inputs.grid_rowconfigure(4, weight=1)
        #self.numeric_inputs.grid_rowconfigure(5, weight=1)
        #self.numeric_inputs.grid_rowconfigure(6, weight=1)
        self.numeric_inputs.grid_propagate(False)


        #self.inputsLabel = ctk.CTkLabel(self.inputs_frame, text="Inputs")
        #self.inputsLabel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.get_propellants()

        self.propellant_label = ctk.CTkLabel(self.numeric_inputs, text="Propelente")
        self.propellant_label.grid(row=0, column=0, columnspan=2, padx=(10, 5), pady=10, sticky="nsew")
        self.propellant_selector = ctk.CTkOptionMenu(self.numeric_inputs, values=self.propellants)
        self.propellant_selector.grid(row=0, column=2, columnspan=2, padx=(5, 10), pady=10, sticky="nsew")
        self.propellant_selector.bind("<Enter>", self.update_propellant_menu)

        #grains = ["Tubular", "End-Burner"]
        grains = list(self.grainClasses.keys())
        self.grainGeo_label = ctk.CTkLabel(self.numeric_inputs, text="Geometría del grano")
        self.grainGeo_label.grid(row=1, column=0, columnspan=2, padx=(10, 5), pady=10, sticky="nsew")
        self.grainGeo_selector = ctk.CTkOptionMenu(self.numeric_inputs, values=grains, command=self.update_options)
        self.grainGeo_selector.grid(row=1, column=2, columnspan=2, padx=(5, 10), pady=10, sticky="nsew")

        self.mainInputsFrame = ctk.CTkScrollableFrame(self.numeric_inputs)
        self.mainInputsFrame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.subInputsFrame = ctk.CTkScrollableFrame(self.numeric_inputs)
        self.subInputsFrame.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="nsew")





        self.ambientPressureLabel = ctk.CTkLabel(self.mainInputsFrame, text="Presión Ambiente (Pa):")
        self.ambientPressureLabel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.ambientPressureEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.ambientPressureEntry.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.ambientPressureEntry.bind("<FocusOut>", self.update_plot)


        self.throatRadiLabel = ctk.CTkLabel(self.mainInputsFrame, text="Radio Garganta (m):")
        self.throatRadiLabel.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.throatRadiEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.throatRadiEntry.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.throatRadiEntry.bind("<FocusOut>", self.update_plot)

        self.caseRadiLabel = ctk.CTkLabel(self.mainInputsFrame, text="Radio Carcasa (m):")
        self.caseRadiLabel.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.caseRadiEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.caseRadiEntry.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.caseRadiEntry.bind("<FocusOut>", self.update_plot)

        self.lCombLabel = ctk.CTkLabel(self.mainInputsFrame, text="Longitud (mm):")
        self.lCombLabel.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.lCombEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.lCombEntry.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")
        self.lCombEntry.bind("<FocusOut>", self.update_plot)

        self.timeStepLabel = ctk.CTkLabel(self.mainInputsFrame, text="Paso temporal (s):")
        self.timeStepLabel.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.timeStepEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.timeStepEntry.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")
        self.timeStepEntry.bind("<FocusOut>", self.update_plot)

        self.spaceStepLabel = ctk.CTkLabel(self.mainInputsFrame, text="Paso espacial (m):")
        self.spaceStepLabel.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")
        self.spaceStepEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.spaceStepEntry.grid(row=5, column=1, padx=10, pady=10, sticky="nsew")
        self.spaceStepEntry.bind("<FocusOut>", self.update_plot)

        self.maxItersLabel = ctk.CTkLabel(self.mainInputsFrame, text="Iteraciones Maximas:")
        self.maxItersLabel.grid(row=6, column=0, padx=10, pady=10, sticky="nsew")
        self.maxItersEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.maxItersEntry.grid(row=6, column=1, padx=10, pady=10, sticky="nsew")
        self.maxItersEntry.bind("<FocusOut>", self.update_plot)


        

        self.preRunFrame = ctk.CTkTabview(self.inputs_frame)
        self.preRunFrame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.preRunFrame.add("Geometría")
        self.preRunFrame.tab("Geometría").grid_columnconfigure(0, weight=1)
        self.preRunFrame.tab("Geometría").grid_rowconfigure(0, weight=1)
        self.preRunFrame.add("Consola")
        self.preRunFrame.tab("Consola").grid_columnconfigure(0, weight=1)
        self.preRunFrame.tab("Consola").grid_columnconfigure(1, weight=1)
        self.preRunFrame.tab("Consola").grid_rowconfigure(0, weight=10)
        self.preRunFrame.tab("Consola").grid_rowconfigure(1, weight=1)
        self.preRunFrame.add("Regresión")
        self.preRunFrame.tab("Regresión").grid_columnconfigure(0, weight=1)
        self.preRunFrame.tab("Regresión").grid_rowconfigure(0, weight=1)
        self.preRunFrame.grid_propagate(False)

        self.image_frame = ctk.CTkFrame(self.preRunFrame.tab("Geometría"))
        self.image_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.image_frame.grid_propagate(False)
        self.image_frame.configure(fg_color="white")
        
        self.run_frame = self.preRunFrame.tab("Consola")

        self.regression_frame = ctk.CTkFrame(self.preRunFrame.tab("Regresión"))
        self.regression_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.regression_frame.grid_propagate(False)
        self.regression_frame.configure(fg_color="white")

        self.console_box = ctk.CTkTextbox(self.run_frame)
        self.console_box.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.calcButton = ctk.CTkButton(self.run_frame, text="Calcular combustión", command=self.calculate_n_show)
        self.calcButton.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        self.exportDataButton = ctk.CTkButton(self.run_frame, text="Exportar Resultados", command=self.export_results)
        self.exportDataButton.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")


        self.preRunFrame.set("Geometría")  # set currently visible tab




        # Crear un Tabview
        #self.inputImageTabview = ctk.CTkTabview(self.inputs_frame)
        #self.inputImageTabview.grid(row=0, column=2, rowspan=5, padx=10, pady=10, sticky="nsew")

        # Añadir dos pestañas al Tabview
        #self.inputImage_frontSection = self.inputImageTabview.add("Sección Frontal")
        #self.inputImage_profileSection = self.inputImageTabview.add("Sección Lateral")

        #self.inputImageTabview.tab("Sección Frontal").grid_columnconfigure(0, weight=1)
        #self.inputImageTabview.tab("Sección Frontal").grid_rowconfigure(0, weight=1)

        #self.inputImageTabview.tab("Sección Lateral").grid_columnconfigure(0, weight=1)
        #self.inputImageTabview.tab("Sección Lateral").grid_rowconfigure(0, weight=1)


        # Frame en la primera pestaña
        #self.inputImageFrame1 = ctk.CTkFrame(self.inputImage_frontSection)
        #self.inputImageFrame1.grid(row=0, column=0, rowspan=5, padx=10, pady=10, sticky="nsew")
        #self.inputImageFrame1.grid_propagate(False)
        #self.inputImageFrame1.configure(fg_color="white")
#        self.inputImageFrame1.bind("<Button-1>", self.update_plot)

        # Frame en la segunda pestaña
        #self.inputImageFrame2 = ctk.CTkFrame(self.inputImage_profileSection)
        #self.inputImageFrame2.grid(row=0, column=0, rowspan=5, padx=10, pady=10, sticky="nsew")
        #self.inputImageFrame2.grid_propagate(False)
        #self.inputImageFrame2.configure(fg_color="white")
#        self.inputImageFrame2.bind("<Button-1>", self.update_plot)


        #self.inputImageFrame = ctk.CTkFrame(self.inputs_frame)
        #self.inputImageFrame.grid(row=0, column=2, rowspan=5, padx=10, pady=10, sticky="nsew")
        #self.inputImageFrame.grid_propagate(False)
        #self.inputImageFrame.configure(fg_color="white")
        #self.inputImageFrame.bind("<Button-1>", self.update_plot)

        #self.outputs_frame = ctk.CTkTabview(self.content_frame)

        #self.outputs_frame = ctk.CTkFrame(self.content_frame)
        #self.outputs_frame.grid(row=1, rowspan=2, column=0, padx=10, pady=10, sticky="nsew")
        #self.outputs_frame.grid_rowconfigure(0, weight=1)
        #self.outputs_frame.grid_rowconfigure(1, weight=1)
        #self.outputs_frame.grid_rowconfigure(2, weight=1)
        #self.outputs_frame.grid_rowconfigure(3, weight=1)
        #self.outputs_frame.grid_rowconfigure(4, weight=1)
        #self.outputs_frame.grid_rowconfigure(5, weight=5)
        #self.outputs_frame.grid_columnconfigure(0, weight=1)
        #self.outputs_frame.grid_columnconfigure(1, weight=1)
        #self.outputs_frame.grid_columnconfigure(2, weight=1)
        #self.outputs_frame.grid_columnconfigure(3, weight=1)

        self.outputs_frame = ctk.CTkTabview(self.content_frame)
        self.outputs_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.outputs_frame.grid_propagate(False)

        self.outputs_graphs = self.outputs_frame.add("Gráficos")
        self.outputs_graphs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.outputs_graphs.grid_rowconfigure(0, weight=1)
        self.outputs_graphs.grid_rowconfigure(1, weight=1)
        self.outputs_graphs.grid_rowconfigure(2, weight=1)
        self.outputs_graphs.grid_columnconfigure(0, weight=1)

        self.pressureFrame = ctk.CTkFrame(self.outputs_graphs)
        self.pressureFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.pressureFrame.grid_propagate(False)
        self.pressureFrame.configure(fg_color="white")

        self.massFlowFrame = ctk.CTkFrame(self.outputs_graphs)
        self.massFlowFrame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.massFlowFrame.grid_propagate(False)
        self.massFlowFrame.configure(fg_color="white")
        
        self.massTimeFrame = ctk.CTkFrame(self.outputs_graphs)
        self.massTimeFrame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.massTimeFrame.grid_propagate(False)
        self.massTimeFrame.configure(fg_color="white")
        

        self.outputs_numeric = self.outputs_frame.add("Datos")
        self.outputs_numeric.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.outputs_numeric.grid_rowconfigure(0, weight=1)
        self.outputs_numeric.grid_rowconfigure(1, weight=20)
        self.outputs_numeric.grid_columnconfigure(0, weight=1)
        self.outputs_numeric.grid_propagate(False)


        self.numeric_frame = ctk.CTkFrame(self.outputs_numeric)
        self.numeric_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.numeric_frame.grid_rowconfigure(0, weight=1)
        self.numeric_frame.grid_rowconfigure(1, weight=1)
        self.numeric_frame.grid_rowconfigure(2, weight=1)
        self.numeric_frame.grid_rowconfigure(3, weight=1)
        self.numeric_frame.grid_columnconfigure(0, weight=1)
        self.numeric_frame.grid_columnconfigure(1, weight=1)
        self.numeric_frame.grid_columnconfigure(2, weight=1)
        self.numeric_frame.grid_columnconfigure(3, weight=1)


        self.treeData_frame = ctk.CTkFrame(self.outputs_numeric)
        self.treeData_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.treeData_frame.grid_columnconfigure(0, weight=1)
        self.treeData_frame.grid_rowconfigure(0, weight=1)
        #self.outputs_numeric.grid_rowconfigure(0, weight=1)
        #self.outputs_numeric.grid_rowconfigure(1, weight=1)
        #self.outputs_numeric.grid_rowconfigure(2, weight=1)
        #self.outputs_numeric.grid_rowconfigure(3, weight=1)
        #self.outputs_numeric.grid_rowconfigure(4, weight=20)
        #self.outputs_numeric.grid_columnconfigure(0, weight=1)
        #self.outputs_numeric.grid_columnconfigure(1, weight=1)
        #self.outputs_numeric.grid_columnconfigure(3, weight=1)
        #self.outputs_numeric.grid_columnconfigure(4, weight=1)
        



        self.meanPressure_label = ctk.CTkLabel(self.numeric_frame, text="Presión Media (Pa):")
        self.meanPressure_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.meanPressure_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.meanPressure_entry.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.maxPressure_label = ctk.CTkLabel(self.numeric_frame, text="Presión Máxima (Pa):")
        self.maxPressure_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.maxPressure_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.maxPressure_entry.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.minPressure_label = ctk.CTkLabel(self.numeric_frame, text="Presión Mínima (Pa):")
        self.minPressure_label.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.minPressure_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.minPressure_entry.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.totalTime_label = ctk.CTkLabel(self.numeric_frame, text="Tiempo total de combustión (s): ")
        self.totalTime_label.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.totalTime_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.totalTime_entry.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.meanMassFlow_label = ctk.CTkLabel(self.numeric_frame, text="Flujo másico medio (kg/s):")
        self.meanMassFlow_label.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        self.meanMassFlow_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.meanMassFlow_entry.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")

        self.maxMassFlow_label = ctk.CTkLabel(self.numeric_frame, text="Flujo másico máximo (kg/s):")
        self.maxMassFlow_label.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        self.maxMassFlow_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.maxMassFlow_entry.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")

        self.minMassFlow_label = ctk.CTkLabel(self.numeric_frame, text="Flujo másico mínimo (kg/s):")
        self.minMassFlow_label.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")
        self.minMassFlow_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.minMassFlow_entry.grid(row=2, column=3, padx=10, pady=10, sticky="nsew")

        self.totalMass_label = ctk.CTkLabel(self.numeric_frame, text="Masa de propelente quemada (kg):")
        self.totalMass_label.grid(row=3, column=2, padx=10, pady=10, sticky="nsew")
        self.totalMass_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.totalMass_entry.grid(row=3, column=3, padx=10, pady=10, sticky="nsew")


        self.tree_frame = ctk.CTkFrame(self.treeData_frame)
        self.tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
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

        self.outputs_frame.set("Gráficos")  # set currently visible tab





        #self.buttonsFrame = ctk.CTkFrame(self.content_frame, height=5)
        #self.buttonsFrame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        #self.buttonsFrame.grid_rowconfigure(0, weight=1)  # Ensure buttons frame rows and columns expand correctly
        #self.buttonsFrame.grid_columnconfigure(0, weight=1)
        #self.buttonsFrame.grid_columnconfigure(1, weight=1)
        #self.buttonsFrame.grid_columnconfigure(2, weight=1)
        #self.buttonsFrame.grid_propagate(False)

        #self.calcButton = ctk.CTkButton(self.buttonsFrame, text="Calcular combustión")#, command=self.calculate_n_show)
        #self.calcButton.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

        #self.exportDataButton = ctk.CTkButton(self.buttonsFrame, text="Exportar Resultados", command=self.export_results)
        #self.exportDataButton.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")


        self.specInputs_entries = {}
        self.create_widgets_for_all_grain_types()

        self.selection = grains[0]  # Initialize selection
        self.update_options(self.selection)



#        self.tubular_widgets = []
#        self.end_burner_widgets = []
#        self.selection = 'Tubular'  # Initialize selection
#
#        self.create_tubular_entries()
#        self.create_end_burner_entries()
#
#    
#        self.update_entries("Tubular")

        
        
    def create_widgets_for_all_grain_types(self):
        """Crea los widgets para cada tipo de tobera una sola vez y los almacena."""
        for grain_type in self.grainClasses.keys():
            self.specInputs_entries[grain_type] = {}
            selected_nozzle_class = self.grainClasses.get(grain_type)
            input_labels = selected_nozzle_class.get_input_labels()

            # Crear y almacenar widgets (ocultos inicialmente)
            for i, (label_text, entry_name) in enumerate(input_labels.items()):
                label = ctk.CTkLabel(self.subInputsFrame, text=label_text)
                entry = ctk.CTkEntry(self.subInputsFrame)
                entry.bind("<FocusOut>", self.update_plot)
                self.specInputs_entries[grain_type][entry_name] = (label, entry, i)

                # Inicialmente ocultar los widgets
                label.grid_forget()
                entry.grid_forget()


    def update_options(self, selection):
        # Ocultar los widgets de la opción actual si existen
        if self.selection:
            self.hide_widgets()
            #self.hide_result_labels()  # Ocultar los labels de resultados anteriores

        # Actualizar la selección actual
        self.selection = selection

        # Si ya hemos creado los widgets para esta opción, simplemente los mostramos
        if self.selection in self.specInputs_entries:
            self.show_widgets()
        else:
            # Crear los widgets para esta nueva opción
            self.create_widgets_for_option()


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
                label_widget.grid(row=row, column=0, padx=10, pady=10, sticky="nsew")
                entry_widget.grid(row=row, column=1, padx=10, pady=10, sticky="nsew")

    def create_widgets_for_option(self):
        """ Crear los widgets (labels y entries) para la opción seleccionada y mostrarlos. """
        # Obtener la clase seleccionada desde el diccionario
        selected_grain_class = self.grainClasses.get(self.selection)

        if not selected_grain_class:
            messagebox.showerror("Error", "No se encontró la clase correspondiente.", parent=self.content_frame)
            return

        # Crear entradas dinámicamente basadas en las etiquetas proporcionadas
        input_labels = selected_grain_class.get_input_labels()

        # Crear un diccionario para almacenar los labels y entradas de la nueva opción
        self.specInputs_entries[self.selection] = {}

        for i, (label_text, entry_name) in enumerate(input_labels.items()):
            label = ctk.CTkLabel(self.subInputsFrame, text=label_text)
            entry = ctk.CTkEntry(self.subInputsFrame)

            # Colocar los widgets y almacenarlos en el diccionario
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")

            # Guardar la referencia del label, entry y su fila
            self.specInputs_entries[self.selection][entry_name] = (label, entry, i)

        
    def add_labels_and_entries(self, frame, data_list):
        # Crear los labels de resultados
        for i, label_text in enumerate(data_list):
            label = ctk.CTkLabel(frame, text=label_text)
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky='w')

            entry = ctk.CTkEntry(frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky='we')


    def get_inputs(self):
        self.specInputs = {}

        self.propellant_type = re.sub(r'\s*\(\d+\)\s*', '', self.propellant_selector.get())
        self.grain_config = self.grainGeo_selector.get()
        
        self.specInputs["P0"] = float(get_entry_value(self.ambientPressureEntry))
        self.specInputs["Rt"] = float(get_entry_value(self.throatRadiEntry))
        self.specInputs["R2"] = float(get_entry_value(self.caseRadiEntry))
        self.specInputs["Lc"] = float(get_entry_value(self.lCombEntry))
        self.specInputs["dt"] = float(get_entry_value(self.timeStepEntry))
        self.specInputs["dh"] = float(get_entry_value(self.spaceStepEntry))
        self.specInputs["It"] = float(get_entry_value(self.maxItersEntry))

        self.specInputs["a"] = get_propellant_value("a", self.propellant_type)[0]
        self.specInputs["n"] = get_propellant_value("n", self.propellant_type)[0]
        self.specInputs["R"] = get_propellant_value("R", self.propellant_type)[0]
        self.specInputs["T1"] = get_propellant_value("T_ad", self.propellant_type)[0]
        self.specInputs["cChar"] = get_propellant_value("cChar", self.propellant_type)[0]
        self.specInputs["rho_b"] = get_propellant_value("Density", self.propellant_type)[0]
        self.specInputs["P1_min"] = get_propellant_value("P1_min", self.propellant_type)[0]
        self.specInputs["P1_max"] = get_propellant_value("P1_max", self.propellant_type)[0]

        self.selected_grain_config = self.grainClasses.get(self.grain_config)

        for entry_name, widget_info in self.specInputs_entries[self.selection].items():
            entry_widget = widget_info[1]  # Extraer el entry (segundo elemento de la tupla)
            try:
                self.specInputs[entry_name] = float(entry_widget.get())  # Obtener el valor del entry
            except ValueError:
                #messagebox.showerror("Error", "Por favor, introduce valores numéricos válidos.", parent=self.content_frame)
                return
            
        self.init_specs = {key: self.specInputs[key] for key in list(self.selected_grain_config.get_input_labels().values()) if key in self.specInputs}



#    def calculate_n_show(self):
#        self.get_inputs()
#        grainConfigClass = self.selected_grain_config(self.init_specs, self.specInputs["R2"], self.specInputs["dh"])
#        init_geo =  grainConfigClass.getPhi()
#        
#        simulation = PropellantRegresionLSM(
#            textbox=0, 
#            dt=self.specInputs["dt"], 
#            dh=self.specInputs["dh"], 
#            maxIters=self.specInputs["It"], 
#            phi0=init_geo, 
#            init_data=self.specInputs, 
#            workingPrecision=8, 
#            image_resolution=30
#            )
#        
#        results = simulation.run(self.console_box)
#        insert_fig(simulation.result_figure(), self.regression_frame)
#        self.preRunFrame.set("Regresión")  # set currently visible tab
#
#        self.meanPressure_entry.configure(state='normal')  # Cambiar a estado 'normal'
#        self.meanPressure_entry.delete(0, tk.END)  # Borrar el contenido actual
#        self.meanPressure_entry.insert(0, np.mean(results["P1"][1:]))  # Insertar el nuevo valor
#        self.meanPressure_entry.configure(state='readonly')  # Volver a 'readonly'
#
#        self.maxPressure_entry.configure(state='normal')  # Cambiar a estado 'normal'
#        self.maxPressure_entry.delete(0, tk.END)  # Borrar el contenido actual
#        self.maxPressure_entry.insert(0, np.max(results["P1"][1:]))  # Insertar el nuevo valor
#        self.maxPressure_entry.configure(state='readonly')  # Volver a 'readonly'
#
#        self.minPressure_entry.configure(state='normal')  # Cambiar a estado 'normal'
#        self.minPressure_entry.delete(0, tk.END)  # Borrar el contenido actual
#        self.minPressure_entry.insert(0, np.min(results["P1"][1:]))  # Insertar el nuevo valor
#        self.minPressure_entry.configure(state='readonly')  # Volver a 'readonly'
#
#        self.totalTime_entry.configure(state='normal')  # Cambiar a estado 'normal'
#        self.totalTime_entry.delete(0, tk.END)  # Borrar el contenido actual
#        self.totalTime_entry.insert(0, results["TIME"][-1])  # Insertar el nuevo valor
#        self.totalTime_entry.configure(state='readonly')  # Volver a 'readonly'
#
#        self.meanMassFlow_entry.configure(state='normal')  # Cambiar a estado 'normal'
#        self.meanMassFlow_entry.delete(0, tk.END)  # Borrar el contenido actual
#        self.meanMassFlow_entry.insert(0, np.mean(results["GP"][1:]))  # Insertar el nuevo valor
#        self.meanMassFlow_entry.configure(state='readonly')  # Volver a 'readonly'
#
#        self.maxMassFlow_entry.configure(state='normal')  # Cambiar a estado 'normal'
#        self.maxMassFlow_entry.delete(0, tk.END)  # Borrar el contenido actual
#        self.maxMassFlow_entry.insert(0, np.max(results["GP"][1:]))  # Insertar el nuevo valor
#        self.maxMassFlow_entry.configure(state='readonly')  # Volver a 'readonly'
#
#        self.minMassFlow_entry.configure(state='normal')  # Cambiar a estado 'normal'
#        self.minMassFlow_entry.delete(0, tk.END)  # Borrar el contenido actual
#        self.minMassFlow_entry.insert(0, np.min(results["GP"][1:]))  # Insertar el nuevo valor
#        self.minMassFlow_entry.configure(state='readonly')  # Volver a 'readonly'
#
#        self.totalMass_entry.configure(state='normal')  # Cambiar a estado 'normal'
#        self.totalMass_entry.delete(0, tk.END)  # Borrar el contenido actual
#        self.totalMass_entry.insert(0, results["MP"][0])  # Insertar el nuevo valor
#        self.totalMass_entry.configure(state='readonly')  # Volver a 'readonly'
#
#        # Limpiar Treeview
#        for row in self.tree.get_children():
#            self.tree.delete(row)
#        # Insertar nuevos datos en el Treeview
#        tree_data = [results["TIME"][1:], results["P1"][1:], results["GP"][1:], results["MP"][1:]]
#        decimal_places = len(str(self.specInputs["dt"]).split('.')[-1])
#        for i in range(len(tree_data[0])):  # Asumiendo que todos los vectores tienen la misma longitud
#            # Formatear el tiempo con el número de decimales adecuado
#            formatted_time = f"{tree_data[0][i]:.{decimal_places}f}"
#            row_data = [formatted_time] + [col[i] for col in tree_data[1:]]  # Crear una fila con elementos de cada vector en la misma posición
#            self.tree.insert("", "end", values=row_data)
#
#        insert_fig(simulation.plot_pressure(), self.pressureFrame)
#        insert_fig(simulation.plot_massFlow(), self.massFlowFrame)
#        insert_fig(simulation.plot_massBurn(), self.massTimeFrame)

    def calculate_n_show(self):
        # Obtener los inputs
        self.get_inputs()
        
        # Crear un hilo para ejecutar la simulación
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.start()

        # Start polling to check if the simulation thread has finished
        self.check_simulation_thread()

    def run_simulation(self):
        grainConfigClass = self.selected_grain_config(self.init_specs, self.specInputs["R2"], self.specInputs["dh"])
        init_geo = grainConfigClass.getPhi()

        self.simulation = PropellantRegresionLSM(
            textbox=0, 
            dt=self.specInputs["dt"], 
            dh=self.specInputs["dh"], 
            maxIters=self.specInputs["It"], 
            phi0=init_geo, 
            init_data=self.specInputs, 
            workingPrecision=8, 
            image_resolution=30
        )

        self.results = self.simulation.run(self.console_box)

    def check_simulation_thread(self):
        if self.simulation_thread.is_alive():
            # If the thread is still running, check again after 100 ms
            self.main_frame.after(100, self.check_simulation_thread)
        else:
            # Once the thread has finished, update the results
            self.update_results(self.results, self.simulation)

    def update_results(self, results, simulation):
        insert_fig(simulation.result_figure(), self.regression_frame)
        self.preRunFrame.set("Regresión")  # set currently visible tab

        self.meanPressure_entry.configure(state='normal')
        self.meanPressure_entry.delete(0, tk.END)
        self.meanPressure_entry.insert(0, np.mean(results["P1"][1:]))
        self.meanPressure_entry.configure(state='readonly')

        self.maxPressure_entry.configure(state='normal')
        self.maxPressure_entry.delete(0, tk.END)
        self.maxPressure_entry.insert(0, np.max(results["P1"][1:]))
        self.maxPressure_entry.configure(state='readonly')

        self.minPressure_entry.configure(state='normal')
        self.minPressure_entry.delete(0, tk.END)
        self.minPressure_entry.insert(0, np.min(results["P1"][1:]))
        self.minPressure_entry.configure(state='readonly')

        self.totalTime_entry.configure(state='normal')
        self.totalTime_entry.delete(0, tk.END)
        self.totalTime_entry.insert(0, results["TIME"][-1])
        self.totalTime_entry.configure(state='readonly')

        self.meanMassFlow_entry.configure(state='normal')
        self.meanMassFlow_entry.delete(0, tk.END)
        self.meanMassFlow_entry.insert(0, np.mean(results["GP"][1:]))
        self.meanMassFlow_entry.configure(state='readonly')

        self.maxMassFlow_entry.configure(state='normal')
        self.maxMassFlow_entry.delete(0, tk.END)
        self.maxMassFlow_entry.insert(0, np.max(results["GP"][1:]))
        self.maxMassFlow_entry.configure(state='readonly')

        self.minMassFlow_entry.configure(state='normal')
        self.minMassFlow_entry.delete(0, tk.END)
        self.minMassFlow_entry.insert(0, np.min(results["GP"][1:]))
        self.minMassFlow_entry.configure(state='readonly')

        self.totalMass_entry.configure(state='normal')
        self.totalMass_entry.delete(0, tk.END)
        self.totalMass_entry.insert(0, results["MP"][0])
        self.totalMass_entry.configure(state='readonly')

        # Limpiar Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Insertar nuevos datos en el Treeview
        tree_data = [results["TIME"][1:], results["P1"][1:], results["GP"][1:], results["MP"][1:]]
        decimal_places = len(str(self.specInputs["dt"]).split('.')[-1])
        for i in range(len(tree_data[0])):
            formatted_time = f"{tree_data[0][i]:.{decimal_places}f}"
            row_data = [formatted_time] + [col[i] for col in tree_data[1:]]
            self.tree.insert("", "end", values=row_data)

        insert_fig(simulation.plot_pressure(), self.pressureFrame)
        insert_fig(simulation.plot_massFlow(), self.massFlowFrame)
        insert_fig(simulation.plot_massBurn(), self.massTimeFrame)



    def update_plot(self, event=None):
        try:
            self.get_inputs()
            grainConfigClass = self.selected_grain_config(self.init_specs, self.specInputs["R2"], self.specInputs["dh"])
            insert_fig(grainConfigClass.plotGeometry(), self.image_frame)
            self.preRunFrame.set("Geometría")  # set currently visible tab
        except Exception:
            return




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

            # Recopilar datos a guardar
            inputs = {
                "Propellant": re.sub(r'\s*\(\d+\)\s*', '', self.propellant_selector.get()),
                "GrainGeo": self.grain_config,
            }

            # Añadir todos los elementos de self.specInputs a inputs
            inputs.update(self.specInputs)  # Esto añade todos los elementos del diccionario self.specInputs

            results = {
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

            # Guardar datos en un archivo JSON
            with open(file_path, 'w') as json_file:
                json.dump({"inputs": inputs, "results": results}, json_file, indent=4)
            
            messagebox.showinfo("Guardar archivo", f"Resultados guardados en {file_path}", parent=self.content_frame)