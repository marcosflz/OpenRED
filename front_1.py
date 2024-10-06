from imports import *
from functions import *

from back_0 import *


class TermoquimicaWindow:
    instance = None  # Variable de clase para rastrear la instancia

    def __init__(self, parent):
        if TermoquimicaWindow.instance is not None:
            # Si ya existe una instancia, mostrar un mensaje y retornar
            messagebox.showinfo("Info", "La ventana de Termoquímica ya está abierta.", parent=parent)
            return
        # Establecer la instancia de la clase
        TermoquimicaWindow.instance = self

        self.conn = sqlite3.connect('database.db')  # Cambiar el nombre del archivo de base de datos
        self.c = self.conn.cursor()

        # Crear tablas si no existen
        # Moved

        self.columnTags = ("ID", "Component", "MolWeight", "Hf0 (298K)", "minColdTemp", "maxColdTemp", "minHotTemp", "maxHotTemp",
                      "a1_cold", "a2_cold", "a3_cold", "a4_cold", "a5_cold",
                      "a1_hot", "a2_hot", "a3_hot", "a4_hot", "a5_hot")
        
        self.conn.commit()

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Termoquímica")
        self.window.geometry("1200x600")

        # Asegurarse de que la ventana emergente se mantenga en primer plano
        self.window.transient(parent)
        self.window.grab_set()
        self.window.lift()

        # Asociar el evento de cierre para restablecer la instancia de clase
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Crear la estructura de la nueva ventana
        self.entries_frame = ctk.CTkScrollableFrame(self.window, width=300)
        self.entries_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.buttons_frame = ctk.CTkFrame(self.window)
        self.buttons_frame.grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.list_frame = ctk.CTkScrollableFrame(self.window, orientation='horizontal')
        self.list_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Configurar pesos para el grid
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_columnconfigure(2, weight=1)
        self.window.grid_columnconfigure(3, weight=1)

        self.buttons_frame.grid_rowconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)
        self.buttons_frame.grid_columnconfigure(2, weight=1)

        # Agregar los labels en entries_frame
        ctk.CTkLabel(self.entries_frame, text=f"Datos del Componente").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.labels = [ctk.CTkLabel(self.entries_frame, text=self.columnTags[i]) for i in range(1, len(self.columnTags))]  # Excluir ID
        for i, label in enumerate(self.labels):
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky="ew")

        # Obtener componentes de la base de datos
        self.components = self.get_components()

        # Agregar los elementos en entries_frame
        self.entries = []

        self.combobox_var = tk.StringVar()
        self.combobox = ctk.CTkComboBox(self.entries_frame, values=self.components, variable=self.combobox_var)
        self.combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        #self.combobox.set('Comp.')
        self.combobox_var.trace_add("write", self.fill_entries)  # Añadir el evento
        self.entries.append(self.combobox)


        for i in range(1, len(self.columnTags)-1):
            entry = ctk.CTkEntry(self.entries_frame)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.validate_entry)
            entry.bind("<KeyRelease>", self.validate_entry)
            self.entries.append(entry)

        # Hacer que el marco se ajuste dinámicamente
        for i in range(len(self.columnTags) - 1):  # Excluir ID
            self.entries_frame.grid_rowconfigure(i, weight=1)
        self.entries_frame.grid_columnconfigure(1, weight=1)

        # Agregar botones en buttons_frame
        ctk.CTkButton(self.buttons_frame, text="Add", command=self.add_record).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Edit", command=self.edit_record).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.buttons_frame, text="Delete", command=self.delete_record).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Agregar Treeview en list_frame con barras de desplazamiento
        self.tree = ttk.Treeview(self.list_frame, columns=self.columnTags, show="headings")  # Incluir ID para referencia
        for col in self.columnTags:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=100)

        self.tree.pack(expand=True, fill="both", padx=5, pady=5)
        self.reassign_ids()
        self.update_treeview()

    def validate_entry(self, event):
        entry = event.widget
        value = entry.get()
        corrected_value = value.replace(',', '.')

        # Reemplazar la coma por un punto
        if ',' in value:
            entry.delete(0, tk.END)
            entry.insert(0, corrected_value)
            messagebox.showwarning("Formato de número", "Se ha reemplazado la coma por un punto para mantener el formato numérico.", parent=self.window)

        # Validar la notación científica
        if not validate_scientific_notation(corrected_value):
            entry.configure(fg="red")
        else:
            entry.configure(fg="white")


    def get_clean_component_name(self, component):
        # Elimina números entre paréntesis al final del componente
        return re.sub(r'\(\d+\)$', '', component).strip()

    def on_closing(self):
        # Restablecer la instancia de clase cuando la ventana se cierra
        TermoquimicaWindow.instance = None
        self.window.destroy()

    def get_components(self):
        self.c.execute("SELECT id, Component FROM termoquimica")
        components = [f"{row[1]} ({row[0]})" for row in self.c.fetchall()]
        return components

    def get_entry_value(self, widget):
        if isinstance(widget, ctk.CTkComboBox):
            return widget.get()
        return widget.get() if widget.get() else '0'

    def fill_entries(self, *args):
        # Obtener el componente seleccionado
        selected_component = self.combobox_var.get()

        # Extraer el ID del componente seleccionado
        self.selected_id = selected_component.split('(')[-1].strip(')')

        # Obtener los valores correspondientes de la base de datos
        self.c.execute("SELECT * FROM termoquimica WHERE id=?", (self.selected_id,))
        record = self.c.fetchone()

        if record:
            # Rellenar los campos de entrada con los valores correspondientes
            for i, value in enumerate(record):
                if i < 2:
                    continue  # Saltar el ID ya que está en el combobox
                self.entries[i-1].delete(0, tk.END)
                self.entries[i-1].insert(0, value)

    def validate_component(self, component):
        # Verifica que el componente contiene al menos una letra
        return any(char.isalpha() for char in component)

    def add_record(self):
        component_value = self.get_entry_value(self.entries[0])
        component_value = self.get_clean_component_name(component_value)
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "El componente debe contener al menos una letra.", parent=self.window)
            return

        values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:])
        self.c.execute("INSERT INTO termoquimica (Component, MolWeight, Hf0, minColdTemp, maxColdTemp, minHotTemp, maxHotTemp, "
                       "a1_cold, a2_cold, a3_cold, a4_cold, a5_cold, "
                       "a1_hot, a2_hot, a3_hot, a4_hot, a5_hot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()

    def edit_record(self):
        component_value = self.get_entry_value(self.entries[0])
        component_value = self.get_clean_component_name(component_value)
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "El componente debe contener al menos una letra.", parent=self.window)
            return

        # Verificar que `self.selected_id` esté definido
        if not hasattr(self, 'selected_id'):
            messagebox.showerror("Invalid Operation", "Seleccione un componente para editar.", parent=self.window)
            return

        # Crear la tupla de valores para la actualización
        values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:]) + (self.selected_id,)

        # Ejecutar la sentencia de actualización en la base de datos
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
        if selected_items:
            for selected in selected_items:
                item = self.tree.item(selected)
                record_id = item['values'][0]  # Obtener el ID de la fila seleccionada
                self.c.execute("DELETE FROM termoquimica WHERE id=?", (record_id,))
            self.conn.commit()
            self.reassign_ids()
            self.update_treeview()

    def reassign_ids(self):
        # Obtener todos los registros ordenados por el ID actual
        self.c.execute("SELECT * FROM termoquimica ORDER BY id")
        records = self.c.fetchall()

        # Reiniciar el contador de ID
        new_id = 1

        for record in records:
            old_id = record[0]  # El ID actual
            # Actualizar el registro con el nuevo ID
            self.c.execute("""
                UPDATE termoquimica 
                SET id=? 
                WHERE id=?
            """, (new_id, old_id))
            new_id += 1

        self.conn.commit()

    def update_treeview(self):
        # Limpiar el treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insertar datos en el treeview
        self.c.execute("SELECT * FROM termoquimica")
        for row in self.c.fetchall():
            self.tree.insert("", "end", values=row)  # Incluir ID pero no mostrarlo en la interfaz

        # Actualizar valores del combobox
        self.combobox.configure(values=self.get_components())