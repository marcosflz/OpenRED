from imports import *
from functions import *

from front_modules.front_doc      import *
from front_modules.front_adTemp   import *
from front_modules.front_chemWin  import *
from front_modules.front_propWin  import *
from front_modules.front_propDes  import *
from front_modules.front_nozDes   import *
from front_modules.front_cad      import *
from front_modules.front_cfd      import *
from front_modules.front_test     import *
from front_modules.front_post      import *

global main_frame
global adiabatic_module_instance
global engineDesing_module_instance
global nozzleDesing_module_instance
global EngineCADDesing_module_instance
global TestingBed_module_instance
global CFD_module_instance

global working_path
global file_path

initialize_database()

closing = False
working_path = None
file_path = None


def open_directory():
    """
    Opens a dialog for the user to select a directory.
    If a directory is selected, it sets the working path (working_path) 
    and creates a path for a configuration file named "config.json".
    Then, it saves the selected directory path and loads the configuration from that directory.

    Global variables:
    - working_path: The path of the selected directory.
    - file_path: Full path to the "config.json" configuration file.
    """
    # Declare the global variables to be modified
    global working_path
    global file_path
    
    # Open a dialog for selecting a directory
    working_path = filedialog.askdirectory()
    
    # If a directory is selected (working_path is not empty)
    if working_path:
        # Construct the full path for the "config.json" file in the selected directory
        file_path = os.path.join(working_path, "config.json")
        
        # Save the selected directory path
        save_dir_path(working_path)
        
        # Load the configuration from the file in the selected directory
        load_configuration(working_path)


def open_on_saving_directory():
    """
    Opens a dialog for the user to select a directory for saving.
    If a directory is selected and it doesn't already contain a "config.json" file, 
    the function saves the directory path and returns True.
    If the "config.json" file already exists, it shows an error message and returns False.

    Global variables:
    - working_path: The path of the selected directory.
    - file_path: Full path to the "config.json" configuration file.
    
    Returns:
    - True: If no "config.json" file exists in the selected directory and the directory is saved.
    - False: If a "config.json" file already exists in the selected directory.
    """
    # Declare the global variables to be modified
    global working_path
    global file_path
    global main_frame
    
    # Open a dialog for selecting a directory
    working_path = filedialog.askdirectory()
    
    # If a directory is selected (working_path is not empty)
    if working_path:
        # Construct the full path for the "config.json" file in the selected directory
        file_path = os.path.join(working_path, "config.json")
        
        # Check if the "config.json" file already exists in the selected directory
        if os.path.isfile(file_path):
            # Show an error message if the file exists and return False
            messagebox.showerror(
                "Directory Error", 
                "A configuration file already exists. Please select another directory.",
                parent=main_frame
            )
            return False
        else:
            # Save the selected directory path if the file does not exist
            save_dir_path(working_path)
            return True




