from imports import *
from functions import *

from back_0 import *

class PropellantWindow:
    instance = None  # Variable de clase para rastrear la instancia

    def __init__(self, parent):
        if PropellantWindow.instance is not None:
            # Si ya existe una instancia, mostrar un mensaje y retornar
            messagebox.showinfo("Info", "La ventana de Propelente ya está abierta.", parent=parent)
            return
        # Establecer la instancia de la clase
        PropellantWindow.instance = self

        self.conn = sqlite3.connect('database.db')  # Cambiar el nombre del archivo de base de datos
        self.c = self.conn.cursor()

        # Crear tablas si no existen
        # Moved to app

        self.columnTags = ("id", "Propelente", "T_ad", "MolWeight", "Cp", "Cv", "R", "gamma", "cChar", "Density", "P1_min", "P1_max", "a", "n")
        
        self.conn.commit()

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Propelentes")
        self.window.geometry("1200x600")

        # Asegurarse de que la ventana emergente se mantenga en primer plano
        self.window.transient(parent)
        self.window.grab_set()
        self.window.lift()

        # Asociar el evento de cierre para restablecer la instancia de clase
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Crear la estructura de la nueva ventana
        self.entries_frame = ctk.CTkScrollableFrame(self.window, width=350)
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
        ctk.CTkLabel(self.entries_frame, text=f"Datos del Propelente").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.labels = [ctk.CTkLabel(self.entries_frame, text=self.columnTags[i]) for i in range(1, len(self.columnTags))]  # Excluir ID
        for i, label in enumerate(self.labels):
            label.grid(row=i+1, column=0, padx=5, pady=5, sticky="ew")

        # Obtener componentes de la base de datos
        self.components = self.get_components()

        # Agregar los elementos en entries_frame
        self.entries = {}

        self.combobox_var = tk.StringVar()
        self.combobox = ctk.CTkComboBox(self.entries_frame, values=self.components, variable=self.combobox_var)
        self.combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        #self.combobox.set('Comp.')
        self.combobox_var.trace_add("write", self.fill_entries)  # Añadir el evento
        self.entries["Propelente"] = self.combobox

        
        # Crear los entries en el entries_frame y almacenarlos en el diccionario
        for i, tag in enumerate(self.columnTags[2:], start=2):  # Excluir "id"
            entry = ctk.CTkEntry(self.entries_frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.validate_entry)
            entry.bind("<KeyRelease>", self.validate_entry)
            self.entries[tag] = entry

        self.burningRateGraph = ctk.CTkButton(self.entries_frame, text="Mostar curva Burning Rate", command=self.display_burning_rate)
        self.burningRateGraph.grid(row=i+1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")


        #for i in range(1, len(self.columnTags)-1):
        #    entry = ctk.CTkEntry(self.entries_frame)
        #    entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="ew")
        #    entry.bind("<FocusOut>", self.validate_entry)
        #    entry.bind("<KeyRelease>", self.validate_entry)
        #    self.entries.append(entry)

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
        PropellantWindow.instance = None
        self.window.destroy()

    def get_components(self):
        self.c.execute("SELECT id, Propelente FROM propelente")
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
        self.c.execute("SELECT * FROM propelente WHERE id=?", (self.selected_id,))
        record = self.c.fetchone()

        if record:
            # Rellenar los campos de entrada con los valores correspondientes
            for i, value in enumerate(record):
                if i < 2:
                    continue  # Saltar el ID ya que está en el combobox
                tag = self.columnTags[i]
                self.entries[tag].delete(0, tk.END)
                self.entries[tag].insert(0, value)

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
        self.c.execute("INSERT INTO propelente (Propelente, T_ad, MolWeight, Cp, Cv, R, gamma, cChar, Density, P1_min, P1_max, a, n)"
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        self.conn.commit()
        self.reassign_ids()
        self.update_treeview()

    def edit_record(self):
        
        component_value = self.get_entry_value(self.entries[self.columnTags[1]])
        component_value = self.get_clean_component_name(component_value)
        if not self.validate_component(component_value):
            messagebox.showerror("Invalid Input", "El componente debe contener al menos una letra.", parent=self.window)
            return

        # Verificar que `self.selected_id` esté definido
        if not hasattr(self, 'selected_id'):
            messagebox.showerror("Invalid Operation", "Seleccione un componente para editar.", parent=self.window)
            return

        # Crear la tupla de valores para la actualización
        # values = (component_value,) + tuple(self.get_entry_value(widget) for widget in self.entries[1:]) + (self.selected_id,)
        values = (component_value,) + tuple(self.get_entry_value(self.entries[tag]) for tag in self.columnTags[2:]) + (self.selected_id,)

        # Ejecutar la sentencia de actualización en la base de datos
        self.c.execute("""UPDATE propelente SET 
                          Propelente=?, T_ad=?, MolWeight=?, Cp=?, Cv=?, R=?, gamma=?, cChar=?, Density=?, P1_min=?, P1_max=?, a=?, n=?
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
                self.c.execute("DELETE FROM propelente WHERE id=?", (record_id,))
            self.conn.commit()
            self.reassign_ids()
            self.update_treeview()

    def reassign_ids(self):
        # Obtener todos los registros ordenados por el ID actual
        self.c.execute("SELECT * FROM propelente ORDER BY id")
        records = self.c.fetchall()

        # Reiniciar el contador de ID
        new_id = 1

        for record in records:
            old_id = record[0]  # El ID actual
            # Actualizar el registro con el nuevo ID
            self.c.execute("""
                UPDATE propelente 
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
        self.c.execute("SELECT * FROM propelente")
        for row in self.c.fetchall():
            self.tree.insert("", "end", values=row)  # Incluir ID pero no mostrarlo en la interfaz

        # Actualizar valores del combobox
        self.combobox.configure(values=self.get_components())

    def display_burning_rate(self):
        try:
            name = self.combobox_var.get()
            a = float(self.entries["a"].get())
            n = float(self.entries["n"].get())
            P1_min = float(self.entries["P1_min"].get())
            P1_max = float(self.entries["P1_max"].get())
        except ValueError:
            messagebox.showwarning("Aviso", "Por favor, ingrese valores válidos.")
            return

        def r(P1, aCoef = a, nCoef = n):
            return a * P1 ** n
        
        Pvalues = np.linspace(P1_min, P1_max, 1000)
        rValues = r(Pvalues)
    

        # Crear el gráfico y guardarlo en un buffer
        fig, ax = plt.subplots()
        ax.plot(Pvalues, rValues)
        ax.set_xlabel(r'Chamber Pressure $P_1$ ($Pa$)')
        ax.set_ylabel(r'Burning Rate $r$ ($cm/s$)')
        ax.grid(True)
        ax.set_title(f'Propelente: {name}')

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        image = Image.open(buf)

        # Crear una nueva ventana para mostrar la imagen
        plot_window = ctk.CTkToplevel(self.window)
        plot_window.title("Tasa de Combustión")

        # Asegurarse de que la ventana emergente se mantenga en primer plano
        plot_window.transient(self.window)
        plot_window.grab_set()
        plot_window.lift()

        # Mostrar la imagen en la nueva ventana usando CTkImage
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
        img_label = ctk.CTkLabel(plot_window, image=ctk_image)
        img_label.image = ctk_image  # Mantener una referencia a la imagen
        img_label.pack(fill=tk.BOTH, expand=True)
