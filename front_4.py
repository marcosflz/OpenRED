from imports import *
from functions import *

from back_0 import *

class NozzleDesingModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=5)
        self.content_frame.grid_rowconfigure(2, weight=5)
        self.content_frame.grid_rowconfigure(3, weight=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=2)

        self.image_label = None
        self.updateIteration = 0

        self.inputs_frame = ctk.CTkFrame(self.content_frame)
        self.inputs_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.inputs_frame.grid_rowconfigure(0,weight=1)
        self.inputs_frame.grid_rowconfigure(1,weight=1)
        self.inputs_frame.grid_rowconfigure(2,weight=1)
        self.inputs_frame.grid_rowconfigure(3,weight=1)
        self.inputs_frame.grid_rowconfigure(4,weight=1)
        self.inputs_frame.grid_rowconfigure(5,weight=1)
        self.inputs_frame.grid_rowconfigure(6,weight=1)
        self.inputs_frame.grid_columnconfigure(0,weight=1)
        self.inputs_frame.grid_columnconfigure(1,weight=1)
        self.inputs_frame.grid_columnconfigure(2,weight=8)


        self.inputsLabel = ctk.CTkLabel(self.inputs_frame, text="Inputs")
        self.inputsLabel.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='nswe')

        

        self.load_file_button = ctk.CTkButton(self.inputs_frame, text="Cargar Motor", command=self.get_engine_data)
        self.load_file_button.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        
        self.file_path_label = ctk.CTkLabel(self.inputs_frame, text="No se ha cargado ningún archivo")
        self.file_path_label.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')

        self.pressureCheck_Box = ctk.CTkSwitch(self.inputs_frame, text="P1 - Media", command=self.toggle_slider, state="disabled")
        self.pressureCheck_Box.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')

        self.pressureSlide_Bar = ctk.CTkSlider(self.inputs_frame, from_=0, to=100, command=self.update_entry)
        self.pressureSlide_Bar.grid(row=2, column=1, padx=10, pady=10, sticky='nswe')
        self.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")

        self.pressure_label = ctk.CTkLabel(self.inputs_frame, text="P1 - Punto Diseño (Pa): ")
        self.pressure_label.grid(row=3, column=0, padx=10, pady=10, sticky='nswe')
        self.pressure_entry = ctk.CTkEntry(self.inputs_frame)
        self.pressure_entry.grid(row=3, column=1, padx=10, pady=10, sticky='nswe')
        self.pressure_entry.bind("<Return>", self.update_from_entry)

        self.nPoints_label = ctk.CTkLabel(self.inputs_frame, text="Puntos - Resolución: ")
        self.nPoints_label.grid(row=4, column=0, padx=10, pady=10, sticky='nswe')
        self.nPoints_entry = ctk.CTkEntry(self.inputs_frame)
        self.nPoints_entry.grid(row=4, column=1, padx=10, pady=10, sticky='nswe')

        nozzles = ["TOPN-BN", "MOC-2D"]
        self.nozzleTypeMenu = ctk.CTkOptionMenu(self.inputs_frame, values=nozzles, command=self.update_options)
        self.nozzleTypeMenu.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')

        self.nozzleOptions = ctk.CTkScrollableFrame(self.inputs_frame)
        self.nozzleOptions.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')

        self.pressureGraph_Frame = ctk.CTkFrame(self.inputs_frame)
        self.pressureGraph_Frame.grid(row=1, column=2, rowspan=6, padx=10, pady=10, sticky='nswe')
        self.pressureGraph_Frame.configure(fg_color="white")
        self.pressureGraph_Frame.grid_propagate(False)
        self.pressureGraph_Frame.bind("<Enter>", command=self.update_plot)

        



        self.graphs_frame = ctk.CTkFrame(self.content_frame)
        self.graphs_frame.grid(row=1, rowspan=2, column=1, padx=10, pady=10, sticky='nswe')

        self.results_frame = ctk.CTkFrame(self.content_frame)
        self.results_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')

        self.calcExport_frame = ctk.CTkFrame(self.content_frame)
        self.calcExport_frame.grid(row=3, column=1, padx=10, pady=10, sticky='nswe')

        self.TOPN_widgets = []
        self.MOC2D_widgets = []
        self.selection = 'TOPN-BN'  # Initialize selection

        self.create_TOPN_entries()
        self.create_MOC2D_entries()
        self.update_options('TOPN-BN')

    def get_engine_data(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            file_name = os.path.basename(file_path)

            with open(file_path, 'r') as file:
                self.engine_Data = json.load(file)

            try:
                self.propellant = self.engine_Data["Propellant"]
                self.P0         = self.engine_Data["P0"]
                self.Rt         = self.engine_Data["Rt"]

                self.meanP      = self.engine_Data["meanPressure"]
                self.maxP       = self.engine_Data["maxPressure"]
                self.minP       = self.engine_Data["minPressure"]

                self.meanG      = self.engine_Data["meanMassFlow"]
                self.maxG       = self.engine_Data["maxMassFlow"]
                self.minG       = self.engine_Data["minMassFlow"]
                
                self.mass       = self.engine_Data["totalMass"]
                self.time       = self.engine_Data["totalTime"]

                self.t          = self.engine_Data["tree_data"]["Tiempo (s)"]
                self.P          = self.engine_Data["tree_data"]["Presi\u00f3n (Pa)"]
                self.G          = self.engine_Data["tree_data"]["Flujo M\u00e1sico (kg/s)"]
                self.M          = self.engine_Data["tree_data"]["Masa (kg)"]

                self.file_path_label.configure(text=file_name)
            except Exception:
                messagebox.showerror("Error", "Archivo no válido.", parent=self.content_frame)
                self.file_path_label.configure(text="Archivo Inválido")
                return

            # Actualizar el slider con el valor máximo de la presión
            self.update_slider()
            # Cambiar el switch a activo
            self.pressureCheck_Box.configure(state="normal")
            self.pressureCheck_Box.select()
            self.toggle_slider()

    def update_slider(self):
        if self.P:
            self.pressureSlide_Bar.configure(from_= self.minP, to=self.maxP)
            self.pressureSlide_Bar.set(self.meanP)
            self.update_entry()

    def update_entry(self, value=None):
        if self.pressureCheck_Box.get() == 1:
            self.pressure_entry.delete(0, tk.END)
            self.pressure_entry.insert(0, str(self.meanP))
        else:
            self.pressure_entry.delete(0, tk.END)
            self.pressure_entry.insert(0, str(self.pressureSlide_Bar.get()))

        self.update_plot()

    def update_from_entry(self, event):
        try:
            pressure_value = float(self.pressure_entry.get())
            if pressure_value < self.minP or pressure_value > self.maxP:
                messagebox.showerror("Valor introducido inválido", f"El valor debe estar entre {self.minP} y {self.maxP}.")
            else:
                self.pressureSlide_Bar.set(pressure_value)
                self.update_plot()
        except ValueError:
            messagebox.showerror("Valor introducido inválido", "Por favor, introduce un número válido.")

    def toggle_slider(self):
        if self.pressureCheck_Box.get() == 1:
            self.pressureSlide_Bar.configure(state="disabled", button_color="gray", button_hover_color="gray")
            self.update_entry()
            self.pressure_entry.configure(state="disabled")
            self.pressureSlide_Bar.set(self.meanP)
            
        else:
            self.pressureSlide_Bar.configure(state="normal", button_color="#1F6AA5", button_hover_color="#144870")
            self.update_entry()
            self.pressure_entry.configure(state="normal")
            

    def update_options(self, selection):
        self.selection = selection
        # Ocultar todos los widgets actuales
        allWidgets = self.TOPN_widgets + self.MOC2D_widgets
        for widget in allWidgets:
            widget.grid_forget()

         # Mostrar los widgets seleccionados
        if selection == "TOPN-BN":
            for i, widget in enumerate(self.TOPN_widgets):
                row, col = divmod(i, 2)
                widget.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
        elif selection == "MOC-2D":
            for i, widget in enumerate(self.MOC2D_widgets):
                row, col = divmod(i, 2)
                widget.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
                

    def create_TOPN_entries(self):
        # Crear entradas específicas para Tubular
        self.TOPN_entries = []
        labels = [
            "K1 (Factor Entrada):",
            "K2 (Factor Garganta):",
            "θₜ (deg):",
            "θₑ (deg):",
            "% (L. Cono):"
        ]

        for i, label_text in enumerate(labels):
            label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry = ctk.CTkEntry(self.nozzleOptions)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            self.TOPN_entries.append(entry)
            self.TOPN_widgets.append(label)
            self.TOPN_widgets.append(entry)

    def create_MOC2D_entries(self):
        # Crear entradas específicas para End-Burner
        self.MOC2D_entries = []
        labels = [
            "End-Burner Param 1:",
            "End-Burner Param 2:",
            "End-Burner Param 3:"
        ]

        for i, label_text in enumerate(labels):
            label = ctk.CTkLabel(self.nozzleOptions, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="nsew")
            entry = ctk.CTkEntry(self.nozzleOptions)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            self.MOC2D_entries.append(entry)
            self.MOC2D_widgets.append(label)
            self.MOC2D_widgets.append(entry)



    def update_plot(self, event=None):
        try:
            # Crear una figura y un eje
            height, width = self.pressureGraph_Frame.winfo_height() / 100, self.pressureGraph_Frame.winfo_width() / 100
            fig, ax = plt.subplots(figsize=(width, width))

            # Dibujar los círculos exteriores e interiores
            ax.plot(self.t, self.P)


            # Añadir título y etiquetas
            ax.set_title("Pressure Profile (Pa)")
            ax.set_xlabel("Time (s)")
            ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
            ax.set_aspect('auto')

            # Obtener el valor del slider
            pressure_value = float(self.pressure_entry.get())

            # Interpolar el valor del tiempo correspondiente a la presión seleccionada
            interpolate_time = interp1d(self.P, self.t, bounds_error=False, fill_value="extrapolate")
            time_value = interpolate_time(pressure_value)

            # Dibujar el punto rojo
            ax.plot(time_value, pressure_value, 'ro', label="Selected Pressure")
            # Ajustar el aspecto del gráfico para evitar la distorsión
            #ax.set_aspect('equal')
            # Añadir título y leyenda
        except Exception:
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.set_axis_off()
        
        # Limpiar el canvas antes de dibujar
        for widget in self.pressureGraph_Frame.winfo_children():
            widget.destroy()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
        plt.close(fig)
        buf.seek(0)
        image = Image.open(buf)

        display_width, display_height = self.pressureGraph_Frame.winfo_width(), self.pressureGraph_Frame.winfo_height()
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(display_width, display_width))

        if self.image_label:
            self.image_label.destroy()

        self.image_label = ctk.CTkLabel(self.pressureGraph_Frame, text="", image=ctk_image)
        self.image_label.image = ctk_image
        pad4x = abs((display_width-display_height)/2 - 0.05 * (display_width-display_height)/2)
        self.image_label.grid(row=0, column=0, padx=0.05, pady=0, sticky="nsew")
