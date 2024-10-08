from imports import *
from functions import *

from back_modules.back_0 import *

class AdiabaticTempModule:
    def __init__(self, content_frame: ctk.CTkFrame):
        """
        Initializes the Adiabatic Temperature Module.

        Args:
            content_frame (ctk.CTkFrame): The frame in which this module will be displayed.
        """
        self.content_frame = content_frame
        
        # Configure rows and columns for the content frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=0)  # Row with fixed height
        self.content_frame.grid_rowconfigure(2, weight=1)
        self.content_frame.grid_rowconfigure(3, weight=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(2, weight=1)
        self.content_frame.grid_columnconfigure(3, weight=1)

        # Frame to display results and other outputs
        self.display_frame = ctk.CTkFrame(content_frame, height=100)
        self.display_frame.grid(row=0, column=0, rowspan=2, columnspan=4, padx=10, pady=10, sticky="ew")
        self.display_frame.grid_propagate(False)  # Prevents frame from resizing itself
        self.display_frame.bind("<Enter>", lambda event: self.update_reaction_label)

        # Rows for reactants and products
        self.reactivo_row = 2
        self.producto_row = 2
        self.reactivos_widgets = []  # Store reactants widgets
        self.productos_widgets = []   # Store products widgets
        self.label = None  # Initialize the label for reaction updates

        # Scrollable frame for reactants
        self.reactivos_frame = ctk.CTkScrollableFrame(content_frame)
        self.reactivos_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Scrollable frame for products
        self.productos_frame = ctk.CTkScrollableFrame(content_frame)
        self.productos_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        # Frame for displaying results
        self.results_frame = ctk.CTkFrame(content_frame)
        self.results_frame.grid(row=2, column=2, rowspan=3, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Frame for numeric results
        self.numeric_frame = ctk.CTkFrame(self.results_frame)
        self.numeric_frame.grid(row=0, padx=10, columnspan=2, pady=10, sticky="nsew")
        self.numeric_frame.grid_columnconfigure(0, weight=1)
        self.numeric_frame.grid_columnconfigure(1, weight=1)

        # Title for results section
        self.results_title = ctk.CTkLabel(self.numeric_frame, text="Results", font=ctk.CTkFont(size=14, weight="bold"))
        self.results_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="n")

        # Labels for displaying results
        self.results_labels = {}
        results_texts = [
            "Solution Temperature (K):",
            "Molecular Weight of Product (kg/mol):",
            "Specific Heat at Constant Pressure (J/(kg*K)):",
            "Specific Heat at Constant Volume (J/(kg*K)):",
            "Gas Constant of Product (J/(kg*K)):",
            "Gamma (Cp/Cv):",
            "Characteristic Velocity (m/s):"
        ]

        # Create result labels and corresponding readonly entry fields
        for i, text in enumerate(results_texts):
            label = ctk.CTkLabel(self.numeric_frame, text=text)
            label.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(self.numeric_frame, state="readonly")
            entry.grid(row=i+1, column=1, padx=10, pady=5, sticky="ew")
            self.results_labels[text] = entry

        # Frame for additional propellant data
        self.save_reaction_frame = ctk.CTkFrame(self.results_frame)
        self.save_reaction_frame.grid(row=1, padx=10, columnspan=2, pady=10, sticky="nsew")
        self.save_reaction_frame.grid_columnconfigure(0, weight=1)
        self.save_reaction_frame.grid_columnconfigure(1, weight=1)

        # Title for additional data section
        ctk.CTkLabel(self.save_reaction_frame, text='Additional Propellant Data', font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Input fields for propellant data
        self.propellant_name_label = ctk.CTkLabel(self.save_reaction_frame, text='Propellant Name:')
        self.propellant_name_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.propellant_name = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_name.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.propellant_density_label = ctk.CTkLabel(self.save_reaction_frame, text='Propellant Density (kg/m^3):')
        self.propellant_density_label.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        self.propellant_density = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_density.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")

        # Input fields for pressure coefficients
        self.propellant_P1_min_label = ctk.CTkLabel(self.save_reaction_frame, text='P1 (Min. - Pa):')
        self.propellant_P1_min_label.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.propellant_P1_min = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_P1_min.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.propellant_P1_max_label = ctk.CTkLabel(self.save_reaction_frame, text='P1 (Max. - Pa):')
        self.propellant_P1_max_label.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")

        self.propellant_P1_max = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_P1_max.grid(row=2, column=3, padx=10, pady=10, sticky="nsew")

        self.propellant_a_label = ctk.CTkLabel(self.save_reaction_frame, text='Coefficient a:')
        self.propellant_a_label.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

        self.propellant_a = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_a.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        self.propellant_n_label = ctk.CTkLabel(self.save_reaction_frame, text='Coefficient n:')
        self.propellant_n_label.grid(row=3, column=2, padx=10, pady=10, sticky="nsew")

        self.propellant_n = ctk.CTkEntry(self.save_reaction_frame)
        self.propellant_n.grid(row=3, column=3, padx=10, pady=10, sticky="nsew")

        # Button to save propellant data
        self.propellant_button = ctk.CTkButton(self.save_reaction_frame, text='Add Propellant', command=self.save_propellant)
        self.propellant_button.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Treeview configuration for displaying saved propellants
        self.tree_frame = ctk.CTkScrollableFrame(self.results_frame, orientation='horizontal')
        self.tree_frame.grid(row=2, column=0, rowspan=2, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.bind("<Enter>", lambda event: self.populate_treeview())

        # Treeview for displaying propellant data
        self.tree = ttk.Treeview(self.tree_frame, columns=(
            "ID", 
            "Propellant", 
            "T1 (K)", 
            "M (kg/mol)", 
            "Cp (J/KgK)", 
            "Cv (J/KgK)", 
            "R (J/KgK)", 
            "gamma", 
            "c*", 
            "rho", 
            "P1 - Min. (Pa)", 
            "P1 - Max. (Pa)",
            "a (cm/s)", 
            "n"
        ), show="headings")

        # Column headers for the treeview
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=100)
        
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Populate the Treeview with data from the database
        self.populate_treeview()

        # Frame for inputting inlet temperature
        self.inletTemp_frame = ctk.CTkFrame(content_frame)
        self.inletTemp_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

        # Frame for inputting integration step temperature
        self.intStep_frame = ctk.CTkFrame(content_frame)
        self.intStep_frame.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        # Frame for inputting initial seed temperature
        self.seedTemp_frame = ctk.CTkFrame(content_frame)
        self.seedTemp_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

        # Frame for the calculation button
        self.calcButton_frame = ctk.CTkFrame(content_frame)
        self.calcButton_frame.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

        # Entry for inlet temperature
        self.initial_temp = ctk.CTkEntry(self.inletTemp_frame)
        self.initial_temp.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.initial_temp.bind("<FocusOut>", self.update_reaction_label)

        # Entry for integration step temperature
        self.temp_Int_step = ctk.CTkEntry(self.intStep_frame)
        self.temp_Int_step.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.temp_Int_step.bind("<FocusOut>", self.update_reaction_label)

        # Entry for seed temperature guess
        self.temp_guess = ctk.CTkEntry(self.seedTemp_frame)
        self.temp_guess.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.temp_guess.bind("<FocusOut>", self.update_reaction_label)

        # Label for reactants section
        ctk.CTkLabel(self.reactivos_frame, text="Reactants", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="ew")

        # Label for products section
        ctk.CTkLabel(self.productos_frame, text="Products", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="ew")

        # Label for inlet temperature
        ctk.CTkLabel(self.inletTemp_frame, text="Inlet Temperature (K):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="ew")

        # Label for integration step
        ctk.CTkLabel(self.intStep_frame, text="Integration Step (K):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="ew")

        # Label for initial seed temperature
        ctk.CTkLabel(self.seedTemp_frame, text="Initial Temperature (K):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="ew")

        # Button to add a reactant
        add_reactivo_button = ctk.CTkButton(self.reactivos_frame, text="Add Reactant", command=self.add_reactivo)
        add_reactivo_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Button to remove a reactant
        remove_reactivo_button = ctk.CTkButton(self.reactivos_frame, text="Remove Reactant", command=self.remove_reactivo)
        remove_reactivo_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Button to add a product
        add_producto_button = ctk.CTkButton(self.productos_frame, text="Add Product", command=self.add_producto)
        add_producto_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Button to remove a product
        remove_producto_button = ctk.CTkButton(self.productos_frame, text="Remove Product", command=self.remove_producto)
        remove_producto_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Button to calculate results
        calc_button = ctk.CTkButton(self.calcButton_frame, text="Calculate", command=self.calculate)
        calc_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Configuration to expand rows and columns in reactivos_frame and productos_frame
        for i in range(2, self.reactivo_row + 1):
            self.reactivos_frame.grid_rowconfigure(i, weight=1)
        for i in range(2, self.producto_row + 1):
            self.productos_frame.grid_rowconfigure(i, weight=1)

        # Configure columns in the reactants frame
        self.reactivos_frame.grid_columnconfigure(0, weight=1)
        self.reactivos_frame.grid_columnconfigure(1, weight=1)

        # Configure columns in the products frame
        self.productos_frame.grid_columnconfigure(0, weight=1)
        self.productos_frame.grid_columnconfigure(1, weight=1)

        # Configure columns in the results frame
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.results_frame.grid_rowconfigure(2, weight=1)

        # Configure columns in the inlet temperature frame
        self.inletTemp_frame.grid_columnconfigure(0, weight=1)
        self.inletTemp_frame.grid_columnconfigure(1, weight=1)

        # Configure columns in the integration step frame
        self.intStep_frame.grid_columnconfigure(0, weight=1)
        self.intStep_frame.grid_columnconfigure(1, weight=1)

        # Configure columns in the seed temperature frame
        self.seedTemp_frame.grid_columnconfigure(0, weight=1)
        self.seedTemp_frame.grid_columnconfigure(1, weight=1)

        # Configure columns in the calculation button frame
        self.calcButton_frame.grid_columnconfigure(0, weight=1)
        self.calcButton_frame.grid_columnconfigure(1, weight=1)

        # Initialize the first reactant and product
        self.add_reactivo()
        self.add_producto()


    def save_propellant(self) -> None:
        """Save propellant data to the database and update the Treeview."""
        
        # Open a connection to the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Get the name of the propellant
        propellant_name: str = self.propellant_name.get()

        # Get values from the entries
        T_ad: float = float(self.results_labels["Solution Temperature (K):"].get())
        Cp: float = float(self.results_labels["Specific Heat at Constant Pressure (J/(kg*K)):"].get())
        MolWeight: float = float(self.results_labels["Molecular Weight of Product (kg/mol):"].get())
        Cv: float = float(self.results_labels["Specific Heat at Constant Volume (J/(kg*K)):"].get())
        R: float = float(self.results_labels["Gas Constant of Product (J/(kg*K)):"].get())
        gamma: float = float(self.results_labels["Gamma (Cp/Cv):"].get())
        cChar: float = float(self.results_labels["Characteristic Velocity (m/s):"].get())
        density: float = float(self.propellant_density.get())
        a: float = float(self.propellant_a.get())
        n: float = float(self.propellant_n.get())
        P1min: float = float(self.propellant_P1_min.get())
        P1max: float = float(self.propellant_P1_max.get())

        # Insert the data into the database
        c.execute('''
            INSERT INTO propelente (Propelente, T_ad, Cp, MolWeight, Cv, R, gamma, cChar, Density, P1_min, P1_max, a, n)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (propellant_name, T_ad, Cp, MolWeight, Cv, R, gamma, cChar, density, P1min, P1max, a, n))

        # Commit the transaction
        conn.commit()

        # Close the connection to the database
        conn.close()

        # Update the Treeview
        self.populate_treeview()
        self.reassign_ids()


    def populate_treeview(self) -> None:
        """Populate the Treeview with data from the propelente table in the database."""
        
        # Connect to the database
        self.conn = sqlite3.connect('database.db')
        self.c = self.conn.cursor()

        # Clear existing rows in the Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Retrieve data from the propelente table
        self.c.execute("SELECT * FROM propelente")
        rows = self.c.fetchall()

        # Insert data into the Treeview
        for row in rows:
            self.tree.insert("", "end", values=row)

        # Reassign IDs if necessary
        self.reassign_ids()

        # Close the connection to the database
        self.conn.close()
    

    def calculate(self) -> None:
        """Calculate the adiabatic temperature and update the results labels."""
        
        reactivos = []  # List to hold reactant moles and names
        productos = []  # List to hold product moles and names

        # Gather data for reactants
        for mole_entry, option_menu in self.reactivos_widgets:
            try:
                mole: float = float(mole_entry.get())
            except ValueError:
                mole = 0.0
            reactivo: str = option_menu.get()
            reactivos.append((mole, reactivo))

        # Gather data for products
        for mole_entry, option_menu in self.productos_widgets:
            try:
                mole: float = float(mole_entry.get())
            except ValueError:
                mole = 0.0
            producto: str = option_menu.get()
            productos.append((mole, producto))

        # Get initial temperature
        try:
            initial_temp: float = float(self.initial_temp.get())
        except ValueError:
            initial_temp = 0.0

        # Get temperature increment step
        try:
            temp_step: float = float(self.temp_Int_step.get())
        except ValueError:
            temp_step = 0.0

        # Get initial temperature guess
        try:
            temp_guess: float = float(self.temp_guess.get())
        except ValueError:
            temp_guess = 0.0

        # Calculate results using the adiabatic temperature function
        self.results = adiabaticTemp_calc(reactivos, productos, initial_temp, temp_guess, temp_step)

        # Define labels for results
        results_texts = [
            "Solution Temperature (K):",
            "Molecular Weight of Product (kg/mol):",
            "Specific Heat at Constant Pressure (J/(kg*K)):",
            "Specific Heat at Constant Volume (J/(kg*K)):",
            "Gas Constant of Product (J/(kg*K)):",
            "Gamma (Cp/Cv):",
            "Characteristic Velocity (m/s):"
        ]

        # Update results labels with calculated values
        for text, result in zip(results_texts, self.results):
            self.results_labels[text].configure(state="normal")
            self.results_labels[text].delete(0, "end")
            self.results_labels[text].insert(0, str(result))
            self.results_labels[text].configure(state="readonly")


    def update_reaction_label(self, event=None) -> None:
        """Update the reaction label in the display frame based on reactants and products."""
        
        # Gather reactants and products from the widgets
        reactivos = [(entry.get(), option.get()) for entry, option in self.reactivos_widgets]
        productos = [(entry.get(), option.get()) for entry, option in self.productos_widgets]

        # Construct the reaction string in LaTeX format
        reaction_str = " + ".join(f"{mole} {self.latexMap[reactivo]}" for mole, reactivo in reactivos if mole) + \
                    r"\longrightarrow" + \
                    " + ".join(f"{mole} {self.latexMap[producto]}" for mole, producto in productos if mole)

        # Determine the size of the display frame for the plot
        width, height = self.display_frame.winfo_width() / 100, self.display_frame.winfo_height() / 100
        fig, ax = plt.subplots(figsize=(width, height))
        fontsize = 20
        fig.patch.set_facecolor('#2b2b2b')  # Set background color

        while True:
            ax.clear()  # Clear the axes
            ax.text(0.5, 0.5, f"${reaction_str}$", fontsize=fontsize, ha='center', va='center', color='w')  # Add reaction text
            ax.axis('off')  # Turn off the axes
            fig.canvas.draw()  # Update the figure canvas

            # Get the bounding box of the text
            bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            text_width, text_height = bbox.width, bbox.height

            # Check if the text fits within the display frame
            if text_width <= width * 0.9 and text_height <= height * 0.9 or fontsize <= 1:
                break  # Exit the loop if it fits

            fontsize -= 1  # Decrease font size if it doesn't fit

        # Insert the figure into the display frame
        insert_fig(fig, self.display_frame)


    def add_reactivo(self) -> None:
        """Add a new reactant entry and update the reaction label."""
        
        # Retrieve components and the latex map from the database
        components, self.latexMap = get_database_components()

        # Create an entry for the mole value of the reactant
        mole_entry = ctk.CTkEntry(self.reactivos_frame)
        mole_entry.grid(row=self.reactivo_row, column=0, padx=5, pady=5, sticky="ew")
        mole_entry.bind("<FocusOut>", self.update_reaction_label)  # Update label when focus is lost

        # Create an option menu for selecting the reactant
        option_reactivos = ctk.CTkOptionMenu(self.reactivos_frame, values=components, command=lambda x: self.update_reaction_label())
        option_reactivos.grid(row=self.reactivo_row, column=1, padx=5, pady=5, sticky="ew")

        # Append the new mole entry and option menu to the widgets list
        self.reactivos_widgets.append((mole_entry, option_reactivos))
        
        # Increment the row counter for the next reactant
        self.reactivo_row += 1

        # Update the reaction label with the new reactant
        self.update_reaction_label()


    def remove_reactivo(self) -> None:
        """Remove the last added reactant entry and update the reaction label."""
        
        # Check if there are any reactants to remove
        if self.reactivos_widgets:
            # Remove the last reactant entry and option menu
            mole_entry, option_reactivos = self.reactivos_widgets.pop()
            mole_entry.destroy()  # Destroy the mole entry widget
            option_reactivos.destroy()  # Destroy the option menu widget
            
            # Decrement the row counter for the next reactant
            self.reactivo_row -= 1
            
            # Update the reaction label to reflect the changes
            self.update_reaction_label()


    def add_producto(self) -> None:
        """Add a new product entry and update the reaction label."""
        
        # Retrieve components and the latex map from the database
        components, self.latexMap = get_database_components()

        # Create an entry for the mole value of the product
        mole_entry = ctk.CTkEntry(self.productos_frame)
        mole_entry.grid(row=self.producto_row, column=0, padx=5, pady=5, sticky="ew")
        mole_entry.bind("<FocusOut>", self.update_reaction_label)  # Update label when focus is lost

        # Create an option menu for selecting the product
        option_productos = ctk.CTkOptionMenu(self.productos_frame, values=components, command=lambda x: self.update_reaction_label())
        option_productos.grid(row=self.producto_row, column=1, padx=5, pady=5, sticky="ew")

        # Append the new mole entry and option menu to the widgets list
        self.productos_widgets.append((mole_entry, option_productos))
        
        # Increment the row counter for the next product
        self.producto_row += 1

        # Update the reaction label with the new product
        self.update_reaction_label()


    def remove_producto(self) -> None:
        """Remove the last added product entry and update the reaction label."""
        
        # Check if there are any products to remove
        if self.productos_widgets:
            # Remove the last product entry and option menu
            mole_entry, option_productos = self.productos_widgets.pop()
            mole_entry.destroy()  # Destroy the mole entry widget
            option_productos.destroy()  # Destroy the option menu widget
            
            # Decrement the row counter for the next product
            self.producto_row -= 1
            
            # Update the reaction label to reflect the changes
            self.update_reaction_label()


    def reassign_ids(self) -> None:
        """Reassign IDs to the records in the propelente table, starting from 1."""
        
        # Connect to the database
        self.conn = sqlite3.connect('database.db')  # Change the database file name if needed
        self.c = self.conn.cursor()
        
        # Retrieve all records ordered by the current ID
        self.c.execute("SELECT * FROM propelente ORDER BY id")
        records = self.c.fetchall()

        # Reset the ID counter
        new_id = 1

        # Update each record with the new ID
        for record in records:
            old_id = record[0]  # Current ID
            # Update the record with the new ID
            self.c.execute("""
                UPDATE propelente 
                SET id=? 
                WHERE id=?
            """, (new_id, old_id))
            new_id += 1

        # Commit the changes to the database
        self.conn.commit()
        # Close the database connection
        self.conn.close()