def save_configuration():
    """
    Saves the current configuration of various tabs (engine design, nozzle design, engine CAD design, and adiabatic module)
    into a 'config.json' file in the selected working directory.
    
    It first checks if the file path exists. If not, it opens a dialog to choose a directory.
    Then it gathers input values from different modules and saves them into a JSON file.
    """

    global main_frame
    global adiabatic_module_instance
    global engineDesing_module_instance
    global nozzleDesing_module_instance
    global EngineCADDesing_module_instance
    global TestingBed_module_instance

    try:
        # Construct the file path for the 'config.json' file
        file_path = os.path.join(working_path, "config.json")
    except Exception:
        # If the directory is not set, prompt the user to select one
        if open_on_saving_directory():
            file_path = os.path.join(working_path, "config.json")
        else:
            return  # If no directory is selected, exit the function
    
    # Tab 1 Configuration (Engine Design Module)
    tab_1_config = {
        "propellant": engineDesing_module_instance.propellant_selector.get(),
        "geoConfig": engineDesing_module_instance.grainGeo_selector.get(),
        "P0":       get_entry_value(engineDesing_module_instance.ambientPressureEntry),
        "Rt":       get_entry_value(engineDesing_module_instance.throatRadiEntry),
        "Rc":       get_entry_value(engineDesing_module_instance.caseRadiEntry),
        "Lc":       get_entry_value(engineDesing_module_instance.lCombEntry),
        "dt":       get_entry_value(engineDesing_module_instance.timeStepEntry),
        "dh":       get_entry_value(engineDesing_module_instance.spaceStepEntry),
        "ItMax":    get_entry_value(engineDesing_module_instance.maxItersEntry),
    }
    
    # Loop over all grain types and collect input entries for each type
    for grain_type, entries in engineDesing_module_instance.specInputs_entries.items():
        for entry_name, entry_widget in entries.items():
            tab_1_config[f"{grain_type}_{entry_name}"] = get_entry_value(entry_widget[1])  # Entry widget is at position 1

    # Tab 2 Configuration (Nozzle Design Module)
    tab_2_config = {
        "engine_config": nozzleDesing_module_instance.file_path_label.cget("text"),
        "SwitchState": nozzleDesing_module_instance.pressureCheck_Box.get(),
        "P1": get_entry_value(nozzleDesing_module_instance.pressure_entry),
        "n_res": get_entry_value(nozzleDesing_module_instance.nPoints_entry),
        "nozzle_type": nozzleDesing_module_instance.nozzleTypeMenu.get(),
    }
    
    # Loop over all nozzle types and collect input entries for each type
    for nozzle_type, entries in nozzleDesing_module_instance.specInputs_entries.items():
        for entry_name, entry_widget in entries.items():
            tab_2_config[f"{nozzle_type}_{entry_name}"] = get_entry_value(entry_widget[1])  # Entry widget is at position 1

    # Tab 3 Configuration (Engine CAD Design Module)
    try:
        tab_3_config = {
            "NozzleConfig": EngineCADDesing_module_instance.file_name
        }
        # Update with the entries present in the dynamic widgets dictionary
        tab_3_config.update({
            key: widget.get() if isinstance(widget, (ctk.CTkEntry, ctk.CTkOptionMenu, ctk.CTkCheckBox)) else widget.get() 
            for key, widget in EngineCADDesing_module_instance.widgets_dict.items()
        })
    except Exception as e:
        print(f"Error in Tab 3 configuration: {e}")
        tab_3_config = {"None": None}

    # Tab 0 and Tab 1 configurations
    config = {
        "tabs": {
            "tab_0": {
                "reactivos": [(get_entry_value(entry), combo.get()) for entry, combo in adiabatic_module_instance.reactivos_widgets],
                "productos": [(get_entry_value(entry), combo.get()) for entry, combo in adiabatic_module_instance.productos_widgets],
                "initial_temp": get_entry_value(adiabatic_module_instance.initial_temp),
                "temp_Int_step": get_entry_value(adiabatic_module_instance.temp_Int_step),
                "temp_guess": get_entry_value(adiabatic_module_instance.temp_guess)
            },
            "tab_1": tab_1_config,
            "tab_2": tab_2_config,
            "tab_3": tab_3_config
        }
    }

    # Save the configuration to a JSON file
    with open(file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)

    # Show a success message once the file is saved
    messagebox.showinfo("Save File", f"Configuration saved in {file_path}")




