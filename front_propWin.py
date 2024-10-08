from imports import *
from functions import *

from back_0 import *
from back_1 import *


class PropellantWindow:
    instance = None  # Class variable to track the instance

    def __init__(self, parent):
        if PropellantWindow.instance is not None:
            # If an instance already exists, show a message and return
            messagebox.showinfo("Info", "The Propellant window is already open.", parent=parent)
            return
        # Set the class instance
        PropellantWindow.instance = self

        self.conn = sqlite3.connect('database.db')  # Change the database file name
        self.c = self.conn.cursor()

        # Create tables if they don't exist
        # Moved to app

        self.columnTags = ("id", "Propellant", "T_ad", "MolWeight", "Cp", "Cv", "R", "gamma", "cChar", "Density", "P1_min", "P1_max", "a", "n")
        
        self.conn.commit()

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Propellants")
        self.window.geometry("1200x600")

        # Ensure the popup window stays on top
        self.window.transient(parent)
        self.window.grab_set()
        self.window.lift()

        # Bind the close event to reset the class instance
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create the structure of the new window
        self.entries_frame = ctk.CTkScrollableFrame(self.window, width=350)
        self.entries_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.buttons_frame = ctk.CTkFrame(self.window)
        self.buttons_frame.grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.list_frame = ctk.CTkScrollableFrame(self.window, orientation='horizontal')
        self.list_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Configure weights for the grid
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_columnconfigure(2, weight=1)
        self.window.grid_columnconfigure(3, weight=1)

        self.buttons_frame.grid_rowconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)
        self.buttons_frame.grid_columnconfigure(2, weight=1)

        # Add labels in entries_frame
        ctk.CTkLabel(self.entries_frame, text="Propellant Data").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.labels = [ctk.CTkLabel(self.entries_frame, text=self.columnTags[i]) for i in range(1, len(self.columnTags))]  # Exclude ID
        for i, label in enumerate(self.labels):
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky="ew")

        # Get components from the database
        self.components = self.get_components()

        # Add the elements in entries_frame
        self.entries = {}

        self.combobox_var = tk.StringVar()
        self.combobox = ctk.CTkComboBox(self.entries_frame, values=self.components, variable=self.combobox_var)
        self.combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        #self.combobox.set('Comp.')
        self.combobox_var.trace_add("write", self.fill_entries)  # Add the event
        self.entries["Propellant"] = self.combobox

        # Create entries in the entries_frame and store them in the dictionary
        for i, tag in enumerate(self.columnTags[2:], start=2):  # Exclude "id"
            entry = ctk.CTkEntry(self.entries_frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.validate_entry)
            entry.bind("<KeyRelease>", self.validate_entry)
            self.entries[tag] = entry

        self.burningRateGraph = ctk.CTkButton(self.entries_frame, text="Show Burning Rate Curve", command=self.display_burning_rate)
        self.burningRateGraph.grid(row=i+1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Ensure the frame adjusts dynamically
        for i in range(len(self.columnTags) - 1):  # Exclude ID
            self.entries_frame.grid_rowconfigure(i, weight=1)
        self.entries_frame.grid_columnconfigure(1, weight=1)

        # Add buttons in buttons_frame
        ctk.CTkButton(self.buttons_frame, text="Add", command=self.add_record).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Edit", command=self.edit_record).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Delete", command=self.delete_record).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Add Treeview in list_frame with scroll bars
        self.tree = ttk.Treeview(self.list_frame, columns=self.columnTags, show="headings")  # Include ID for reference
        for col in self.columnTags:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=100)

        self.tree.pack(expand=True, fill="both", padx=5, pady=5)
        self.reassign_ids()
        self.update_treeview()


    def validate_entry(self, event):
        """
        Validates the input entry field when it loses focus or a key is released.
        Replaces commas with dots for numerical input and checks if the value
        is in scientific notation. Changes the text color based on validity.

        Parameters:
            event: The event triggered by the widget (e.g., focus out or key release).
        """
        entry = event.widget
        value = entry.get()
        corrected_value = value.replace(',', '.')  # Replace comma with dot

        # If a comma is present, replace it with a dot and show a warning
        if ',' in value:
            entry.delete(0, tk.END)
            entry.insert(0, corrected_value)
            messagebox.showwarning("Number Format", "The comma has been replaced with a dot to maintain numerical format.", parent=self.window)

        # Validate scientific notation
        if not validate_scientific_notation(corrected_value):
            entry.configure(fg="red")  # Change text color to red if invalid
        else:
            entry.configure(fg="white")  # Change text color to white if valid


    def get_clean_component_name(self, component):
        """
        Removes numbers enclosed in parentheses at the end of the component name.
        This helps to standardize the component name for further processing.

        Parameters:
            component (str): The component name that may include numbers in parentheses.

        Returns:
            str: The cleaned component name without the trailing numbers in parentheses.
        """
        # Remove numbers in parentheses at the end of the component
        return re.sub(r'\(\d+\)$', '', component).strip()


    def on_closing(self):
        """
        Handles the event when the window is closed. It resets the class instance
        to allow for the creation of a new instance if the window is reopened.

        This method is called when the user attempts to close the window.
        """
        # Reset class instance when window closes
        PropellantWindow.instance = None
        self.window.destroy()


    def get_components(self):
        """
        Retrieves the list of components from the database.

        This method queries the 'propelente' table to get the component names 
        and their corresponding IDs. It returns a list of formatted strings 
        where each string contains the component name followed by its ID in parentheses.
        
        Returns:
            list: A list of formatted strings representing the components.
        """
        self.c.execute("SELECT id, Propelente FROM propelente")
        components = [f"{row[1]} ({row[0]})" for row in self.c.fetchall()]
        return components


    def get_entry_value(self, widget):
        """
        Retrieves the value from a given widget.

        This method checks if the widget is a CTkComboBox. If it is, 
        it returns the selected value. For other widgets, it returns 
        the current value, or '0' if the value is empty.

        Args:
            widget (ctk.CTkComboBox | ctk.CTkEntry): The widget from which to retrieve the value.

        Returns:
            str: The value from the widget or '0' if the widget is empty.
        """
        if isinstance(widget, ctk.CTkComboBox):
            return widget.get()
        return widget.get() if widget.get() else '0'


    def fill_entries(self, *args):
        """
        Fills the entry fields with data from the selected component.

        This method retrieves the ID of the selected component from the 
        combobox, fetches the corresponding record from the database, 
        and populates the entry fields with the record's values, 
        skipping the ID field.

        Args:
            *args: Variable length argument list, typically used for 
                callback functions that may pass additional parameters.
        """
        # Get the selected component
        selected_component = self.combobox_var.get()

        # Extract the ID of the selected component
        self.selected_id = selected_component.split('(')[-1].strip(')')

        # Get the corresponding values ​​from the database
        self.c.execute("SELECT * FROM propelente WHERE id=?", (self.selected_id,))
        record = self.c.fetchone()

        if record:
            # Fill the input fields with the corresponding values
            for i, value in enumerate(record):
                if i < 2:
                    continue  # Skip the ID as it is in the combobox
                tag = self.columnTags[i]
                self.entries[tag].delete(0, tk.END)
                self.entries[tag].insert(0, value)


    def validate_component(self, component):
        """
        Validates that the component name contains at least one alphabetical character.

        This method checks the given component string to ensure it 
        includes at least one letter. It helps to prevent the entry 
        of invalid component names.

        Args:
            component (str): The component name to validate.

        Returns:
            bool: True if the component contains at least one letter, 
                False otherwise.
        """
        # Check that the component contains at least one letter
        return any(char.isalpha() for char in component)


    def add_record(self):
        """
        Adds a new record to the propelente database.

        This method retrieves the component name and its corresponding 
        values from the entry fields, validates the component name, 
        and then inserts the new record into the database. If the 
        component name is invalid (does not contain at least one letter), 
        an error message is displayed.

        It also reassigns IDs to ensure they are consecutive and updates 
        the treeview to reflect the new record.

        Raises:
            sqlite3.Error: If there is an error executing the SQL command.
        """
        component_value = self.get_entry_value(self.entries[0])
        component_value = self.get_clean_component_name(component_value)
        
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "The component must contain at least one letter.", parent=self.window)
            return

        values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:])
        
        self.c.execute("INSERT INTO propelente (Propelente, T_ad, MolWeight, Cp, Cv, R, gamma, cChar, Density, P1_min, P1_max, a, n) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()


    def edit_record(self):
        """
        Edits the selected record in the propelente database.

        This method retrieves the updated component name and its corresponding 
        values from the entry fields, validates the component name, and then 
        updates the selected record in the database. If the component name 
        is invalid (does not contain at least one letter), an error message 
        is displayed.

        If no record is selected for editing, an error message is shown.

        The method also reassigns IDs to ensure they are consecutive and updates 
        the treeview to reflect the changes.

        Raises:
            sqlite3.Error: If there is an error executing the SQL command.
        """
        component_value = self.get_entry_value(self.entries[self.columnTags[1]])
        component_value = self.get_clean_component_name(component_value)

        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "The component must contain at least one letter.", parent=self.window)
            return

        # Check that `self.selected_id` is defined
        if not hasattr(self, 'selected_id'):
            messagebox.showerror("Invalid Operation", "Select a component to edit.", parent=self.window)
            return

        # Create the tuple of values ​​for the update
        values = (component_value,) + tuple(self.get_entry_value(self.entries[tag]) for tag in self.columnTags[2:]) + (self.selected_id,)

        # Execute the update statement on the database
        self.c.execute("""UPDATE propelente SET 
                        Propelente=?, T_ad=?, MolWeight=?, Cp=?, Cv=?, R=?, gamma=?, cChar=?, Density=?, P1_min=?, P1_max=?, a=?, n=?
                        WHERE id=?""", values)
        
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()


    def delete_record(self):
        """
        Deletes the selected record(s) from the propelente database.

        This method retrieves the IDs of the selected items in the treeview 
        and removes the corresponding records from the database. If multiple 
        records are selected, all of them will be deleted.

        After deletion, the method ensures that IDs are reassigned to maintain 
        consecutive numbering and updates the treeview to reflect the current 
        state of the database.

        Raises:
            sqlite3.Error: If there is an error executing the SQL command.
        """
        selected_items = self.tree.selection()
        if selected_items:
            for selected in selected_items:
                item = self.tree.item(selected)
                record_id = item['values'][0]  # Get the ID of the selected row
                self.c.execute("DELETE FROM propelente WHERE id=?", (record_id,))
            self.conn.commit()
            self.reassign_ids()
            self.update_treeview()


    def reassign_ids(self):
        """
        Reassigns IDs for all records in the propelente database to ensure 
        consecutive numbering starting from 1.

        This method retrieves all records from the propelente table, 
        sorts them by their current ID, and updates each record's ID 
        to a new consecutive value. This is useful after deletions to 
        maintain a clean and organized ID structure.

        Raises:
            sqlite3.Error: If there is an error executing the SQL command.
        """
        # Get all records sorted by the current ID
        self.c.execute("SELECT * FROM propelente ORDER BY id")
        records = self.c.fetchall()

        # Reset ID counter
        new_id = 1

        for record in records:
            old_id = record[0]  # The current ID
            # Update the record with the new ID
            self.c.execute("""
                UPDATE propelente 
                SET id=? 
                WHERE id=?
            """, (new_id, old_id))
            new_id += 1

        self.conn.commit()


    def update_treeview(self):
        """
        Updates the Treeview widget to display the latest records from 
        the propelente database.

        This method clears the existing entries in the Treeview, 
        retrieves the current records from the propelente table, 
        and populates the Treeview with these records. 
        It also updates the values in the combobox to reflect 
        the current components available in the database.

        Raises:
            sqlite3.Error: If there is an error executing the SQL command.
        """
        # Clear the treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert data into the treeview
        self.c.execute("SELECT * FROM propelente")
        for row in self.c.fetchall():
            self.tree.insert("", "end", values=row)  # Include ID but do not display it in the interface

        # Update combobox values
        self.combobox.configure(values=self.get_components())


    def display_burning_rate(self):
        """
        Calculates and displays the burning rate of a propellant based on 
        chamber pressure and specific coefficients (a and n).

        This method retrieves user-input values for coefficients and 
        pressure range, computes the burning rate using the formula:
        
            r(P1) = a * P1^n

        where:
        - r is the burning rate.
        - P1 is the chamber pressure.
        - a and n are user-defined coefficients.

        A plot of the burning rate against chamber pressure is generated 
        and displayed in a new window.

        Raises:
            ValueError: If the user inputs invalid values for coefficients or pressure.
        """
        try:
            name = self.combobox_var.get()
            a = float(self.entries["a"].get())
            n = float(self.entries["n"].get())
            P1_min = float(self.entries["P1_min"].get())
            P1_max = float(self.entries["P1_max"].get())
        except ValueError:
            messagebox.showwarning("Warning", "Please enter valid values.")
            return

        def r(P1, aCoef=a, nCoef=n):
            return a * P1 ** n
        
        Pvalues = np.linspace(P1_min, P1_max, 1000)
        rValues = r(Pvalues)

        # Create the graph and save it to a buffer
        fig, ax = plt.subplots()
        ax.plot(Pvalues, rValues)
        ax.set_xlabel(r'Chamber Pressure $P_1$ ($Pa$)')
        ax.set_ylabel(r'Burning Rate $r$ ($cm/s$)')
        ax.grid(True)
        ax.set_title(f'Propellant: {name}')

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        image = Image.open(buf)

        # Create a new window to display the image
        plot_window = ctk.CTkToplevel(self.window)
        plot_window.title("Burning Rate")

        # Make sure the popup stays in the foreground
        plot_window.transient(self.window)
        plot_window.grab_set()
        plot_window.lift()

        # Display the image in the new window using CTkImage
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
        img_label = ctk.CTkLabel(plot_window, text='', image=ctk_image)
        img_label.image = ctk_image  # Keep a reference to the image
        img_label.pack(fill=tk.BOTH, expand=True)
