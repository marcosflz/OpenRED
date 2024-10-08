from imports import *
from functions import *

from back_modules.back_1 import *

class PropellantDesignModule:
    def __init__(self, content_frame: ctk.CTkFrame, main_frame: ctk.CTkFrame):
        """
        Initializes the Propellant Design Module interface.

        Args:
            content_frame (ctk.CTkFrame): The frame where the main content will be placed.
            main_frame (ctk.CTkFrame): The main frame encompassing all components.
        """
        
        # Store the main frame and content frame
        self.main_frame = main_frame
        self.content_frame = content_frame
        
        # Configure the grid layout for the content frame
        self.content_frame.grid_rowconfigure(0, weight=1)  # Configure the first row to expand
        self.content_frame.grid_columnconfigure(0, weight=1)  # Configure the first column to expand
        self.content_frame.grid_columnconfigure(1, weight=1)  # Configure the second column to expand

        self.image_label = None  # Initialize the image label (it will be set later)

        # Import the GrainLibrary dynamically and assign it to grainClasses
        self.grainClasses = importLibraries(lib='back_modules/GrainLibrary')  # Import the GrainLibrary (a custom library)

        # Create frames inside content_frame

        # Create an input frame to hold user inputs
        self.inputs_frame = ctk.CTkFrame(self.content_frame)
        self.inputs_frame.grid(row=0, rowspan=2, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure the layout of the input frame to ensure it adapts to content
        self.inputs_frame.grid_columnconfigure(0, weight=1)  # Configure the first column to expand
        self.inputs_frame.grid_rowconfigure(0, weight=1)  # Configure the first row to expand
        self.inputs_frame.grid_rowconfigure(1, weight=1)  # Configure the second row to expand
        self.inputs_frame.grid_propagate(False)  # Prevent the frame from resizing based on content

        # Create a subframe to hold numeric inputs
        self.numeric_inputs = ctk.CTkFrame(self.inputs_frame, height=80)
        self.numeric_inputs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure the grid layout for the numeric input frame
        self.numeric_inputs.grid_columnconfigure(0, weight=1)  # First column expands
        self.numeric_inputs.grid_columnconfigure(1, weight=1)  # Second column expands
        self.numeric_inputs.grid_columnconfigure(2, weight=1)  # Third column expands
        self.numeric_inputs.grid_columnconfigure(3, weight=1)  # Fourth column expands
        self.numeric_inputs.grid_rowconfigure(0, weight=1)  # First row expands
        self.numeric_inputs.grid_rowconfigure(1, weight=1)  # Second row expands
        self.numeric_inputs.grid_rowconfigure(2, weight=10)  # Third row has more weight, so it expands more
        self.numeric_inputs.grid_propagate(False)  # Prevent resizing based on the content

        # Retrieve the list of propellants and configure the OptionMenu for selection
        self.get_propellants()

        # Label and dropdown for selecting propellant
        self.propellant_label = ctk.CTkLabel(self.numeric_inputs, text="Propellant")
        self.propellant_label.grid(row=0, column=0, columnspan=2, padx=(10, 5), pady=10, sticky="nsew")

        # Create a dropdown (OptionMenu) for selecting propellant, using the list of propellants retrieved earlier
        self.propellant_selector = ctk.CTkOptionMenu(self.numeric_inputs, values=self.propellants)
        self.propellant_selector.grid(row=0, column=2, columnspan=2, padx=(5, 10), pady=10, sticky="nsew")

        # Bind an event so when the user hovers over the dropdown, it updates the propellant menu
        self.propellant_selector.bind("<Enter>", self.update_propellant_menu)

        # Get the list of grain geometries from the grainClasses (keys of the grainClasses dictionary)
        grains = list(self.grainClasses.keys())

        # Label for selecting the grain geometry
        self.grainGeo_label = ctk.CTkLabel(self.numeric_inputs, text="Grain Geometry")
        self.grainGeo_label.grid(row=1, column=0, columnspan=2, padx=(10, 5), pady=10, sticky="nsew")

        # Create a dropdown for grain geometry selection, setting grains as the options and binding it to update_options method
        self.grainGeo_selector = ctk.CTkOptionMenu(self.numeric_inputs, values=grains, command=self.update_options)
        self.grainGeo_selector.grid(row=1, column=2, columnspan=2, padx=(5, 10), pady=10, sticky="nsew")

        # Create a scrollable frame for the main inputs
        self.mainInputsFrame = ctk.CTkScrollableFrame(self.numeric_inputs)
        self.mainInputsFrame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Create another scrollable frame for additional inputs (sub inputs)
        self.subInputsFrame = ctk.CTkScrollableFrame(self.numeric_inputs)
        self.subInputsFrame.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="nsew")


        # Label and entry for Ambient Pressure (Pa)
        self.ambientPressureLabel = ctk.CTkLabel(self.mainInputsFrame, text="Ambient Pressure (Pa):")
        self.ambientPressureLabel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.ambientPressureEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.ambientPressureEntry.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.ambientPressureEntry.bind("<FocusOut>", self.update_plot)

        # Label and entry for Throat Radius (m)
        self.throatRadiLabel = ctk.CTkLabel(self.mainInputsFrame, text="Throat Radius (m):")
        self.throatRadiLabel.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.throatRadiEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.throatRadiEntry.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.throatRadiEntry.bind("<FocusOut>", self.update_plot)

        # Label and entry for Case Radius (m)
        self.caseRadiLabel = ctk.CTkLabel(self.mainInputsFrame, text="Case Radius (m):")
        self.caseRadiLabel.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.caseRadiEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.caseRadiEntry.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.caseRadiEntry.bind("<FocusOut>", self.update_plot)

        # Label and entry for Length (mm)
        self.lCombLabel = ctk.CTkLabel(self.mainInputsFrame, text="Length (mm):")
        self.lCombLabel.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.lCombEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.lCombEntry.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")
        self.lCombEntry.bind("<FocusOut>", self.update_plot)

        # Label and entry for Time Step (s)
        self.timeStepLabel = ctk.CTkLabel(self.mainInputsFrame, text="Time Step (s):")
        self.timeStepLabel.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.timeStepEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.timeStepEntry.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")
        self.timeStepEntry.bind("<FocusOut>", self.update_plot)

        # Label and entry for Space Step (m)
        self.spaceStepLabel = ctk.CTkLabel(self.mainInputsFrame, text="Space Step (m):")
        self.spaceStepLabel.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")
        self.spaceStepEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.spaceStepEntry.grid(row=5, column=1, padx=10, pady=10, sticky="nsew")
        self.spaceStepEntry.bind("<FocusOut>", self.update_plot)

        # Label and entry for Maximum Iterations
        self.maxItersLabel = ctk.CTkLabel(self.mainInputsFrame, text="Maximum Iterations:")
        self.maxItersLabel.grid(row=6, column=0, padx=10, pady=10, sticky="nsew")
        self.maxItersEntry = ctk.CTkEntry(self.mainInputsFrame)
        self.maxItersEntry.grid(row=6, column=1, padx=10, pady=10, sticky="nsew")
        self.maxItersEntry.bind("<FocusOut>", self.update_plot)


        

        # Create a tab view for different sections in the input frame
        self.preRunFrame = ctk.CTkTabview(self.inputs_frame)
        self.preRunFrame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Add the "GEOMETRY" tab and configure its grid
        self.preRunFrame.add("GEOMETRY")
        self.preRunFrame.tab("GEOMETRY").grid_columnconfigure(0, weight=1)
        self.preRunFrame.tab("GEOMETRY").grid_rowconfigure(0, weight=1)

        # Add the "CONSOLE" tab and configure its grid
        self.preRunFrame.add("CONSOLE")
        self.preRunFrame.tab("CONSOLE").grid_columnconfigure(0, weight=1)
        self.preRunFrame.tab("CONSOLE").grid_columnconfigure(1, weight=1)
        self.preRunFrame.tab("CONSOLE").grid_rowconfigure(0, weight=10)
        self.preRunFrame.tab("CONSOLE").grid_rowconfigure(1, weight=1)

        # Add the "REGRESSION" tab and configure its grid
        self.preRunFrame.add("REGRESSION")
        self.preRunFrame.tab("REGRESSION").grid_columnconfigure(0, weight=1)
        self.preRunFrame.tab("REGRESSION").grid_rowconfigure(0, weight=1)

        self.preRunFrame.grid_propagate(False)  # Prevent automatic resizing of the grid

        # Frame for displaying images in the "GEOMETRY" tab
        self.image_frame = ctk.CTkFrame(self.preRunFrame.tab("GEOMETRY"))
        self.image_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.image_frame.grid_propagate(False)
        self.image_frame.configure(fg_color="white")  # Set background color to white

        # Reference to the console tab frame
        self.run_frame = self.preRunFrame.tab("CONSOLE")

        # Frame for regression inputs in the "REGRESSION" tab
        self.regression_frame = ctk.CTkFrame(self.preRunFrame.tab("REGRESSION"))
        self.regression_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.regression_frame.grid_propagate(False)
        self.regression_frame.configure(fg_color="white")

        # Textbox for console output in the "CONSOLE" tab
        self.console_box = ctk.CTkTextbox(self.run_frame)
        self.console_box.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Button to calculate combustion
        self.calcButton = ctk.CTkButton(self.run_frame, text="Calculate Combustion", command=self.calculate_n_show)
        self.calcButton.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Button to export results
        self.exportDataButton = ctk.CTkButton(self.run_frame, text="Export Results", command=self.export_results)
        self.exportDataButton.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Set the default visible tab to "GEOMETRY"
        self.preRunFrame.set("GEOMETRY")


        # Create a tab view for outputs
        self.outputs_frame = ctk.CTkTabview(self.content_frame)
        self.outputs_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.outputs_frame.grid_propagate(False)  # Prevent automatic resizing

        # Add "GRAPHS" tab and configure its grid
        self.outputs_graphs = self.outputs_frame.add("GRAPHS")
        self.outputs_graphs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.outputs_graphs.grid_rowconfigure(0, weight=1)
        self.outputs_graphs.grid_rowconfigure(1, weight=1)
        self.outputs_graphs.grid_rowconfigure(2, weight=1)
        self.outputs_graphs.grid_columnconfigure(0, weight=1)

        # Frame for pressure graph
        self.pressureFrame = ctk.CTkFrame(self.outputs_graphs)
        self.pressureFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.pressureFrame.grid_propagate(False)  # Prevent resizing
        self.pressureFrame.configure(fg_color="white")  # Set background color to white

        # Frame for mass flow graph
        self.massFlowFrame = ctk.CTkFrame(self.outputs_graphs)
        self.massFlowFrame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.massFlowFrame.grid_propagate(False)  # Prevent resizing
        self.massFlowFrame.configure(fg_color="white")  # Set background color to white

        # Frame for mass over time graph
        self.massTimeFrame = ctk.CTkFrame(self.outputs_graphs)
        self.massTimeFrame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.massTimeFrame.grid_propagate(False)  # Prevent resizing
        self.massTimeFrame.configure(fg_color="white")  # Set background color to white

        # Add "DATA" tab and configure its grid
        self.outputs_numeric = self.outputs_frame.add("DATA")
        self.outputs_numeric.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.outputs_numeric.grid_rowconfigure(0, weight=1)
        self.outputs_numeric.grid_rowconfigure(1, weight=20)
        self.outputs_numeric.grid_columnconfigure(0, weight=1)
        self.outputs_numeric.grid_propagate(False)  # Prevent resizing

        # Frame for displaying numeric data
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


        # Frame to hold tree data
        self.treeData_frame = ctk.CTkFrame(self.outputs_numeric)
        self.treeData_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.treeData_frame.grid_columnconfigure(0, weight=1)  # Allow column to expand
        self.treeData_frame.grid_rowconfigure(0, weight=1)  # Allow row to expand

        # Mean pressure label and entry
        self.meanPressure_label = ctk.CTkLabel(self.numeric_frame, text="Mean Pressure (Pa):")
        self.meanPressure_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.meanPressure_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.meanPressure_entry.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Max pressure label and entry
        self.maxPressure_label = ctk.CTkLabel(self.numeric_frame, text="Max. Pressure (Pa):")
        self.maxPressure_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.maxPressure_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.maxPressure_entry.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Min pressure label and entry
        self.minPressure_label = ctk.CTkLabel(self.numeric_frame, text="Min. Pressure (Pa):")
        self.minPressure_label.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.minPressure_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.minPressure_entry.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        # Total combustion time label and entry
        self.totalTime_label = ctk.CTkLabel(self.numeric_frame, text="Burning Time (s): ")
        self.totalTime_label.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.totalTime_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.totalTime_entry.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        # Mean mass flow label and entry
        self.meanMassFlow_label = ctk.CTkLabel(self.numeric_frame, text="Mean Mass Flow (kg/s):")
        self.meanMassFlow_label.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        self.meanMassFlow_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.meanMassFlow_entry.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")

        # Max mass flow label and entry
        self.maxMassFlow_label = ctk.CTkLabel(self.numeric_frame, text="Max. Mass Flow (kg/s):")
        self.maxMassFlow_label.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        self.maxMassFlow_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.maxMassFlow_entry.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")

        # Min mass flow label and entry
        self.minMassFlow_label = ctk.CTkLabel(self.numeric_frame, text="Min. Mass Flow (kg/s):")
        self.minMassFlow_label.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")
        self.minMassFlow_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.minMassFlow_entry.grid(row=2, column=3, padx=10, pady=10, sticky="nsew")

        # Total mass label and entry
        self.totalMass_label = ctk.CTkLabel(self.numeric_frame, text="Propellant Mass (kg):")
        self.totalMass_label.grid(row=3, column=2, padx=10, pady=10, sticky="nsew")
        self.totalMass_entry = ctk.CTkEntry(self.numeric_frame, state="readonly", height=5)
        self.totalMass_entry.grid(row=3, column=3, padx=10, pady=10, sticky="nsew")

        # Frame for tree view data
        self.tree_frame = ctk.CTkFrame(self.treeData_frame)
        self.tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)  # Allow row to expand
        self.tree_frame.grid_columnconfigure(0, weight=1)  # Allow column to expand

        # Create a Treeview widget for displaying output data
        self.tree = ttk.Treeview(self.tree_frame, columns=("Time (s)", "Pressure (Pa)", "Mass Flow (kg/s)", "Mass (kg)"), show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")  # Place the tree view in the grid

        # Configure the headings and columns
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)  # Set the column heading text
            self.tree.column(col, anchor="center", width=100)  # Center the column content

        # Add a vertical scrollbar for the tree view
        self.tree_scrollbar = ctk.CTkScrollbar(self.tree_frame, orientation="vertical", command=self.tree.yview)
        self.tree_scrollbar.grid(row=0, column=1, sticky="ns")  # Position the scrollbar
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)  # Link scrollbar to tree view

        # Set the default visible tab in outputs frame
        self.outputs_frame.set("GRAPHS")  

        # Dictionary to hold input entries for different grain types
        self.specInputs_entries = {}
        self.create_widgets_for_all_grain_types()  # Create widgets for user input based on grain type

        self.selection = grains[0]  # Initialize selection with the first grain type
        self.update_options(self.selection)  # Update options based on the selected grain type


        
    def create_widgets_for_all_grain_types(self) -> None:
        """Creates widgets for each type of nozzle only once and stores them."""
        for grain_type in self.grainClasses.keys():
            self.specInputs_entries[grain_type] = {}
            selected_nozzle_class = self.grainClasses.get(grain_type)
            input_labels = selected_nozzle_class.get_input_labels()

            # Create and store widgets (initially hidden)
            for i, (label_text, entry_name) in enumerate(input_labels.items()):
                label = ctk.CTkLabel(self.subInputsFrame, text=label_text)  # Create label
                entry = ctk.CTkEntry(self.subInputsFrame)  # Create entry field
                entry.bind("<FocusOut>", self.update_plot)  # Bind focus out event to update plot
                self.specInputs_entries[grain_type][entry_name] = (label, entry, i)  # Store widgets

                # Initially hide the widgets
                label.grid_forget()
                entry.grid_forget()


    def update_options(self, selection: str) -> None:
            """Updates the displayed widgets based on the selected grain type.

            Args:
                selection (str): The selected grain type.
            """
            # Hide current option widgets if they exist
            if self.selection:
                self.hide_widgets()
                # self.hide_result_labels()  # Hide previous result labels

            # Update current selection
            self.selection = selection

            # Show existing widgets for the current selection
            if self.selection in self.specInputs_entries:
                self.show_widgets()
            else:
                # Create widgets for the new selection
                self.create_widgets_for_option()


    def hide_widgets(self) -> None:
        """Hide the widgets (labels and entries) of the current option using grid_forget()."""
        if self.selection in self.specInputs_entries:
            for widget_info in self.specInputs_entries[self.selection].values():
                label_widget = widget_info[0]  # Extract the label
                entry_widget = widget_info[1]  # Extract the entry
                label_widget.grid_forget()  # Hide the label
                entry_widget.grid_forget()  # Hide the entry


    def show_widgets(self) -> None:
        """Show the widgets (labels and entries) of the current option using grid()."""
        if self.selection in self.specInputs_entries:
            for widget_info in self.specInputs_entries[self.selection].values():
                label_widget, entry_widget, row = widget_info  # Extract label, entry, and row
                label_widget.grid(row=row, column=0, padx=10, pady=10, sticky="nsew")
                entry_widget.grid(row=row, column=1, padx=10, pady=10, sticky="nsew")


    def create_widgets_for_option(self) -> None:
        """Create the widgets (labels and entries) for the selected option and display them."""
        # Get the selected class from the dictionary
        selected_grain_class = self.grainClasses.get(self.selection)

        if not selected_grain_class:
            messagebox.showerror("Error", "Selected grain class not found.", parent=self.content_frame)
            return

        # Dynamically create entries based on the provided labels
        input_labels = selected_grain_class.get_input_labels()

        # Create a dictionary to store the labels and entries for the new option
        self.specInputs_entries[self.selection] = {}

        for i, (label_text, entry_name) in enumerate(input_labels.items()):
            label = ctk.CTkLabel(self.subInputsFrame, text=label_text)  # Create label
            entry = ctk.CTkEntry(self.subInputsFrame)  # Create entry field

            # Place the widgets and store them in the dictionary
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")

            # Save the reference of the label, entry, and its row
            self.specInputs_entries[self.selection][entry_name] = (label, entry, i)

        
    def add_labels_and_entries(self, frame: ctk.CTkFrame, data_list: list[str]) -> None:
        """Create result labels and corresponding entry fields in the specified frame."""
        # Create result labels
        for i, label_text in enumerate(data_list):
            label = ctk.CTkLabel(frame, text=label_text)  # Create label
            label.grid(row=i + 1, column=0, padx=5, pady=5, sticky='w')  # Place label in the grid

            entry = ctk.CTkEntry(frame)  # Create entry field
            entry.grid(row=i + 1, column=1, padx=5, pady=5, sticky='we')  # Place entry in the grid


    def get_inputs(self) -> None:
        """Retrieve input values from the GUI and store them in specInputs."""
        self.specInputs = {}  # Initialize input dictionary

        self.propellant_type = re.sub(r'\s*\(\d+\)\s*', '', self.propellant_selector.get())  # Clean propellant type
        self.grain_config = self.grainGeo_selector.get()  # Get grain configuration
        
        # Get numerical inputs from entry fields and store them
        self.specInputs["P0"] = float(get_entry_value(self.ambientPressureEntry))  # Ambient pressure
        self.specInputs["Rt"] = float(get_entry_value(self.throatRadiEntry))  # Throat radius
        self.specInputs["R2"] = float(get_entry_value(self.caseRadiEntry))  # Case radius
        self.specInputs["Lc"] = float(get_entry_value(self.lCombEntry))  # Combustion length
        self.specInputs["dt"] = float(get_entry_value(self.timeStepEntry))  # Time step
        self.specInputs["dh"] = float(get_entry_value(self.spaceStepEntry))  # Space step
        self.specInputs["It"] = float(get_entry_value(self.maxItersEntry))  # Maximum iterations

        # Get propellant properties
        self.specInputs["a"] = get_propellant_value("a", self.propellant_type)[0]
        self.specInputs["n"] = get_propellant_value("n", self.propellant_type)[0]
        self.specInputs["R"] = get_propellant_value("R", self.propellant_type)[0]
        self.specInputs["T1"] = get_propellant_value("T_ad", self.propellant_type)[0]
        self.specInputs["cChar"] = get_propellant_value("cChar", self.propellant_type)[0]
        self.specInputs["rho_b"] = get_propellant_value("Density", self.propellant_type)[0]
        self.specInputs["P1_min"] = get_propellant_value("P1_min", self.propellant_type)[0]
        self.specInputs["P1_max"] = get_propellant_value("P1_max", self.propellant_type)[0]

        self.selected_grain_config = self.grainClasses.get(self.grain_config)  # Get selected grain config

        # Update specInputs with values from input entries for the current selection
        for entry_name, widget_info in self.specInputs_entries[self.selection].items():
            entry_widget = widget_info[1]  # Extract entry (second element of the tuple)
            try:
                self.specInputs[entry_name] = float(entry_widget.get())  # Get entry value
            except ValueError:
                # messagebox.showerror("Error", "Por favor, introduce valores numéricos válidos.", parent=self.content_frame)
                return
            
        # Initialize init_specs with relevant input values based on selected grain configuration
        self.init_specs = {key: self.specInputs[key] for key in list(self.selected_grain_config.get_input_labels().values()) if key in self.specInputs}


    def calculate_n_show(self) -> None:
        """Get inputs, start the simulation in a separate thread, and check its status."""
        # Obtener los inputs
        self.get_inputs()  # Retrieve input values

        # Crear un hilo para ejecutar la simulación
        self.simulation_thread = threading.Thread(target=self.run_simulation)  # Create thread for simulation
        self.simulation_thread.start()  # Start the simulation thread

        # Start polling to check if the simulation thread has finished
        self.check_simulation_thread()  # Check simulation thread status


    def run_simulation(self) -> None:
        """Initialize the grain configuration and run the propellant regression simulation."""
        # Configurar la clase de la configuración de grano
        grainConfigClass = self.selected_grain_config(self.init_specs, self.specInputs["R2"], self.specInputs["dh"])
        init_geo = grainConfigClass.getPhi()  # Obtener la geometría inicial
        self.propCAD = grainConfigClass.sketchCAD()  # Generar el diseño CAD

        # Inicializar la simulación
        self.simulation = PropellantRegresionLSM(
            textbox=0,  # Interfaz de texto (por definir)
            dt=self.specInputs["dt"],  # Paso de tiempo
            dh=self.specInputs["dh"],  # Paso espacial
            maxIters=self.specInputs["It"],  # Número máximo de iteraciones
            phi0=init_geo,  # Geometría inicial
            init_data=self.specInputs,  # Datos iniciales de entrada
            workingPrecision=8,  # Precisión de trabajo
            image_resolution=30  # Resolución de la imagen
        )

        # Ejecutar la simulación y almacenar los resultados
        self.results = self.simulation.run(self.console_box)  # Guardar los resultados en la caja de consola


    def check_simulation_thread(self) -> None:
        """Check if the simulation thread is still running and update results when finished."""
        if self.simulation_thread.is_alive():  # Verificar si el hilo de simulación sigue activo
            # Si el hilo sigue ejecutándose, verificar de nuevo después de 100 ms
            self.main_frame.after(100, self.check_simulation_thread)
        else:
            # Una vez que el hilo ha terminado, actualizar los resultados
            self.update_results(self.results, self.simulation)


    def update_results(self, results: dict, simulation) -> None:
        """Update the results displayed in the GUI based on simulation output."""
        insert_fig(simulation.result_figure(), self.regression_frame)  # Insert the result figure into the regression frame
        self.preRunFrame.set("REGRESSION")  # Set currently visible tab

        # Update pressure entries
        self.meanPressure_entry.configure(state='normal')
        self.meanPressure_entry.delete(0, tk.END)
        self.meanPressure_entry.insert(0, np.mean(results["P1"][1:]))  # Calculate and insert mean pressure
        self.meanPressure_entry.configure(state='readonly')

        self.maxPressure_entry.configure(state='normal')
        self.maxPressure_entry.delete(0, tk.END)
        self.maxPressure_entry.insert(0, np.max(results["P1"][1:]))  # Calculate and insert max pressure
        self.maxPressure_entry.configure(state='readonly')

        self.minPressure_entry.configure(state='normal')
        self.minPressure_entry.delete(0, tk.END)
        self.minPressure_entry.insert(0, np.min(results["P1"][1:]))  # Calculate and insert min pressure
        self.minPressure_entry.configure(state='readonly')

        # Update total time entry
        self.totalTime_entry.configure(state='normal')
        self.totalTime_entry.delete(0, tk.END)
        self.totalTime_entry.insert(0, results["TIME"][-1])  # Insert total time from results
        self.totalTime_entry.configure(state='readonly')

        # Update mass flow entries
        self.meanMassFlow_entry.configure(state='normal')
        self.meanMassFlow_entry.delete(0, tk.END)
        self.meanMassFlow_entry.insert(0, np.mean(results["GP"][1:]))  # Calculate and insert mean mass flow
        self.meanMassFlow_entry.configure(state='readonly')

        self.maxMassFlow_entry.configure(state='normal')
        self.maxMassFlow_entry.delete(0, tk.END)
        self.maxMassFlow_entry.insert(0, np.max(results["GP"][1:]))  # Calculate and insert max mass flow
        self.maxMassFlow_entry.configure(state='readonly')

        self.minMassFlow_entry.configure(state='normal')
        self.minMassFlow_entry.delete(0, tk.END)
        self.minMassFlow_entry.insert(0, np.min(results["GP"][1:]))  # Calculate and insert min mass flow
        self.minMassFlow_entry.configure(state='readonly')

        # Update total mass entry
        self.totalMass_entry.configure(state='normal')
        self.totalMass_entry.delete(0, tk.END)
        self.totalMass_entry.insert(0, results["MP"][0])  # Insert total mass from results
        self.totalMass_entry.configure(state='readonly')

        # Clear Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)  # Remove existing rows in the tree view
        # Insert new data into Treeview
        tree_data = [results["TIME"][1:], results["P1"][1:], results["GP"][1:], results["MP"][1:]]
        decimal_places = len(str(self.specInputs["dt"]).split('.')[-1])  # Determine decimal places for formatting
        for i in range(len(tree_data[0])):
            formatted_time = f"{tree_data[0][i]:.{decimal_places}f}"  # Format time with appropriate decimal places
            row_data = [formatted_time] + [col[i] for col in tree_data[1:]]  # Combine formatted time with other data
            self.tree.insert("", "end", values=row_data)  # Insert row into tree view

        # Insert additional simulation figures
        insert_fig(simulation.plot_pressure(), self.pressureFrame)  # Plot pressure data
        insert_fig(simulation.plot_massFlow(), self.massFlowFrame)  # Plot mass flow data
        insert_fig(simulation.plot_massBurn(), self.massTimeFrame)  # Plot mass burn data


    def update_plot(self, event=None) -> None:
        """Update the plot based on current inputs and display the geometry."""
        try:
            self.get_inputs()  # Retrieve inputs from the GUI
            grainConfigClass = self.selected_grain_config(self.init_specs, self.specInputs["R2"], self.specInputs["dh"])  # Create an instance of the selected grain configuration class
            insert_fig(grainConfigClass.plotGeometry(), self.image_frame)  # Insert the geometry plot into the image frame
            self.preRunFrame.set("GEOMETRY")  # Set currently visible tab to 'GEOMETRY'
        except Exception:
            return  # Handle any exceptions silently


    def get_propellants(self) -> None:
        """Fetch propellant names and IDs from the database and store them in a list."""
        conn = sqlite3.connect('database.db')  # Connect to the SQLite database
        cursor = conn.cursor()  # Create a cursor object to execute SQL commands
        cursor.execute("SELECT id, Propelente FROM propelente")  # Execute SQL query to get propellant data
        results = cursor.fetchall()  # Fetch all results from the executed query
        conn.close()  # Close the database connection
        self.propellants = [f"{row[1]} ({row[0]})" for row in results]  # Format results and store in self.propellants


    def update_propellant_menu(self, event=None) -> None:
        """Update the propellant selector menu with the latest propellant data."""
        self.get_propellants()  # Fetch the latest propellants from the database
        self.propellant_selector.configure(values=self.propellants)  # Update the selector with new values


    def export_results(self) -> None:
        """Export the simulation results and inputs to a JSON file."""
        working_path = get_dir_path()  # Get the working directory
        if not working_path:
            messagebox.showerror("Error", "No working directory has been selected.", parent=self.content_frame)
            return
        
        # Ask the user for the file name
        file_name = simpledialog.askstring("Save file", "Enter the file name:", parent=self.content_frame)
        
        if file_name:
            # Ensure the file name ends with '.json'
            if not file_name.endswith('.json'):
                file_name += '.json'

            # Create a folder named "resultados" within the working directory
            results_folder = os.path.join(working_path, "Engines")
            os.makedirs(results_folder, exist_ok=True)

            # Build the complete file path
            file_path = os.path.join(results_folder, file_name)

            # Collect data to save
            tree_data = {
                "Time (s)": [],
                "Pressure (Pa)": [],
                "Mass Flow (kg/s)": [],
                "Mass (kg)": []
            }

            # Save data from the Treeview in separate columns
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                tree_data["Time (s)"].append(float(values[0]))
                tree_data["Pressure (Pa)"].append(float(values[1]))
                tree_data["Mass Flow (kg/s)"].append(float(values[2]))
                tree_data["Mass (kg)"].append(float(values[3]))

            # Collect data to save
            inputs = {
                "Propellant": re.sub(r'\s*\(\d+\)\s*', '', self.propellant_selector.get()),
                "GrainGeo": self.grain_config,
                "CADx": self.propCAD[1][0].tolist(),
                "CADy": self.propCAD[1][1].tolist(),
                "CAD0": self.propCAD[0]
            }

            # Add all elements of self.specInputs to inputs
            inputs.update(self.specInputs)  # This adds all elements from the self.specInputs dictionary

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

            # Save data to a JSON file
            with open(file_path, 'w') as json_file:
                json.dump({"inputs": inputs, "results": results}, json_file, indent=4)
            
            messagebox.showinfo("Save file", f"Results saved in {file_path}", parent=self.content_frame)