def load_configuration(working_path):
    """
    Load configuration settings from a JSON file and update various module instances with the loaded values.
    This function handles the restoration of settings for different tabs in the application (Reactants & Products,
    Engine Design, and Nozzle Design), ensuring that the UI reflects previously saved user input.

    Parameters:
    - working_path (str): The directory path where the configuration file (config.json) is located.

    The function updates:
    - Tab 0: Reactants and products information (moles, types), and initial temperature settings.
    - Tab 1: Engine design parameters, such as propellant, geometry configuration, and engine design inputs.
    - Tab 2: Nozzle design parameters, including pressure and nozzle type.
    - Tab 3: Engine CAD design inputs.

    If any part of the configuration file is missing or invalid, default settings are used.
    """

    global main_frame
    global adiabatic_module_instance
    global engineDesing_module_instance
    global nozzleDesing_module_instance
    global EngineCADDesing_module_instance
    global TestingBed_module_instance

    # Define the path for the configuration file (config.json)
    file_path = os.path.join(working_path, "config.json")
    
    # Check if the configuration file exists
    if os.path.exists(file_path):
        try:
            # Open the configuration file and load its contents as a dictionary
            with open(file_path, 'r') as config_file:
                config = json.load(config_file)

            # --------------- Load Tab 0 Configuration (Reactants & Products) --------------- #
            tab_0_config = config["tabs"]["tab_0"]
            
            # Clear current reactants widgets and reset row index
            for entry, combo in adiabatic_module_instance.reactivos_widgets:
                entry.destroy()
                combo.destroy()
            adiabatic_module_instance.reactivos_widgets.clear()
            adiabatic_module_instance.reactivo_row = 2

            # Clear current products widgets and reset row index
            for entry, combo in adiabatic_module_instance.productos_widgets:
                entry.destroy()
                combo.destroy()
            adiabatic_module_instance.productos_widgets.clear()
            adiabatic_module_instance.producto_row = 2

            # Populate reactants from configuration
            for mole, reactivo in tab_0_config["reactivos"]:
                adiabatic_module_instance.add_reactivo()
                adiabatic_module_instance.reactivos_widgets[-1][0].insert(0, mole)  # Set mole amount
                adiabatic_module_instance.reactivos_widgets[-1][1].set(reactivo)  # Set reactant type

            # Populate products from configuration
            for mole, producto in tab_0_config["productos"]:
                adiabatic_module_instance.add_producto()
                adiabatic_module_instance.productos_widgets[-1][0].insert(0, mole)  # Set mole amount
                adiabatic_module_instance.productos_widgets[-1][1].set(producto)  # Set product type

            # Set initial temperature and other temperature-related settings
            adiabatic_module_instance.initial_temp.delete(0, tk.END)
            adiabatic_module_instance.initial_temp.insert(0, tab_0_config["initial_temp"])
            adiabatic_module_instance.temp_Int_step.delete(0, tk.END)
            adiabatic_module_instance.temp_Int_step.insert(0, tab_0_config["temp_Int_step"])
            adiabatic_module_instance.temp_guess.delete(0, tk.END)
            adiabatic_module_instance.temp_guess.insert(0, tab_0_config["temp_guess"])

            # Update the label displaying the reaction data
            adiabatic_module_instance.update_reaction_label()

            # --------------- Load Tab 1 Configuration (Engine Design) --------------- #
            tab_1_config = config["tabs"]["tab_1"]
            
            # Set propellant and geometry configuration
            engineDesing_module_instance.propellant_selector.set(tab_1_config["propellant"])
            engineDesing_module_instance.grainGeo_selector.set(tab_1_config["geoConfig"])
            engineDesing_module_instance.update_options(tab_1_config["geoConfig"])  # Update based on selected geometry

            # Set various engine design entries
            engineDesing_module_instance.ambientPressureEntry.delete(0, tk.END)
            engineDesing_module_instance.ambientPressureEntry.insert(0, tab_1_config["P0"])

            engineDesing_module_instance.throatRadiEntry.delete(0, tk.END)
            engineDesing_module_instance.throatRadiEntry.insert(0, tab_1_config["Rt"])

            engineDesing_module_instance.caseRadiEntry.delete(0, tk.END)
            engineDesing_module_instance.caseRadiEntry.insert(0, tab_1_config["Rc"])

            engineDesing_module_instance.lCombEntry.delete(0, tk.END)
            engineDesing_module_instance.lCombEntry.insert(0, tab_1_config["Lc"])

            engineDesing_module_instance.timeStepEntry.delete(0, tk.END)
            engineDesing_module_instance.timeStepEntry.insert(0, tab_1_config["dt"])

            engineDesing_module_instance.spaceStepEntry.delete(0, tk.END)
            engineDesing_module_instance.spaceStepEntry.insert(0, tab_1_config["dh"])

            engineDesing_module_instance.maxItersEntry.delete(0, tk.END)
            engineDesing_module_instance.maxItersEntry.insert(0, tab_1_config["ItMax"])

            # Loop over all nozzle types and load input entries for each type
            for grain_type, entries in engineDesing_module_instance.specInputs_entries.items():
                for entry_name, entry_widget in entries.items():
                    full_key = f"{grain_type}_{entry_name}"
                    if full_key in tab_1_config:
                        entry_widget[1].delete(0, tk.END)
                        entry_widget[1].insert(0, tab_1_config[full_key])

            engineDesing_module_instance.update_plot()


            # --------------- Load Tab 2 Configuration (Nozzle Design) --------------- #
            tab_2_config = config["tabs"]["tab_2"]

            # Load engine configuration file for Nozzle Design
            engine_path = os.path.join(working_path, "Engines", tab_2_config["engine_config"])
            nozzleDesing_module_instance.get_engine_data(on_load=True, file=engine_path)

            # Set pressure entry field
            nozzleDesing_module_instance.pressure_entry.delete(0, tk.END)
            nozzleDesing_module_instance.pressure_entry.insert(0, tab_2_config["P1"])

            # Handle SwitchState logic for pressure controls
            if tab_2_config["SwitchState"] == 1:
                # If the switch is on, disable the pressure slide bar and set mean pressure
                nozzleDesing_module_instance.pressureCheck_Box.configure(state="normal")
                nozzleDesing_module_instance.pressureCheck_Box.select()
                nozzleDesing_module_instance.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")
                nozzleDesing_module_instance.pressure_entry.delete(0, tk.END)
                nozzleDesing_module_instance.pressure_entry.insert(0, str(nozzleDesing_module_instance.meanP))
                nozzleDesing_module_instance.pressure_entry.configure(state="disabled")
                nozzleDesing_module_instance.pressureSlide_Bar.set(nozzleDesing_module_instance.meanP)
            else:
                # If the switch is off, allow pressure to be manually adjusted
                nozzleDesing_module_instance.pressureCheck_Box.configure(state="normal")
                nozzleDesing_module_instance.pressureCheck_Box.deselect()
                nozzleDesing_module_instance.pressureSlide_Bar.configure(state="normal", button_color="#1F6AA5", button_hover_color="#144870")
                nozzleDesing_module_instance.pressureSlide_Bar.set(float(tab_2_config["P1"]))
                nozzleDesing_module_instance.pressure_entry.delete(0, tk.END)
                nozzleDesing_module_instance.pressure_entry.insert(0, str(tab_2_config["P1"]))
                nozzleDesing_module_instance.pressure_entry.configure(state="normal")

            # Update the nozzle plot and resolution points
            nozzleDesing_module_instance.update_plot()
            nozzleDesing_module_instance.nPoints_entry.delete(0, tk.END)
            nozzleDesing_module_instance.nPoints_entry.insert(0, tab_2_config["n_res"])

            # Set saved nozzle type in OptionMenu and update the corresponding input fields
            nozzleDesing_module_instance.nozzleTypeMenu.set(tab_2_config["nozzle_type"])
            nozzleDesing_module_instance.update_options(tab_2_config["nozzle_type"])

            # Loop over all nozzle types and load input entries for each type
            for nozzle_type, entries in nozzleDesing_module_instance.specInputs_entries.items():
                for entry_name, entry_widget in entries.items():
                    full_key = f"{nozzle_type}_{entry_name}"
                    if full_key in tab_2_config:
                        entry_widget[1].delete(0, tk.END)
                        entry_widget[1].insert(0, tab_2_config[full_key])


            # --------------- Load Tab 3 Configuration (Engine CAD Design) --------------- #
            tab_3_config = config["tabs"]["tab_3"]

            # Build engine design entries based on nozzle configuration file
            EngineCADDesing_module_instance.build_entries(on_load=True, file=tab_3_config["NozzleConfig"])

            # Loop through widgets to populate values based on the saved configuration
            for key, value in tab_3_config.items():
                if key in EngineCADDesing_module_instance.widgets_dict:
                    widget = EngineCADDesing_module_instance.widgets_dict[key]
                    
                    # Set values based on widget type (OptionMenu, Entry, or CheckBox)
                    if isinstance(widget, ctk.CTkOptionMenu):
                        widget.set(value)
                    elif isinstance(widget, ctk.CTkEntry):
                        widget.delete(0, tk.END)
                        widget.insert(0, value)
                    elif isinstance(widget, ctk.CTkCheckBox):
                        if value:
                            widget.select()
                        else:
                            widget.deselect()

            # Update the engine design plots after loading settings
            EngineCADDesing_module_instance.update_plots()

            # Call the testing bed to refresh the checklist of engine designs
            TestingBed_module_instance.create_checklist()

        # Handle errors if the file is not found or other exceptions occur during the load
        except FileNotFoundError as e:
            print(e)
            print("No previous configuration found. Starting with default values.")
        except Exception as e:
            print(f"Error loading configuration: {e}")




