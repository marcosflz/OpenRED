from imports import *
from functions import *

from back_modules.back_0 import *


class TermoquimicaWindow:
    instance = None  # Class variable to track the instance

    def __init__(self, parent: tk.Tk) -> None:
        """Initialize the Termoquimica window."""
        
        if TermoquimicaWindow.instance is not None:
            # If an instance already exists, show a message and return
            messagebox.showinfo("Info", "The Thermochemistry window is already open.", parent=parent)
            return
        
        # Set the class instance
        TermoquimicaWindow.instance = self

        self.conn = sqlite3.connect('database.db')  # Change the database file name if needed
        self.c = self.conn.cursor()

        # Create tables if they do not exist (moved to a separate method)

        self.columnTags = (
            "ID", "Component", "MolWeight", "Hf0 (298K)", 
            "minColdTemp", "maxColdTemp", "minHotTemp", "maxHotTemp",
            "a1_cold", "a2_cold", "a3_cold", "a4_cold", "a5_cold",
            "a1_hot", "a2_hot", "a3_hot", "a4_hot", "a5_hot"
        )
        
        self.conn.commit()

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Thermochemistry")
        self.window.geometry("1200x600")

        # Ensure the pop-up window stays on top
        self.window.transient(parent)
        self.window.grab_set()
        self.window.lift()

        # Associate the close event to reset the class instance
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create the layout for the new window
        self.entries_frame = ctk.CTkScrollableFrame(self.window, width=300)
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

        # Add labels to the entries frame
        ctk.CTkLabel(self.entries_frame, text="Component Data").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.labels = [ctk.CTkLabel(self.entries_frame, text=self.columnTags[i]) for i in range(1, len(self.columnTags))]  # Exclude ID
        for i, label in enumerate(self.labels):
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky="ew")

        # Retrieve components from the database
        self.components = self.get_components()

        # Add elements to the entries frame
        self.entries = []

        self.combobox_var = tk.StringVar()
        self.combobox = ctk.CTkComboBox(self.entries_frame, values=self.components, variable=self.combobox_var)
        self.combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        # self.combobox.set('Comp.')
        self.combobox_var.trace_add("write", self.fill_entries)  # Add the event
        self.entries.append(self.combobox)

        for i in range(1, len(self.columnTags) - 1):
            entry = ctk.CTkEntry(self.entries_frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.validate_entry)
            entry.bind("<KeyRelease>", self.validate_entry)
            self.entries.append(entry)

        # Make the frame adjust dynamically
        for i in range(len(self.columnTags) - 1):  # Exclude ID
            self.entries_frame.grid_rowconfigure(i, weight=1)
        self.entries_frame.grid_columnconfigure(1, weight=1)

        # Add buttons to the buttons frame
        ctk.CTkButton(self.buttons_frame, text="Add", command=self.add_record).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Edit", command=self.edit_record).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Delete", command=self.delete_record).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Add Treeview to the list frame with scrollbars
        self.tree = ttk.Treeview(self.list_frame, columns=self.columnTags, show="headings")  # Include ID for reference
        for col in self.columnTags:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=100)

        self.tree.pack(expand=True, fill="both", padx=5, pady=5)
        self.reassign_ids()
        self.update_treeview()


    def validate_entry(self, event: tk.Event) -> None:
        """Validate the input entry and format it as needed."""
        
        entry = event.widget
        value = entry.get()
        corrected_value = value.replace(',', '.')

        # Replace comma with a period
        if ',' in value:
            entry.delete(0, tk.END)
            entry.insert(0, corrected_value)
            messagebox.showwarning(
                "Number Format",
                "The comma has been replaced with a period to maintain numerical format.",
                parent=self.window
            )

        # Validate scientific notation
        if not validate_scientific_notation(corrected_value):
            entry.configure(fg="red")  # Set text color to red if invalid
        else:
            entry.configure(fg="white")  # Set text color to white if valid


    def get_clean_component_name(self, component: str) -> str:
        """Remove numbers in parentheses at the end of the component name."""
        
        return re.sub(r'\(\d+\)$', '', component).strip()


    def on_closing(self):
        """Reset the class instance when the window is closed."""
        
        TermoquimicaWindow.instance = None
        self.window.destroy()


    def get_components(self) -> list[str]:
        """Fetch components from the database and format them as 'Component (ID)'."""
        
        self.c.execute("SELECT id, Component FROM termoquimica")
        components = [f"{row[1]} ({row[0]})" for row in self.c.fetchall()]
        return components


    def get_entry_value(self, widget: ctk.CTkEntry | ctk.CTkComboBox) -> str:
        """Retrieve the value from the given widget, returning '0' if the value is empty."""
        
        if isinstance(widget, ctk.CTkComboBox):
            return widget.get()
        return widget.get() if widget.get() else '0'


    def fill_entries(self, *args) -> None:
        """Fill the entry fields with values corresponding to the selected component."""

        # Get the selected component
        selected_component = self.combobox_var.get()

        # Extract the ID from the selected component
        self.selected_id = selected_component.split('(')[-1].strip(')')

        # Retrieve the corresponding values from the database
        self.c.execute("SELECT * FROM termoquimica WHERE id=?", (self.selected_id,))
        record = self.c.fetchone()

        if record:
            # Fill the entry fields with the corresponding values
            for i, value in enumerate(record):
                if i < 2:
                    continue  # Skip the ID since it's in the combobox
                self.entries[i-1].delete(0, tk.END)
                self.entries[i-1].insert(0, value)


    def validate_component(self, component: str) -> bool:
        """Check that the component contains at least one letter."""
        return any(char.isalpha() for char in component)


    def add_record(self):
        component_value = self.get_entry_value(self.entries[0])
        component_value = self.get_clean_component_name(component_value)
        
        # Validate that the component contains at least one letter
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "The component must contain at least one letter.", parent=self.window)
            return

        # Gather all values from the entry fields
        values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:])
        
        # Insert the values into the database
        self.c.execute("INSERT INTO termoquimica (Component, MolWeight, Hf0, minColdTemp, maxColdTemp, minHotTemp, maxHotTemp, "
                    "a1_cold, a2_cold, a3_cold, a4_cold, a5_cold, "
                    "a1_hot, a2_hot, a3_hot, a4_hot, a5_hot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()


    def edit_record(self):
        component_value = self.get_entry_value(self.entries[0])
        component_value = self.get_clean_component_name(component_value)
        
        # Validate that the component contains at least one letter
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "The component must contain at least one letter.", parent=self.window)
            return

        # Check if `self.selected_id` is defined
        if not hasattr(self, 'selected_id'):
            messagebox.showerror("Invalid Operation", "Select a component to edit.", parent=self.window)
            return

        # Create the tuple of values for the update
        values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:]) + (self.selected_id,)

        # Execute the update statement in the database
        self.c.execute("""UPDATE termoquimica SET 
                        Component=?, MolWeight=?, Hf0=?, minColdTemp=?, maxColdTemp=?, minHotTemp=?, maxHotTemp=?, 
                        a1_cold=?, a2_cold=?, a3_cold=?, a4_cold=?, a5_cold=?, 
                        a1_hot=?, a2_hot=?, a3_hot=?, a4_hot=?, a5_hot=? 
                        WHERE id=?""", values)
        
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()


    def delete_record(self):
        selected_items = self.tree.selection()
        
        # Check if any items are selected
        if selected_items:
            for selected in selected_items:
                item = self.tree.item(selected)
                record_id = item['values'][0]  # Get the ID of the selected row
                
                # Execute the delete statement in the database
                self.c.execute("DELETE FROM termoquimica WHERE id=?", (record_id,))
            
            self.conn.commit()  # Commit the changes to the database
            self.reassign_ids()  # Reassign IDs after deletion
            self.update_treeview()  # Update the treeview to reflect changes


    def reassign_ids(self):
        # Get all records ordered by the current ID
        self.c.execute("SELECT * FROM termoquimica ORDER BY id")
        records = self.c.fetchall()

        # Reset the ID counter
        new_id = 1

        for record in records:
            old_id = record[0]  # The current ID
            
            # Update the record with the new ID
            self.c.execute("""
                UPDATE termoquimica 
                SET id=? 
                WHERE id=?
            """, (new_id, old_id))
            new_id += 1  # Increment the new ID for the next record

        self.conn.commit()  # Commit the changes to the database


    def update_treeview(self):
        # Clear the treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert data into the treeview
        self.c.execute("SELECT * FROM termoquimica")
        for row in self.c.fetchall():
            self.tree.insert("", "end", values=row)  # Include ID but do not display it in the interface

        # Update combobox values
        self.combobox.configure(values=self.get_components())