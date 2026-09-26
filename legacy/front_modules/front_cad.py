from imports import *
from functions import *

from back_modules.back_2 import *

class EngineCADModule:
    def __init__(self, content_frame: ctk.CTkFrame) -> None:
        """
        Initialize the EngineCADModule.

        This module creates a tabbed interface for engine CAD with two main tabs: 
        ENGINE and TOOLS. It also configures the layout of the content frame.

        Args:
            content_frame (ctk.CTkFrame): The parent frame for the tabbed interface.
        """
        self.content_frame = content_frame
        
        # Configure the grid layout for the content frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(2, weight=1)

        self.user_settings = None  # Placeholder for user settings

        # Create a tab view for graphs
        self.tab_view_graphs = ctk.CTkTabview(self.content_frame)
        self.tab_view_graphs.grid(row=0, rowspan=2, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Add tabs to the tab view
        self.tab_view_graphs.add("ENGINE")
        self.tab_view_graphs.add("TOOLS")

        # Configure grid for ENGINE tab
        self.tab_view_graphs.tab("ENGINE").grid_rowconfigure(0, weight=1)
        self.tab_view_graphs.tab("ENGINE").grid_rowconfigure(1, weight=1)
        self.tab_view_graphs.tab("ENGINE").grid_columnconfigure(0, weight=1)
        self.tab_view_graphs.tab("ENGINE").grid_columnconfigure(1, weight=1)

        # Configure grid for TOOLS tab
        self.tab_view_graphs.tab("TOOLS").grid_rowconfigure(0, weight=1)
        self.tab_view_graphs.tab("TOOLS").grid_rowconfigure(1, weight=1)
        self.tab_view_graphs.tab("TOOLS").grid_columnconfigure(0, weight=1)
        self.tab_view_graphs.tab("TOOLS").grid_columnconfigure(1, weight=1)

        self.tab_view_graphs.grid_propagate(False)  # Prevent grid from resizing based on widget size



        # Create frames for the ENGINE tab
        self.CoverView_frame = ctk.CTkFrame(self.tab_view_graphs.tab("ENGINE"))
        self.CoverView_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.CoverView_frame.configure(fg_color="white")
        self.CoverView_frame.grid_propagate(False)

        self.EngineView_frame = ctk.CTkFrame(self.tab_view_graphs.tab("ENGINE"))
        self.EngineView_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.EngineView_frame.configure(fg_color="white")
        self.EngineView_frame.grid_propagate(False)

        self.NozzleView_frame = ctk.CTkFrame(self.tab_view_graphs.tab("ENGINE"))
        self.NozzleView_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')
        self.NozzleView_frame.configure(fg_color="white")
        self.NozzleView_frame.grid_propagate(False)

        # Create frames for the TOOLS tab
        self.CastingMould_frame = ctk.CTkFrame(self.tab_view_graphs.tab("TOOLS"))
        self.CastingMould_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.CastingMould_frame.configure(fg_color="white")
        self.CastingMould_frame.grid_propagate(False)

        self.CoverView1_frame = ctk.CTkFrame(self.tab_view_graphs.tab("TOOLS"))
        self.CoverView1_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.CoverView1_frame.configure(fg_color="white")
        self.CoverView1_frame.grid_propagate(False)

        self.CoverView2_frame = ctk.CTkFrame(self.tab_view_graphs.tab("TOOLS"))
        self.CoverView2_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')
        self.CoverView2_frame.configure(fg_color="white")
        self.CoverView2_frame.grid_propagate(False)

        # Create the main options frame
        self.options_frame = ctk.CTkFrame(self.content_frame)
        self.options_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky='nswe')
        self.options_frame.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_rowconfigure(0, weight=1)
        self.options_frame.grid_rowconfigure(1, weight=10)
        self.options_frame.grid_rowconfigure(2, weight=1)
        self.options_frame.grid_propagate(False)

        # Create the import frame for loading files
        self.import_frame = ctk.CTkFrame(self.options_frame, height=100)
        self.import_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.import_frame.grid_rowconfigure(0, weight=1)
        self.import_frame.grid_columnconfigure(0, weight=1)
        self.import_frame.grid_columnconfigure(1, weight=1)

        # Button for loading engine files
        self.load_file_button = ctk.CTkButton(self.import_frame, text="Cargar Motor", command=self.build_entries, width=50)
        self.load_file_button.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.load_file_button.grid_propagate(False)

        # Label to display the file path
        self.file_path_label = ctk.CTkLabel(self.import_frame, text="No se ha cargado ningún archivo")
        self.file_path_label.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')
        self.file_path_label.grid_propagate(False)

        # Create a tab view for additional options
        self.tab_view = ctk.CTkTabview(self.options_frame)
        self.tab_view.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_view.add("ENTRIES")
        self.tab_view.add("CHECKBOXES")
        self.tab_view.grid_propagate(False)

        # Make sure the tabs expand to fill the available space
        self.tab_view.tab("ENTRIES").grid_rowconfigure(0, weight=1)
        self.tab_view.tab("ENTRIES").grid_columnconfigure(0, weight=1)
        self.tab_view.tab("CHECKBOXES").grid_rowconfigure(0, weight=1)
        self.tab_view.tab("CHECKBOXES").grid_columnconfigure(0, weight=1)

        # Scrollable frame for the Entries tab
        self.entries_tab = ctk.CTkScrollableFrame(self.tab_view.tab("ENTRIES"))
        self.entries_tab.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.entries_tab.grid_columnconfigure(0, weight=1)

        # Scrollable frame for the Checkboxes tab
        self.checkboxes_tab = ctk.CTkScrollableFrame(self.tab_view.tab("CHECKBOXES"))
        self.checkboxes_tab.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.checkboxes_tab.grid_columnconfigure(0, weight=1)

        # Export frame for export options
        self.export_frame = ctk.CTkFrame(self.options_frame)
        self.export_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')
        self.export_frame.grid_rowconfigure(0, weight=1)
        self.export_frame.grid_rowconfigure(1, weight=1)
        self.export_frame.grid_columnconfigure(0, weight=1)
        self.export_frame.grid_columnconfigure(1, weight=1)

        # Button to export engine sketch
        self.export_engine_button = ctk.CTkButton(self.export_frame, text="Engine Sketch",
            command=lambda: self.export_sketch(self.user_settings, 'Engine'))
        self.export_engine_button.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        # Button to export cover sketch
        self.export_cover_button = ctk.CTkButton(self.export_frame, text="Cover Sketch",
            command=lambda: self.export_sketch(self.user_settings, 'Cover'))
        self.export_cover_button.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        # Uncomment to add export button for mounting sketch
        # self.export_mount_button = ctk.CTkButton(self.export_frame, text="Mount Sketch",
        #     command=lambda: self.export_sketch(self.user_settings, 'Mount'))
        # self.export_mount_button.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')

        # Button to export tools sketch
        self.export_tools_button = ctk.CTkButton(self.export_frame, text="Tools Sketch",
            command=lambda: self.export_sketch(self.user_settings, 'Tools'))
        self.export_tools_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')

        # Dictionary to hold dynamic widgets
        self.widgets_dict = {}


    def build_entries(self, on_load: bool = False, file: str = None) -> None:
        """
        Build the entry fields and checkboxes based on the data loaded from a JSON file.

        This method prompts the user to select a JSON file if not loading automatically. 
        It extracts nozzle data from the file and creates the appropriate widgets 
        in the GUI, including entry fields and checkboxes based on the data.

        Args:
            on_load (bool): Flag indicating whether the method is called during an 
                            automatic load (default is False).
            file (str, optional): The file path to load data from if on_load is True.

        Returns:
            None
        """
        # Prompt user to load a file if not loading automatically
        if not on_load:
            file_path = filedialog.askopenfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        else:
            file_path = file

        if file_path:
            self.file_name = os.path.basename(file_path)
            try:
                # Get nozzle data from the file
                nozzleData = get_data(type='Nozzles', file=self.file_name)
                nozzle_arch = nozzleData["Inputs"]["NozzleConfig"]

                if nozzle_arch != 'AS-Nozzle':
                    # Define labels for entry fields
                    self.entriesLabelsDic = {
                        'type':             "Tipo de pared en la tobera",
                        'n_conv':           "Puntos Arco Convergente (n)",
                        't_cartridge':      "Espesor de Cartucho (m)",
                        'KIn':              "Coeficiente radio entrada (%)",
                        'alpha':            "Angulo zona convergente (deg)",
                        'wall_t':           "Espesor de pared (m)",
                        'bolt_OffSet':      "Longitud tornillo (m)",
                        'hBoltFactor':      "Factor de altura del tornillo (%)",
                        'cover_t':          "Espesor de la cubierta (m)",
                        'dy_elect':         "Distancia entre electrodos (m)",
                        'd_elect':          "Diámetro del electrodo (m)",
                        "on_Cartridge":     "Mostrar Cartucho",
                        "on_Propellant":    "Mostrar Propelente",
                        "on_Engine":        "Mostrar Motor",
                        "on_Cover":         "Mostrar Cubierta",
                        "t_factor":         "Factor Espesor Tools (%)",
                        "extra_len":        "Longitud Extra de molde (m)",
                        "cover_len":        "Longitud exterior molde (m)",
                        "on_CoverCast1":    "Cubierta de molde",
                        "on_CoverCast2":    "Sujección de molde",
                        "on_CastBolt":      "Tornillo de Tuerca",
                        "on_Mould":         "Molde de propelente",
                        "on_CastNut":       "Tuerca de molde",
                        "nut_h":            "Altura de Tuerca (m)",
                        "nut_dr":           "Incremento radio de Tuerca (m)"
                    }

                    # Initialize the engine builder
                    self.engineBuild = EngineCADBuilder_ConventionalNozzle(self.file_name)

                # Clear existing widgets in the tabs
                for widget in self.entries_tab.winfo_children():
                    widget.destroy()
                for widget in self.checkboxes_tab.winfo_children():
                    widget.destroy()

                # Initialize row counters for entries and checkboxes
                row_entries = 1
                row_checkboxes = 1

                # Create input fields and checkboxes based on the labels dictionary
                for key, label_text in self.entriesLabelsDic.items():
                    if key == 'type':
                        options = ["Fitted", "Bulk"]
                        # Option menu for type selection
                        optionTypeLabel = ctk.CTkLabel(self.entries_tab, text=label_text)
                        optionTypeLabel.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
                        optionTypeMenu = ctk.CTkOptionMenu(self.entries_tab, values=options, command=self.update_plots)
                        optionTypeMenu.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
                        self.widgets_dict[key] = optionTypeMenu

                    # Create entry fields for other parameters
                    elif '(' in label_text:
                        label = ctk.CTkLabel(self.entries_tab, text=label_text)
                        label.grid(row=row_entries, column=0, padx=10, pady=5, sticky="nsew")
                        entry = ctk.CTkEntry(self.entries_tab)
                        entry.grid(row=row_entries, column=1, padx=10, pady=5, sticky="nsew")
                        entry.bind("<FocusOut>", self.update_plots)
                        self.widgets_dict[key] = entry
                        row_entries += 1
                    # Create checkboxes for boolean parameters
                    else:
                        label = ctk.CTkLabel(self.checkboxes_tab, text=label_text)
                        label.grid(row=row_checkboxes, column=0, padx=10, pady=5, sticky="nsew")
                        checkbox = ctk.CTkCheckBox(self.checkboxes_tab, text="", command=self.update_plots)
                        checkbox.grid(row=row_checkboxes, column=1, padx=10, pady=5, sticky="nsew")
                        checkbox.select()  # Default to selected
                        self.widgets_dict[key] = checkbox
                        row_checkboxes += 1

                # Update the file path label to show the loaded file name
                self.file_path_label.configure(text=self.file_name)

            except Exception as e:
                # Display an error message if loading fails
                messagebox.showerror("Error", f"Archivo no válido: {e}", parent=self.content_frame)
                self.file_path_label.configure(text="Archivo Inválido")
                return
            

    def collect_widget_values(self) -> dict[str, float | str | bool]:
        """
        Collect values from the user interface widgets and store them in a dictionary.

        This method iterates through the widgets managed in the `widgets_dict` attribute, 
        retrieving the values from option menus, entry fields, and checkboxes. 

        Returns:
            dict[str, float | str | bool]: A dictionary containing the collected values 
            where keys are widget identifiers and values are the corresponding user inputs.
        """
        values_dict = {}
        
        # Iterate through the widgets stored in the dictionary
        for key, widget in self.widgets_dict.items():
            if isinstance(widget, ctk.CTkOptionMenu):
                # Get the selected value from the option menu
                values_dict[key] = widget.get()
            elif isinstance(widget, ctk.CTkEntry):
                # Retrieve and convert the entry value to float
                values_dict[key] = float(get_entry_value(widget))
            elif isinstance(widget, ctk.CTkCheckBox):
                # Get the state of the checkbox (selected or not)
                values_dict[key] = widget.get()
        
        return values_dict
    

    def update_plots(self, event=None) -> None:
        """
        Update and generate plots based on user settings collected from the interface.

        Args:
            event (Optional[ctk.Event]): An optional event object, typically used for event handling.
        
        Raises:
            Exception: Catches and prints any exceptions that occur during the plotting process.
        """
        try:
            # Collect user settings from widgets
            self.user_settings = self.collect_widget_values()

            # Generate plots using the user settings
            engine_fig = self.engineBuild.plot_Engine(self.user_settings)
            cover_fig = self.engineBuild.plot_CoverFront(self.user_settings)
            nozzle_fig = self.engineBuild.plot_NozzleFront(self.user_settings)
            
            tool_covers_fig = self.engineBuild.plot_Tools(self.user_settings)
            tool_coverFront_1_fig = self.engineBuild.plot_ToolMould(self.user_settings)
            tool_coverFront_2_fig = self.engineBuild.plot_ToolMouldFix(self.user_settings)

            # Insert generated plots into the respective frames
            insert_fig(engine_fig, self.EngineView_frame)
            insert_fig(cover_fig, self.CoverView_frame)
            insert_fig(nozzle_fig, self.NozzleView_frame)

            insert_fig(tool_covers_fig, self.CastingMould_frame)
            insert_fig(tool_coverFront_1_fig, self.CoverView1_frame)
            insert_fig(tool_coverFront_2_fig, self.CoverView2_frame)

        except Exception as e:
            # Print the error for debugging purposes
            print("An error occurred:", e)
            traceback.print_exc()


    def export_sketch(self, user_settings: dict, sketch_type: str) -> None:
        """
        Export sketches based on the provided sketch type and user settings.

        Args:
            user_settings (dict): A dictionary containing user-defined parameters for the sketch.
            sketch_type (str): The type of sketch to export. Accepted values are 'Engine', 'Cover', and 'Tools'.

        Raises:
            Exception: Raises an exception if the export process fails.
        """
        working_path = get_dir_path()
        if not working_path:
            messagebox.showerror("Error", "No se ha seleccionado un directorio de trabajo.", parent=self.content_frame)
            return
        
        # Prompt user for the filename
        file_name = simpledialog.askstring("Guardar archivo", "Introduce el nombre del archivo:", parent=self.content_frame)
        
        if file_name:
            # Ensure the filename ends with '.csv'
            if not file_name.endswith('.csv'):
                file_name += '.csv'
            
            # Create a folder named "Sketches" within the working directory
            results_folder = os.path.join(working_path, "Sketches")
            os.makedirs(results_folder, exist_ok=True)

            # Build the complete file path
            file_path = os.path.join(results_folder, file_name)

            # Check if the file already exists
            if os.path.exists(file_path):
                if not messagebox.askyesno("Overwrite file", f"El archivo {file_name} ya existe. ¿Quieres sobrescribirlo?", parent=self.content_frame):
                    return  # User chose not to overwrite

            # Export based on sketch type
            try:
                if sketch_type == 'Engine':
                    self.engineBuild.export_engine(user_settings, file_path)
                elif sketch_type == 'Cover':
                    self.engineBuild.export_cover(user_settings, file_path)
                elif sketch_type == 'Tools':
                    self.engineBuild.export_tools(user_settings, file_path)
                else:
                    messagebox.showerror("Error", "Tipo de boceto no válido.", parent=self.content_frame)
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {e}", parent=self.content_frame)