def on_closing():
    """
    Handles the closing event of the application.
    
    Before the application is closed, the user is prompted with a dialog box asking if they want to save the current configuration.
    If the user chooses to save, the save_configuration function is called. The function then performs necessary cleanup tasks,
    including clearing the directory path, triggering any shutdown routines for the TestingBed module, and finally, ensuring that the
    main application frame is properly closed.
    
    The use of `after(100, main_frame.quit)` ensures that any pending tasks are allowed to complete before the application exits.
    """

    global main_frame
    global TestingBed_module_instance
    global closing

    if not closing:
        closing = True  # Set the closing flag to prevent multiple triggers of the closing process
        
        # Ask the user if they want to save the configuration before exiting
        answer = messagebox.askyesno("Guardar", "¿Deseas guardar la configuración antes de salir?")
        
        if answer:
            save_configuration()  # Call the save function if the user chooses to save
        
        # Perform necessary cleanup before closing the application
        clear_dir_path()  # Clear any directory path references or temporary files
        TestingBed_module_instance.on_close()  # Call the close routine for the TestingBed module
        
        # Schedule the main frame to quit after 100 milliseconds to allow pending tasks to complete
        main_frame.after(100, main_frame.quit)
        
        # Ensure that the main application frame quits, even if the after method is delayed
        main_frame.quit()



