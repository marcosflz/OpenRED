from imports import *
from functions import *


class NozzleDesignModule:
    def __init__(self, content_frame: ctk.CTkFrame):
        """Initialize the NozzleDesignModule with layout and import necessary libraries."""
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)  # Configure row weights
        self.content_frame.grid_rowconfigure(1, weight=20)
        self.content_frame.grid_rowconfigure(2, weight=20)
        self.content_frame.grid_rowconfigure(3, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)  # Configure column weights
        self.content_frame.grid_columnconfigure(1, weight=2)

        # Import nozzle classes
        self.nozzleClasses = importLibraries(lib='back_modules/NozzleLibrary')

        self.image_label = None  # Initialize image label for the nozzle design
        self.updateIteration = 0  # Initialize update iteration counter

        # Create inputs frame with fixed size and layout configuration
        self.inputs_frame = ctk.CTkFrame(self.content_frame, height=450, width=600)
        self.inputs_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.inputs_frame.grid_propagate(False)
        # Configure rows and columns in inputs frame
        self.inputs_frame.grid_rowconfigure(0, weight=1)
        self.inputs_frame.grid_rowconfigure(1, weight=1)
        self.inputs_frame.grid_rowconfigure(2, weight=1)
        self.inputs_frame.grid_rowconfigure(3, weight=1)
        self.inputs_frame.grid_rowconfigure(4, weight=1)
        self.inputs_frame.grid_rowconfigure(5, weight=1)
        self.inputs_frame.grid_rowconfigure(6, weight=1)
        self.inputs_frame.grid_columnconfigure(0, weight=1)
        self.inputs_frame.grid_columnconfigure(1, weight=1)
        self.inputs_frame.grid_columnconfigure(2, weight=15)

        inputsPad = 5  # Padding for input elements

        # Button to load engine data file
        self.load_file_button = ctk.CTkButton(self.inputs_frame, text="Load engine", command=self.get_engine_data)
        self.load_file_button.grid(row=0, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Label to display the path of the loaded file
        self.file_path_label = ctk.CTkLabel(self.inputs_frame, text="No file has been loaded")
        self.file_path_label.grid(row=0, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Switch to enable pressure settings (initially disabled)
        self.pressureCheck_Box = ctk.CTkSwitch(self.inputs_frame, text="P1 - Mean Value (Pa)", command=self.toggle_slider, state="disabled")
        self.pressureCheck_Box.grid(row=1, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Slider to adjust pressure (initially disabled)
        self.pressureSlide_Bar = ctk.CTkSlider(self.inputs_frame, from_=0, to=100, command=self.update_entry)
        self.pressureSlide_Bar.grid(row=1, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")

        # Label for pressure input field
        self.pressure_label = ctk.CTkLabel(self.inputs_frame, text="P1 - Design point (Pa): ")
        self.pressure_label.grid(row=2, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Entry field for manual pressure input
        self.pressure_entry = ctk.CTkEntry(self.inputs_frame)
        self.pressure_entry.grid(row=2, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.pressure_entry.bind("<Return>", self.update_from_entry)

        # Label for resolution points input
        self.nPoints_label = ctk.CTkLabel(self.inputs_frame, text="Points - Resolution: ")
        self.nPoints_label.grid(row=3, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Entry field for resolution points input
        self.nPoints_entry = ctk.CTkEntry(self.inputs_frame)
        self.nPoints_entry.grid(row=3, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Label for time step input
        self.timeNormalization_label = ctk.CTkLabel(self.inputs_frame, text="Temp. Step (s): ")
        self.timeNormalization_label.grid(row=4, column=0, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Entry field for time step input
        self.timeNormalization_entry = ctk.CTkEntry(self.inputs_frame)
        self.timeNormalization_entry.grid(row=4, column=1, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Dropdown menu for selecting nozzle types
        nozzle_types = list(self.nozzleClasses.keys())
        self.nozzleTypeMenu = ctk.CTkOptionMenu(self.inputs_frame, values=nozzle_types, command=self.update_options)
        self.nozzleTypeMenu.grid(row=5, column=0, columnspan=2, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Scrollable frame for displaying nozzle-specific options
        self.nozzleOptions = ctk.CTkScrollableFrame(self.inputs_frame)
        self.nozzleOptions.grid(row=6, column=0, columnspan=2, padx=inputsPad, pady=inputsPad, sticky='nswe')

        # Frame for displaying the pressure graph
        self.pressureGraph_Frame = ctk.CTkFrame(self.inputs_frame)
        self.pressureGraph_Frame.grid(row=0, column=2, rowspan=7, padx=inputsPad, pady=inputsPad, sticky='nswe')
        self.pressureGraph_Frame.grid_rowconfigure(0, weight=1)
        self.pressureGraph_Frame.configure(fg_color="white")
        self.pressureGraph_Frame.grid_propagate(False)
        self.pressureGraph_Frame.bind("<Button-1>", self.update_plot)

        # Tabs for displaying nozzle characteristics and operational points
        self.resultsTabs = ctk.CTkTabview(self.content_frame)
        self.resultsTabs.grid(row=0, rowspan=3, column=1, padx=10, pady=10, sticky='nswe')
        self.resultsTabs.add("NOZZLE RESULTS") 
        self.resultsTabs.add("PERFORMANCE AND OPERATION")

        # Frame for displaying nozzle characteristics
        self.characteristics_frame = ctk.CTkFrame(self.resultsTabs.tab("NOZZLE RESULTS"))
        self.characteristics_frame.pack(fill="both", expand=True)
        self.characteristics_frame.grid_propagate(False)
        self.characteristics_frame.grid_columnconfigure(0, weight=1)
        self.characteristics_frame.grid_rowconfigure(0, weight=1)
        self.characteristics_frame.grid_rowconfigure(1, weight=1)
        self.characteristics_frame.grid_rowconfigure(2, weight=1)

        # Frame for displaying thrust graph
        self.thrustGraph_frame = ctk.CTkFrame(self.characteristics_frame)
        self.thrustGraph_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.thrustGraph_frame.grid_propagate(False)
        self.thrustGraph_frame.configure(fg_color='white')

        # Frame for displaying thrust coefficient graph
        self.thrustCoefGraph_frame = ctk.CTkFrame(self.characteristics_frame)
        self.thrustCoefGraph_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')
        self.thrustCoefGraph_frame.grid_propagate(False)
        self.thrustCoefGraph_frame.configure(fg_color='white')

        # Frame for displaying nozzle geometry graph
        self.nozzleGeoGraph_frame = ctk.CTkFrame(self.characteristics_frame)
        self.nozzleGeoGraph_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.nozzleGeoGraph_frame.grid_propagate(False)
        self.nozzleGeoGraph_frame.configure(fg_color='white')

        # Frame for displaying the operating points
        self.operating_points_frame = ctk.CTkFrame(self.resultsTabs.tab("PERFORMANCE AND OPERATION"))
        self.operating_points_frame.pack(fill="both", expand=True)
        self.operating_points_frame.grid_propagate(False)
        self.operating_points_frame.grid_columnconfigure(0, weight=100)
        self.operating_points_frame.grid_columnconfigure(1, weight=1)
        self.operating_points_frame.grid_rowconfigure(0, weight=50)
        self.operating_points_frame.grid_rowconfigure(1, weight=50)
        self.operating_points_frame.grid_rowconfigure(2, weight=1)

        # Frame for displaying the pressure map
        self.presMap_frame = ctk.CTkFrame(self.operating_points_frame)
        self.presMap_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.presMap_frame.grid_propagate(False)
        self.presMap_frame.configure(fg_color='white')

        # Frame for displaying the Mach map
        self.machMap_frame = ctk.CTkFrame(self.operating_points_frame)
        self.machMap_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.machMap_frame.grid_propagate(False)
        self.machMap_frame.configure(fg_color='white')

        # Frame for displaying numeric values
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

        # Label and entry for subsónic pressure ratio
        self.PR_Crit_1_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - Sub.")
        self.PR_Crit_1_Label.grid(row=0, column=0, padx=pad, pady=pad, sticky='nswe')
        self.PR_Crit_1_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR_Crit_1_Entry.grid(row=0, column=1, padx=pad, pady=pad, sticky='nswe')

        # Label and entry for near-sonic exit pressure ratio
        self.PR_Crit_2_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - NS Exit")
        self.PR_Crit_2_Label.grid(row=1, column=0, padx=pad, pady=pad, sticky='nswe')
        self.PR_Crit_2_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR_Crit_2_Entry.grid(row=1, column=1, padx=pad, pady=pad, sticky='nswe')

        # Label and entry for optimal pressure ratio
        self.PR_Crit_3_Label = ctk.CTkLabel(self.numericFrame, text="(Pe/P1t) - Op.")
        self.PR_Crit_3_Label.grid(row=2, column=0, padx=pad, pady=pad, sticky='nswe')
        self.PR_Crit_3_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR_Crit_3_Entry.grid(row=2, column=1, padx=pad, pady=pad, sticky='nswe')

        # Label and entry for expansion capacity ratio
        self.PR1_Label = ctk.CTkLabel(self.numericFrame, text="P0/P1t (Exp. Ratio)")
        self.PR1_Label.grid(row=0, column=2, padx=pad, pady=pad, sticky='nswe')
        self.PR1_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR1_Entry.grid(row=0, column=3, padx=pad, pady=pad, sticky='nswe')

        # Label and entry for exit/combustion chamber pressure ratio
        self.PR2_Label = ctk.CTkLabel(self.numericFrame, text="Pe/P1t (Exit/Comb.)")
        self.PR2_Label.grid(row=1, column=2, padx=pad, pady=pad, sticky='nswe')
        self.PR2_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR2_Entry.grid(row=1, column=3, padx=pad, pady=pad, sticky='nswe')

        # Label and entry for exit/ambient pressure ratio
        self.PR3_Label = ctk.CTkLabel(self.numericFrame, text="Pe/P0 (Exit/Amb.)")
        self.PR3_Label.grid(row=2, column=2, padx=pad, pady=pad, sticky='nswe')
        self.PR3_Entry = ctk.CTkEntry(self.numericFrame, height=entry_height)
        self.PR3_Entry.grid(row=2, column=3, padx=pad, pady=pad, sticky='nswe')

        # Additional numeric fields
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

        # Frame for pressure sliders with height set
        self.pressureSlider_frame = ctk.CTkFrame(self.numericFrame, height=75)
        self.pressureSlider_frame.grid(row=3, column=0, columnspan=6, padx=5, pady=5, sticky='nswe')
        self.pressureSlider_frame.grid_rowconfigure(0, weight=1)
        self.pressureSlider_frame.grid_rowconfigure(1, weight=1)
        self.pressureSlider_frame.grid_columnconfigure(0, weight=1)
        self.pressureSlider_frame.grid_columnconfigure(1, weight=10)
        self.pressureSlider_frame.grid_columnconfigure(2, weight=1)
        self.pressureSlider_frame.grid_propagate(False)  # Prevent resizing

        # Label and slider for P1t
        self.offDesingPressure_label = ctk.CTkLabel(self.pressureSlider_frame, text="P1t")
        self.offDesingPressure_label.grid(row=0, column=0, padx=pad, pady=pad, sticky='nswe')
        self.offDesingPressureSlider = ctk.CTkSlider(self.pressureSlider_frame, from_=1e-3, to=1, orientation='horizontal', number_of_steps=1000)
        self.offDesingPressureSlider.set(1)
        self.offDesingPressureSlider.bind('<B1-Motion>', self.updatePercentLabels)
        self.offDesingPressureSlider.bind('<B1-Motion>', self.updateMapPlots)  # Update map plots as slider moves
        self.offDesingPressureSlider.grid(row=0, column=1, padx=pad, pady=pad, sticky='nswe')

        # Label and slider for P0
        self.offDesingPressure0_label = ctk.CTkLabel(self.pressureSlider_frame, text="P0")
        self.offDesingPressure0_label.grid(row=1, column=0, padx=pad, pady=pad, sticky='nswe')
        self.offDesingPressure0Slider = ctk.CTkSlider(self.pressureSlider_frame, from_=1e-3, to=1, orientation='horizontal', number_of_steps=1000)
        self.offDesingPressure0Slider.set(1)
        self.offDesingPressure0Slider.bind('<B1-Motion>', self.updatePercentLabels)
        self.offDesingPressure0Slider.bind('<B1-Motion>', self.updateMapPlots)
        self.offDesingPressure0Slider.grid(row=1, column=1, padx=pad, pady=pad, sticky='nswe')

        # Initial percentage labels for the sliders
        p1p_init = f"{self.offDesingPressureSlider.get():.2f}"
        p0p_init = f"{self.offDesingPressure0Slider.get():.2f}"
        self.offDesingPressurePercent_label = ctk.CTkLabel(self.pressureSlider_frame, text=p1p_init)
        self.offDesingPressurePercent_label.grid(row=0, column=2, padx=pad, pady=pad, sticky='nswe')
        self.offDesingPressure0Percent_label = ctk.CTkLabel(self.pressureSlider_frame, text=p0p_init)
        self.offDesingPressure0Percent_label.grid(row=1, column=2, padx=pad, pady=pad, sticky='nswe')

        # Results frame
        self.results_frame = ctk.CTkFrame(self.content_frame)
        self.results_frame.grid(row=1, rowspan=3, column=0, padx=10, pady=10, sticky='nswe')
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.results_frame.grid_propagate(False)

        # Scrollable frame for displaying numeric results
        self.numericResults_frame = ctk.CTkScrollableFrame(self.results_frame)
        self.numericResults_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.numericResults_frame.grid_columnconfigure(0, weight=1)
        self.numericResults_frame.grid_columnconfigure(1, weight=1)

        # Label for numeric results
        self.numericResults_label = ctk.CTkLabel(self.numericResults_frame, text="Resultados Numéricos")
        self.numericResults_label.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        self.resultsEntries = {}

        # Crear TabView
        self.tabview = ctk.CTkTabview(self.results_frame)
        self.tabview.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        # Añadir pestaña
        self.tabview.add("TIME RESULTS")
        self.tabview.add("GEOMETRY")

        # Create ScrollableFrame and Treeview in the "Results" tab
        self._create_treeview_in_tab(self.tabview.tab("TIME RESULTS"), [("Time (s)", "Thrust (kg)", "CF")])
        
        # Create Scrollableframe and Treeview in the "Geometry" tab
        self._create_treeview_in_tab(self.tabview.tab("GEOMETRY"), [("X (m)", "Y (m)", "AR")])

    
        # Frame for calculation and export buttons
        self.calcExport_frame = ctk.CTkFrame(self.content_frame)
        self.calcExport_frame.grid(row=3, column=1, padx=10, pady=10, sticky='nswe')
        self.calcExport_frame.grid_columnconfigure(0, weight=1)
        self.calcExport_frame.grid_columnconfigure(1, weight=2)
        self.calcExport_frame.grid_rowconfigure(0, weight=1)

        # Button to calculate results
        self.calcButton = ctk.CTkButton(self.calcExport_frame, text="CALCULATE", command=self.calculate_n_show)
        self.calcButton.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        # Button to export data
        self.exportData = ctk.CTkButton(self.calcExport_frame, text="EXPORT", command=self.export_results)
        self.exportData.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        # Dictionary to store specific inputs
        self.specInputs_entries = {}

        # Create widgets for different nozzle types
        self.create_widgets_for_all_nozzle_types()

        # Initialize nozzle selection
        self.selection = nozzle_types[0]  # Set the first nozzle type as default
        self.update_options(self.selection)


    def calculate_n_show(self) -> None:
        """
        Gathers user inputs, initializes the nozzle calculation process, and runs
        the step-by-step calculation while updating the progress window.
        """
        # Create a progress window and reset progress
        self.create_progress_window()
        self.progress_var.set(0)

        # Get engine configuration and user inputs
        engine_config = self.file_path_label.cget("text")
        nozzle_config = self.nozzleTypeMenu.get()
        P1 = float(self.pressure_entry.get())
        n = float(self.nPoints_entry.get())
        dt = float(get_entry_value(self.timeNormalization_entry))
        defaultState = self.pressureCheck_Box.get()

        # Determine total steps based on the provided time step
        if not dt:
            self.total_steps = len(self.P)  # Use predefined pressure data if dt is not provided
        else:
            self.total_steps = len(np.arange(self.t[0], self.t[-1], dt))

        self.current_step = 0
        self.calculation_running = True

        # Get the selected nozzle class
        selected_nozzle_class = self.nozzleClasses.get(nozzle_config)

        # Extract dynamic input values for the selected nozzle
        specInputs = {}
        for entry_name, widget_info in self.specInputs_entries[self.selection].items():
            entry_widget = widget_info[1]  # Entry widget (second element of the tuple)
            try:
                specInputs[entry_name] = float(entry_widget.get())  # Get numeric value from entry
            except ValueError:
                messagebox.showerror("Error", "Por favor, introduce valores numéricos válidos.", parent=self.content_frame)
                return

        # Instantiate the selected nozzle with parameters
        self.calculatedNozzle = selected_nozzle_class(defaultState, P1, n, dt, engine_config, specInputs)
        self.calculatedNozzle.calculation_running = self.calculation_running  # Pass control variable

        # Execute the calculation step by step
        loop_func = self.calculatedNozzle.run_step
        self.run_calculations_step(loop_func)


    def run_calculations_step(self, loop_func: callable) -> None:
        """
        Executes a single step of the calculations using the provided loop function
        and updates the progress bar. Continues until all steps are completed or
        the calculation is stopped.

        Args:
            loop_func: A function to execute for each calculation step.
        """
        if self.current_step < self.total_steps and self.calculation_running:
            loop_func(self.current_step)

            # Update progress bar
            progress = (self.current_step + 1) / self.total_steps if self.total_steps > 0 else 1
            self.progress_var.set(progress)
            self.progress_label.configure(text=f"{int(progress * 100)}%")

            self.current_step += 1
            self.content_frame.after(1, lambda: self.run_calculations_step(loop_func))
        else:
            self.on_calculations_done()


    def on_calculations_done(self) -> None:
        """
        Handles actions to be performed after calculations are completed.
        Destroys the progress window, updates graphs, and displays results.
        """
        if self.calculation_running:
            self.progress_window.destroy()
            self.calculation_running = False

            # Generate figures from nozzle calculations
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

            # Insert figures into their respective frames
            for i, (fig, frame) in enumerate(zip(figs, frames)):
                insert_fig(fig, frame)

        self.result_array = self.calculatedNozzle.calculated_results()
        self.update_results_entries(self.result_array)


    def on_progress_window_close(self) -> None:
        """
        Handles the event when the progress window is closed.
        Stops the ongoing calculations and destroys the progress window.
        """
        self.calculation_running = False
        self.progress_window.destroy()


    def create_progress_window(self):
        """
        Create and display a progress window that shows the progress of a calculation.

        The window contains a progress bar and a label indicating the percentage of completion.
        It is designed to be modal, preventing interaction with the main window while it is open.
        """

        # Create a top-level window for displaying progress
        self.progress_window = ctk.CTkToplevel(self.content_frame)
        self.progress_window.title("Progress")

        self.progress_var = ctk.DoubleVar()  # Variable to track progress percentage

        # Frame for the progress bar and percentage label
        self.progress_frame = ctk.CTkFrame(self.progress_window)
        self.progress_frame.grid(padx=20, pady=20, sticky='nswe')

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

        # Percentage label
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0%")
        self.progress_label.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        self.progress_frame.grid_columnconfigure(0, weight=1)  # Configure column weight for resizing

        # Calculate the size of the progress_frame to adjust the window
        self.progress_frame.update_idletasks()  # Update layout information
        frame_width = self.progress_frame.winfo_width() * 1.3  # Frame width
        frame_height = self.progress_frame.winfo_height() * 2  # Frame height

        # Calculate the center of the screen for window positioning
        screen_width = self.progress_window.winfo_screenwidth()
        screen_height = self.progress_window.winfo_screenheight()
        position_top = int(screen_height / 2 - frame_height / 2)  # Top position
        position_right = int(screen_width / 2 - frame_width / 2)  # Right position

        # Set the window size and position
        self.progress_window.geometry(f"{frame_width}x{frame_height}+{position_right}+{position_top}")

        self.progress_window.transient(self.content_frame)  # Make the progress window modal
        self.progress_window.grab_set()  # Ensure the progress window is active

        # Handle the close event of the progress window
        self.progress_window.protocol("WM_DELETE_WINDOW", self.on_progress_window_close)


    def update_progress(self, progress: float):
        """
        Update the progress bar and percentage label in the progress window.

        Args:
            progress (float): A value between 0 and 1 representing the progress percentage.
        """
        # Set the current value of the progress bar
        self.progress_var.set(progress)

        # Update the label to display the current progress as a percentage
        self.progress_label.configure(text=f"{int(progress * 100)}%")

   
    def updatePercentLabels(self, event=None):
        """
        Update the percentage labels for the off-design pressure sliders.

        This method is called when the sliders are moved to display the current values
        of the pressures as formatted strings.
        
        Args:
            event (optional): The event that triggered the update (default is None).
        """
        # Get the current value of the first pressure slider and format it to three decimal places
        p1p_update = f"{float(self.offDesingPressureSlider.get()):.3f}"

        # Get the current value of the second pressure slider and format it to three decimal places
        p0p_update = f"{float(self.offDesingPressure0Slider.get()):.3f}"

        # Update the label displaying the percentage for the first pressure slider
        self.offDesingPressurePercent_label.configure(text=p1p_update)

        # Update the label displaying the percentage for the second pressure slider
        self.offDesingPressure0Percent_label.configure(text=p0p_update)

        
    def updateMapPlots(self, event=None):
        """
        Update the operational point plots and relevant entries based on the current slider values.

        This method retrieves values from the pressure sliders, performs calculations
        to update various performance metrics, and displays the results on the GUI.
        
        Args:
            event (optional): The event that triggered the update (default is None).
        """
        try:
            # Calculate the off-design pressures based on slider values
            p0_value = self.offDesingPressure0Slider.get() * self.calculatedNozzle.P0
            slider_value = self.offDesingPressureSlider.get()  # Get the slider value (between 0 and 1)
            min_pressure = min(self.calculatedNozzle.P_t)  # Get the minimum value of P_t
            max_pressure = max(self.calculatedNozzle.P_t)  # Get the maximum value of P_t

            # Linear interpolation between the minimum and maximum pressures
            p1_value = min_pressure + slider_value * (max_pressure - min_pressure)
            
            # Calculate operational points
            thrust_value = self.calculatedNozzle.opPoint_plot(p1_value, p0_value)["F"]
            pe_value = self.calculatedNozzle.opPoint_plot(p1_value, p0_value)["Pe"]
            
            # Generate pressure and Mach number plots
            pres_fig = self.calculatedNozzle.pres_plot(p1_value, p0_value)
            mach_fig = self.calculatedNozzle.mach_plot(p1_value, p0_value)

            # Update entry labels with calculated values
            p0_p1_update = f"{(p0_value / p1_value):.4f}"
            pe_p1_update = f"{(pe_value / p1_value):.4f}"
            pe_p0_update = f"{(pe_value / p0_value):.4f}"
            thrst_update = f"{thrust_value:.4f}"

            # Get critical pressure ratios from entries
            PRC0_value = float(self.PR_Crit_0_Entry.get())
            PRC1_value = float(self.PR_Crit_1_Entry.get())
            PRC2_value = float(self.PR_Crit_2_Entry.get())
            PRC3_value = float(self.PR_Crit_3_Entry.get())

            # Update the entry fields with the calculated ratios
            self.PR1_Entry.delete(0, tk.END)
            self.PR1_Entry.insert(0, p0_p1_update)
            self.PR2_Entry.delete(0, tk.END)
            self.PR2_Entry.insert(0, pe_p1_update)
            self.PR3_Entry.delete(0, tk.END)
            self.PR3_Entry.insert(0, pe_p0_update)
            self.ThrustOff_Entry.delete(0, tk.END)
            self.ThrustOff_Entry.insert(0, thrst_update)

            # Determine the operating condition based on calculated pressure ratios
            if float(p0_p1_update) > PRC0_value:
                operation_tag = 'Subsonic'  
            elif PRC2_value < float(pe_p1_update) < PRC1_value:
                operation_tag = 'Normal Shock Inside'
            elif abs(float(pe_p1_update) - PRC3_value) < 1e-2 and pe_value < p0_value:
                operation_tag = 'Over-Expanded'
            elif abs(float(pe_p1_update) - PRC3_value) < 1e-2 and pe_value == p0_value:
                operation_tag = 'Design-Point'
            elif abs(float(pe_p1_update) - PRC3_value) < 1e-2 and pe_value > p0_value:
                operation_tag = 'Under-Expanded'
            else:
                operation_tag = 'Normal Shock Exit'

            # Update the operation point entry with the determined tag
            self.OperationPoint_Entry.delete(0, tk.END)
            self.OperationPoint_Entry.insert(0, operation_tag)

            # Insert the generated figures into the respective frames
            insert_fig(pres_fig, self.presMap_frame, resize='Auto')
            insert_fig(mach_fig, self.machMap_frame, resize='Auto')

        except Exception as e:
            print("An error occurred:", e)
            traceback.print_exc()


    def add_labels_and_entries(self, frame, data_list):
        """
        Create and display result labels and entry fields in the specified frame.

        This method clears previous results and generates new labels and entry fields
        based on the provided data list. Each label corresponds to an entry for user input.

        Args:
            frame (ctk.CTkFrame): The frame in which to add the labels and entries.
            data_list (list): A list of strings containing the label texts for the entries.
        """
        # Clear previous results
        if hasattr(self, 'result_labels'):
            for widget in self.result_labels:
                widget.grid_forget()

        self.result_labels = []  # Store the created label widgets
        self.resultsEntries = {}  # Dictionary to hold entry widgets

        # Create result labels and entry fields
        for i, label_text in enumerate(data_list):
            # Create and place the label
            label = ctk.CTkLabel(frame, text=label_text)
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky='w')

            # Create and place the entry field
            entry = ctk.CTkEntry(frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky='we')
            self.resultsEntries[label_text] = entry  # Store the entry in the dictionary

            # Save the created widgets for later visibility management
            self.result_labels.append(label)
            self.result_labels.append(entry)


    def update_results_entries(self, result_array):
        """
        Update the result entry fields and treeviews with new calculation results.

        This method dynamically updates the entry fields for results and populates
        the associated treeviews for both time results and geometry with the values
        from the result_array.

        Args:
            result_array (list): A nested list containing results, where:
                - result_array[0] contains scalar results for entries.
                - result_array[1] contains results for the time results treeview.
                - result_array[2] contains results for the geometry treeview.
                - result_array[3] contains critical pressure values.
        """
        # Update the result entry fields dynamically
        for i, key in enumerate(self.resultsEntries):
            entry = self.resultsEntries.get(key)
            if entry:
                entry.delete(0, tk.END)  # Clear current entry value
                value = result_array[0][i]  # Access the value from the result array
                formatted_value = f"{value:.4e}" if value >= 1e6 else f"{value:.4f}"  # Format value
                entry.insert(0, formatted_value)  # Insert the formatted value into the entry

        # List of entries for critical pressure values
        rightResults_entries = [
            self.PR_Crit_0_Entry,
            self.PR_Crit_1_Entry,
            self.PR_Crit_2_Entry,
            self.PR_Crit_3_Entry
        ]

        for i, entry in enumerate(rightResults_entries):
            entry.delete(0, tk.END)  # Clear current entry value
            value = result_array[3][i]  # Get the corresponding critical pressure value
            entry.insert(0, f"{value:.4f}")  # Insert the formatted value

        # Update the "TIME RESULTS" treeview
        results_treeview = self.tabview.tab("TIME RESULTS").winfo_children()[0].winfo_children()[0]
        # Clear the current contents of the treeview
        for item in results_treeview.get_children():
            results_treeview.delete(item)

        # Populate the treeview with new data
        for row in zip(*result_array[1]):
            formatted_row = [f"{value:.4e}" if value >= 1e6 else f"{value:.4f}" for value in row]
            results_treeview.insert("", "end", values=formatted_row)  # Insert new row

        # Update the "GEOMETRY" treeview
        geometry_treeview = self.tabview.tab("GEOMETRY").winfo_children()[0].winfo_children()[0]
        # Clear the current contents of the treeview
        for item in geometry_treeview.get_children():
            geometry_treeview.delete(item)

        # Populate the geometry treeview with new data
        for row in zip(*result_array[2]):
            formatted_row = [f"{value:.6f}" for value in row]
            geometry_treeview.insert("", "end", values=formatted_row)  # Insert new row

            
    def get_entryResults_values(self):
        """
        Retrieve the values from the result entry fields.

        This method collects and returns the current values from the entry fields 
        stored in the resultsEntries dictionary as a dictionary.

        Returns:
            dict: A dictionary where keys are the labels of the entries and 
                values are the corresponding entry values as strings.
        """
        # Retrieve the values from the entries stored in the resultsEntries dictionary
        values = {key: entry.get() for key, entry in self.resultsEntries.items()}
        return values


    def _create_treeview_in_tab(self, tab, columns_list):
        """
        Create a Treeview widget within a specified tab.

        This method initializes and configures a Treeview widget for displaying
        tabular data. It sets up the columns, headings, and scrollbar for the Treeview.

        Args:
            tab (CTkFrame): The tab where the Treeview will be placed.
            columns_list (list of list): A list of lists, where each inner list
                                        contains the column names for a Treeview.
        """
        for i, columns in enumerate(columns_list):
            # Create a frame for the Treeview
            tree_frame = ctk.CTkFrame(tab)
            tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Initialize the Treeview with the specified columns
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
            tree.grid(row=0, column=0, sticky="nsew")

            # Configure each column's heading and width
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=100)

            # Add a vertical scrollbar for the Treeview
            tree_scrollbar = ctk.CTkScrollbar(tree_frame, orientation="vertical", command=tree.yview)
            tree_scrollbar.grid(row=0, column=1, sticky="ns")
            tree.configure(yscrollcommand=tree_scrollbar.set)

        # Configure the tab layout
        tab.grid_rowconfigure(len(columns_list) - 1, weight=1)
        tab.grid_columnconfigure(0, weight=1)


    def get_engine_data(self, on_load: bool = False, file: str = None) -> None:
        """
        Load engine data from a JSON file.

        This method either prompts the user to select a JSON file or uses a provided file path 
        to load engine data. It extracts various parameters and results from the JSON structure 
        and updates the corresponding attributes and UI elements.

        Args:
            on_load (bool): Indicates whether the method is called on load. 
                            If False, a file dialog will open to select a file.
            file (str): Optional; the file path to load if on_load is True.

        Returns:
            None
        """
        if not on_load:
            file_path = filedialog.askopenfilename(defaultextension=".json", 
                                                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        else:
            file_path = file

        if file_path:
            self.file_name = os.path.basename(file_path)

            with open(file_path, 'r') as file:
                self.engine_Data = json.load(file)

            try:
                # Extracting input parameters from the JSON data
                self.propellant = self.engine_Data["inputs"]["Propellant"]
                self.P0         = self.engine_Data["inputs"]["P0"]
                self.Rt         = self.engine_Data["inputs"]["Rt"]

                # Extracting result metrics from the JSON data
                self.meanP      = self.engine_Data["results"]["meanPressure"]
                self.maxP       = self.engine_Data["results"]["maxPressure"]
                self.minP       = self.engine_Data["results"]["minPressure"]

                self.meanG      = self.engine_Data["results"]["meanMassFlow"]
                self.maxG       = self.engine_Data["results"]["maxMassFlow"]
                self.minG       = self.engine_Data["results"]["minMassFlow"]

                self.mass       = self.engine_Data["results"]["totalMass"]
                self.time       = self.engine_Data["results"]["totalTime"]

                # Extracting time and data arrays
                self.t          = self.engine_Data["results"]["tree_data"]["Time (s)"]
                self.P          = self.engine_Data["results"]["tree_data"]["Pressure (Pa)"]
                self.G          = self.engine_Data["results"]["tree_data"]["Mass Flow (kg/s)"]
                self.M          = self.engine_Data["results"]["tree_data"]["Mass (kg)"]

                self.file_path_label.configure(text=self.file_name)
            except Exception as e:
                # Handle error in case of invalid file
                messagebox.showerror("Error", "Invalid file.", parent=self.content_frame)
                self.file_path_label.configure(text="Invalid File")
                return

            if not on_load:
                # Update UI elements if not loading on startup
                self.update_slider()
                self.pressureCheck_Box.configure(state="normal")
                self.pressureCheck_Box.select()
                self.toggle_slider()
            else:
                # Adjust slider range if loading on startup
                self.pressureSlide_Bar.configure(from_=self.minP, to=self.maxP)
                

    def update_slider(self) -> None:
        """
        Update the pressure slider's range and position.

        This method configures the pressure slider to reflect the minimum and maximum pressure 
        values based on the loaded engine data. It also sets the slider's current value to the 
        mean pressure.

        Returns:
            None
        """
        if self.P:
            # Configure the slider's range and set the current value to the mean pressure
            self.pressureSlide_Bar.configure(from_=self.minP, to=self.maxP)
            self.pressureSlide_Bar.set(self.meanP)
            self.update_entry()


    def update_entry(self, value: float = None) -> None:
        """
        Update the pressure entry field based on the state of the checkbox.

        If the checkbox is selected, the entry is updated with the mean pressure. 
        If the checkbox is not selected, the entry is updated with the current value 
        from the pressure slider. This method also updates the associated plot.

        Args:
            value (float, optional): An optional value to set. Defaults to None.

        Returns:
            None
        """
        if self.pressureCheck_Box.get() == 1:
            # Set the entry to the mean pressure value
            self.pressure_entry.delete(0, tk.END)
            self.pressure_entry.insert(0, str(self.meanP))
        else:
            # Set the entry to the current slider value
            self.pressure_entry.delete(0, tk.END)
            self.pressure_entry.insert(0, str(self.pressureSlide_Bar.get()))

        # Update the plot to reflect the new entry value
        self.update_plot()


    def update_from_entry(self, event: tk.Event) -> None:
        """
        Update the slider value based on the input from the pressure entry.

        This method reads the pressure value from the entry field and updates 
        the slider if the value is within the defined limits. It also triggers 
        an error message if the input is invalid.

        Args:
            event (tk.Event): The event that triggered this method, typically from the entry widget.

        Returns:
            None
        """
        try:
            pressure_value = float(self.pressure_entry.get())
            # Check if the entered pressure value is within the valid range
            if pressure_value < self.minP or pressure_value > self.maxP:
                messagebox.showerror("Invalid Input Value", f"The value must be between {self.minP} and {self.maxP}.")
            else:
                # Set the slider to the new pressure value and update the plot
                self.pressureSlide_Bar.set(pressure_value)
                self.update_plot()
        except ValueError:
            # Handle the case where the input cannot be converted to a float
            messagebox.showerror("Invalid Input Value", "Please enter a valid number.")


    def toggle_slider(self) -> None:
        """
        Toggle the state of the pressure slider and entry based on the checkbox state.

        If the checkbox is checked, the slider and entry are disabled, and the 
        slider is set to the mean pressure value. If unchecked, the slider 
        is enabled and the entry can be edited.

        Returns:
            None
        """
        if self.pressureCheck_Box.get() == 1:
            # Disable the slider and entry, and set slider to mean pressure
            self.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")
            self.update_entry()
            self.pressure_entry.configure(state="disabled")
            self.pressureSlide_Bar.set(self.meanP)
        else:
            # Enable the slider and entry, allowing for user input
            self.pressureSlide_Bar.configure(state="normal", button_color="#1F6AA5", button_hover_color="#144870")
            self.update_entry()
            self.pressure_entry.configure(state="normal")

            

    def create_widgets_for_all_nozzle_types(self) -> None:
        """
        Create widgets for each nozzle type once and store them in a dictionary.

        This method generates labels and entry fields for all nozzle types defined
        in the nozzleClasses attribute, storing them in the specInputs_entries
        dictionary for later use. Initially, the widgets are hidden.

        Returns:
            None
        """
        for nozzle_type in self.nozzleClasses.keys():
            self.specInputs_entries[nozzle_type] = {}
            selected_nozzle_class = self.nozzleClasses.get(nozzle_type)
            input_labels = selected_nozzle_class.get_input_labels()

            # Create and store widgets (initially hidden)
            for i, (label_text, entry_name) in enumerate(input_labels.items()):
                label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
                entry = ctk.CTkEntry(self.nozzleOptions)
                self.specInputs_entries[nozzle_type][entry_name] = (label, entry, i)

                # Initially hide the widgets
                label.grid_forget()
                entry.grid_forget()


    def update_options(self, selection: str) -> None:
        """
        Update the UI based on the selected nozzle option.

        This method hides existing widgets associated with the previous selection,
        updates the current selection, and displays the appropriate widgets for
        the newly selected nozzle type. It also dynamically creates result labels
        and entries for the selected option.

        Args:
            selection (str): The selected nozzle type.

        Returns:
            None
        """
        # Hide widgets for the current selection if they exist
        if self.selection:
            self.hide_widgets()
            self.hide_result_labels()  # Hide previous result labels

        # Update the current selection
        self.selection = selection

        # If widgets for this option have already been created, simply show them
        if self.selection in self.specInputs_entries:
            self.show_widgets()
        else:
            # Create widgets for this new option
            self.create_widgets_for_option()

        # Create result labels dynamically for the new option
        selected_nozzle_class = self.nozzleClasses.get(self.selection)
        result_labels = selected_nozzle_class.get_result_labels()
        self.add_labels_and_entries(self.numericResults_frame, result_labels)



    def hide_result_labels(self) -> None:
        """
        Hide the previous result labels.

        This method checks if there are any existing result labels
        and hides them from the UI.

        Returns:
            None
        """
        if hasattr(self, 'result_labels'):
            for widget in self.result_labels:
                widget.grid_forget()



    def hide_widgets(self) -> None:
        """
        Hide the widgets (labels and entries) for the current option.

        This method checks if the current selection has associated widgets
        and hides them from the UI using `grid_forget()`.

        Returns:
            None
        """
        if self.selection in self.specInputs_entries:
            for widget_info in self.specInputs_entries[self.selection].values():
                label_widget = widget_info[0]  # Extract the label
                entry_widget = widget_info[1]  # Extract the entry
                label_widget.grid_forget()  # Hide the label
                entry_widget.grid_forget()  # Hide the entry



    def show_widgets(self) -> None:
        """
        Show the widgets (labels and entries) for the current option.

        This method checks if the current selection has associated widgets
        and displays them in the UI using `grid()`.

        Returns:
            None
        """
        if self.selection in self.specInputs_entries:
            for widget_info in self.specInputs_entries[self.selection].values():
                label_widget, entry_widget, row = widget_info  # Extract label, entry, and row
                label_widget.grid(row=row, column=0, padx=10, pady=5, sticky="nsew")
                entry_widget.grid(row=row, column=1, padx=10, pady=5, sticky="nsew")



    def create_widgets_for_option(self) -> None:
        """
        Create and display the widgets (labels and entries) for the selected option.

        This method retrieves the corresponding nozzle class based on the current
        selection and creates input fields dynamically according to the provided labels.

        Returns:
            None
        """
        # Get the selected nozzle class from the dictionary
        selected_nozzle_class = self.nozzleClasses.get(self.selection)

        if not selected_nozzle_class:
            messagebox.showerror("Error", "No corresponding class found.", parent=self.content_frame)
            return

        # Create inputs dynamically based on the provided labels
        input_labels = selected_nozzle_class.get_input_labels()

        # Create a dictionary to store the labels and entries for the new option
        self.specInputs_entries[self.selection] = {}

        for i, (label_text, entry_name) in enumerate(input_labels.items()):
            label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
            entry = ctk.CTkEntry(self.nozzleOptions)

            # Place the widgets and store them in the dictionary
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")

            # Save the reference of the label, entry, and its row
            self.specInputs_entries[self.selection][entry_name] = (label, entry, i)

        # Add result labels dynamically
        result_labels = selected_nozzle_class.get_result_labels()
        self.add_labels_and_entries(self.numericResults_frame, result_labels)



    def update_plot(self, event: Optional[tk.Event] = None) -> None:
        """
        Update the pressure plot based on the current pressure values and time.

        This method creates a new plot showing the pressure profile over time
        and marks the selected pressure value on the graph.

        Args:
            event (Optional[tk.Event]): An optional event parameter (default is None).

        Returns:
            None
        """
        try:
            # Create a figure and an axis
            height, width = self.pressureGraph_Frame.winfo_height() / 100, self.pressureGraph_Frame.winfo_width() / 100
            fig, ax = plt.subplots(figsize=(width, height))

            # Plot the pressure profile
            ax.plot(self.t, self.P)

            # Add title and labels
            ax.set_title("Pressure Profile (Pa)")
            ax.set_xlabel("Time (s)")
            ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
            ax.set_aspect('auto')

            # Get the current pressure value from the entry
            pressure_value = float(self.pressure_entry.get())

            # Interpolate the corresponding time value for the selected pressure
            interpolate_time = interp1d(self.P, self.t, bounds_error=False, fill_value="extrapolate")
            time_value = interpolate_time(pressure_value)

            # Plot the selected pressure point
            ax.plot(time_value, pressure_value, 'ro', label=f"{(pressure_value / self.maxP):.3f}")
            ax.legend()

        except Exception:
            # In case of an error, create an empty plot
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()

        # Insert the plot into the specified frame
        insert_fig(fig, frame=self.pressureGraph_Frame, resize='Auto')

        
    def export_results(self) -> None:
        """
        Export results to a JSON file.

        This method collects geometry, time results, and additional input data,
        and saves them in a JSON file at the user-specified location.

        Returns:
            None
        """
        working_path = get_dir_path()
        
        # Check if a working directory was selected
        if not working_path:
            messagebox.showerror("Error", "No se ha seleccionado un directorio de trabajo.", parent=self.content_frame)
            return
        
        # Ask the user for the file name
        file_name = simpledialog.askstring("Guardar archivo", "Introduce el nombre del archivo:", parent=self.content_frame)
        
        if file_name:
            # Ensure the file name ends with '.json'
            if not file_name.endswith('.json'):
                file_name += '.json'
            
            # Create a folder named "Nozzles" within the working directory
            results_folder = os.path.join(working_path, "Nozzles")
            os.makedirs(results_folder, exist_ok=True)

            # Construct the full file path
            file_path = os.path.join(results_folder, file_name)

            # Collect data from the "GEOMETRY" tab's Treeview
            geo_tree = self.tabview.tab("GEOMETRY").winfo_children()[0].winfo_children()[0]
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

            # Collect data from the "TIME RESULTS" tab's Treeview
            results_tree = self.tabview.tab("TIME RESULTS").winfo_children()[0].winfo_children()[0]
            timeResults_data = {
                "Time (s)": [],
                "Thrust (kg)": [],
                "CF": []
            }

            for item in results_tree.get_children():
                values = results_tree.item(item)["values"]
                timeResults_data["Time (s)"].append(float(values[0]))
                timeResults_data["Thrust (kg)"].append(float(values[1]))
                timeResults_data["CF"].append(float(values[2]))

            # Collect additional input data
            inputs = {
                "NozzleConfig": self.nozzle_config,
                "DefaultCheck": self.defaultState,
                "P1": self.P1,
                "n": self.n,
                "EngineConfig": self.engine_config,
                "specInputs": self.specInputs
            }

            # Collect calculated results
            calculatedResults = {}
            for i, key in enumerate(self.resultsEntries):
                entry = self.resultsEntries.get(key)
                if entry:
                    # Add the entry value to calculatedResults
                    calculatedResults[key] = float(get_entry_value(entry))
            
            # Add specific calculated results
            calculatedResults["PR_Crit0"] = float(get_entry_value(self.PR_Crit_0_Entry))
            calculatedResults["PR_Crit1"] = float(get_entry_value(self.PR_Crit_1_Entry))
            calculatedResults["PR_Crit2"] = float(get_entry_value(self.PR_Crit_2_Entry))
            calculatedResults["PR_Crit3"] = float(get_entry_value(self.PR_Crit_3_Entry))

            # Combine all results into a single dictionary
            results = {
                "Inputs": inputs,
                "geometry_data": geo_data,
                "timeResults_data": timeResults_data,
                "calculatedResults": calculatedResults
            }

            # Save data to a JSON file
            with open(file_path, 'w') as json_file:
                json.dump(results, json_file, indent=4)
            
            # Show a confirmation message
            messagebox.showinfo("Save file", f"File saved in {file_path}", parent=self.content_frame)