def main():

    global main_frame
    global adiabatic_module_instance
    global engineDesing_module_instance
    global nozzleDesing_module_instance
    global EngineCADDesing_module_instance
    global TestingBed_module_instance

    # Colores
    selected_color = "#e67e22"  # Reddish orange for selected (similar to the logo)
    default_color = "#2c3e50"    # Dark grey for default

    

    # Initialize the main application window
    main_frame = ctk.CTk()
    main_frame.iconbitmap("icon.ico")  # Set window icon
    main_frame.geometry("1920x1080")      # Set default window size
    main_frame.title("OpenRED")  # Set window title

    # Configure grid for window layout
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    
 
    # Dictionary to store tab content frames
    tabs_content = {}
    global adiabatic_module_instance

    # Create the main menu bar using tkinter
    menu = tk.Menu(main_frame)
    main_frame.config(menu=menu)

    # File menu with options to open, save, and exit
    file_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Open", command=open_directory)
    file_menu.add_command(label="Save", command=save_configuration)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=on_closing)

    ctk.set_default_color_theme("themes/red.json") # Needs Fix

    # Create a function to load custom themes
    def load_custom_themes(theme_menu):
        theme_dir = "themes/"  # Directory containing theme JSON files
        themes = [f for f in os.listdir(theme_dir) if f.endswith('.json')]  # List of theme files

        for theme in themes:
            theme_menu.add_command(
                label=theme[:-5],  # Remove '.json' from the display name
                command=lambda t=theme: ctk.set_default_color_theme(os.path.join(theme_dir, t)) 
                )

    # Create the preferences menu for theme settings
    preferences_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Preferences", menu=preferences_menu)

    # Create a submenu for Modes
    modes_menu = tk.Menu(preferences_menu, tearoff=0)
    preferences_menu.add_cascade(label="Modes", menu=modes_menu)
    modes_menu.add_command(label="Dark Mode", command=lambda: ctk.set_appearance_mode("dark"))
    modes_menu.add_command(label="Light Mode", command=lambda: ctk.set_appearance_mode("light"))

    # Create a submenu for Themes
    themes_menu = tk.Menu(preferences_menu, tearoff=0)
    preferences_menu.add_cascade(label="Themes", menu=themes_menu)

    # Load custom themes into the themes menu
    load_custom_themes(themes_menu)

    # Database menu for accessing thermochemical and propellant databases
    database_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Database", menu=database_menu)
    database_menu.add_command(label="Thermochemical Data", command=lambda: TermoquimicaWindow(main_frame))
    database_menu.add_command(label="Propellants Data", command=lambda: PropellantWindow(main_frame))

    # Create a left panel for navigation buttons (tabs)
    tabs_frame = ctk.CTkFrame(main_frame)
    tabs_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # Create a right panel for dynamic content (tab content)
    content_frame = ctk.CTkFrame(main_frame)
    content_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    # Create content frames for each tab (initializing instances of each module)
    tabs_content["tab_adTemp"] = ctk.CTkFrame(content_frame)
    adiabatic_module_instance = AdiabaticTempModule(tabs_content["tab_adTemp"])

    tabs_content["tab_propDes"] = ctk.CTkFrame(content_frame)
    engineDesing_module_instance = PropellantDesignModule(tabs_content["tab_propDes"], main_frame)

    tabs_content["tab_nozDes"] = ctk.CTkFrame(content_frame)
    nozzleDesing_module_instance = NozzleDesignModule(tabs_content["tab_nozDes"])

    tabs_content["tab_cad"] = ctk.CTkFrame(content_frame)
    EngineCADDesing_module_instance = EngineCADModule(tabs_content["tab_cad"])

    tabs_content["tab_test"] = ctk.CTkFrame(content_frame)
    TestingBed_module_instance = TestingBedModule(tabs_content["tab_test"])

    tabs_content["tab_cfd"] = ctk.CTkFrame(content_frame)
    CFD_module_instance = CFD_Module(tabs_content["tab_cfd"])

    tabs_content["tab_Doc"] = ctk.CTkFrame(content_frame)
    DocModule_instance = DocModule(tabs_content["tab_Doc"])

    tabs_content["tab_post"] = ctk.CTkFrame(content_frame)
    PostProcessModule_instance = PostProcessModule(tabs_content["tab_post"])

    # Dictionary to store references to tab buttons for color changes
    tab_buttons = {}


    # Define a list of tab names and their corresponding tags
    tabsList = [
        ("Documentation", "tab_Doc"),
        ("Adiabatic Flame\n Temperature", "tab_adTemp"),
        ("Engine Design", "tab_propDes"),
        ("Nozzle Design", "tab_nozDes"),
        ("CAD Design", "tab_cad"),
        ("OpenFOAM Maker", "tab_cfd"),
        ("Test Bed", "tab_test"),
        ("Post-Processing", "tab_post")
    ]

    # Create buttons for each tab in the left panel
    for tab, tag in tabsList:
        button = ctk.CTkButton(tabs_frame, text=tab, command=lambda tag=tag: change_tab(tag))
        button.pack(pady=10, padx=10, fill="x")
        tab_buttons[tag] = button  # Save reference to the button

    # Function to change the active tab and display its content
    def change_tab(tab_name):
        for tab in tabs_content.values():
            tab.pack_forget()  # Hide all tabs
        tabs_content[tab_name].pack(expand=True, fill="both")  # Show selected tab
        #update_button_colors(tab_name)  # Update button colors

    # Display the first tab (default) and highlight its button
    change_tab(tabsList[0][1])

    # Bind the save function to the window close event
    main_frame.protocol("WM_DELETE_WINDOW", on_closing)

    # Run the application event loop
    main_frame.mainloop()

# Run the main function
if __name__ == "__main__":
    main()