from imports import *
from functions import *

from back_0 import *
from back_1 import *
from back_3 import *

class EngineCADModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(2, weight=1)

        self.user_settings = None


        self.tab_view_graphs = ctk.CTkTabview(self.content_frame)
        self.tab_view_graphs.grid(row=0, rowspan=2, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.tab_view_graphs.add("Engine")
        self.tab_view_graphs.add("Tools")
        self.tab_view_graphs.tab("Engine").grid_rowconfigure(0, weight=1)
        self.tab_view_graphs.tab("Engine").grid_rowconfigure(1, weight=1)
        self.tab_view_graphs.tab("Engine").grid_columnconfigure(0, weight=1)
        self.tab_view_graphs.tab("Engine").grid_columnconfigure(1, weight=1)
        self.tab_view_graphs.tab("Tools").grid_rowconfigure(0, weight=1)
        self.tab_view_graphs.tab("Tools").grid_rowconfigure(1, weight=1)
        self.tab_view_graphs.tab("Tools").grid_columnconfigure(0, weight=1)
        self.tab_view_graphs.tab("Tools").grid_columnconfigure(1, weight=1)
        self.tab_view_graphs.grid_propagate(False)


        self.CoverView_frame = ctk.CTkFrame(self.tab_view_graphs.tab("Engine"))
        self.CoverView_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.CoverView_frame.configure(fg_color="white")
        self.CoverView_frame.grid_propagate(False)

        self.EngineView_frame = ctk.CTkFrame(self.tab_view_graphs.tab("Engine"))
        self.EngineView_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.EngineView_frame.configure(fg_color="white")
        self.EngineView_frame.grid_propagate(False)
        
        self.MountView_frame = ctk.CTkFrame(self.tab_view_graphs.tab("Engine"))
        self.MountView_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')
        self.MountView_frame.configure(fg_color="white")
        self.MountView_frame.grid_propagate(False)



        self.CastingMould_frame = ctk.CTkFrame(self.tab_view_graphs.tab("Tools"))
        self.CastingMould_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.CastingMould_frame.configure(fg_color="white")
        self.CastingMould_frame.grid_propagate(False)

        self.CoverView1_frame = ctk.CTkFrame(self.tab_view_graphs.tab("Tools"))
        self.CoverView1_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')
        self.CoverView1_frame.configure(fg_color="white")
        self.CoverView1_frame.grid_propagate(False)
        
        self.CoverView2_frame = ctk.CTkFrame(self.tab_view_graphs.tab("Tools"))
        self.CoverView2_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')
        self.CoverView2_frame.configure(fg_color="white")
        self.CoverView2_frame.grid_propagate(False)



        self.options_frame = ctk.CTkFrame(self.content_frame)
        self.options_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky='nswe')
        self.options_frame.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_rowconfigure(0, weight=1)
        self.options_frame.grid_rowconfigure(1, weight=10)
        self.options_frame.grid_rowconfigure(2, weight=1)
        self.options_frame.grid_propagate(False)

        self.import_frame = ctk.CTkFrame(self.options_frame, height=100)
        self.import_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.import_frame.grid_rowconfigure(0, weight=1)
        self.import_frame.grid_columnconfigure(0, weight=1)
        self.import_frame.grid_columnconfigure(1, weight=1)

        self.load_file_button = ctk.CTkButton(self.import_frame, text="Cargar Motor", command=self.build_entries, width=50)
        self.load_file_button.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.load_file_button.grid_propagate(False)
        
        self.file_path_label = ctk.CTkLabel(self.import_frame, text="No se ha cargado ningún archivo")
        self.file_path_label.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')
        self.file_path_label.grid_propagate(False)

        self.tab_view = ctk.CTkTabview(self.options_frame)
        self.tab_view.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_view.add("Entries")
        self.tab_view.add("Checkboxes")
        self.tab_view.grid_propagate(False)

        # Make sure the tabs expand to fill the available space
        self.tab_view.tab("Entries").grid_rowconfigure(0, weight=1)
        self.tab_view.tab("Entries").grid_columnconfigure(0, weight=1)
        self.tab_view.tab("Checkboxes").grid_rowconfigure(0, weight=1)
        self.tab_view.tab("Checkboxes").grid_columnconfigure(0, weight=1)

        self.entries_tab = ctk.CTkScrollableFrame(self.tab_view.tab("Entries"))
        self.entries_tab.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.entries_tab.grid_columnconfigure(0, weight=1)

        self.checkboxes_tab = ctk.CTkScrollableFrame(self.tab_view.tab("Checkboxes"))
        self.checkboxes_tab.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.checkboxes_tab.grid_columnconfigure(0, weight=1)

        self.export_frame = ctk.CTkFrame(self.options_frame)
        self.export_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nswe')
        self.export_frame.grid_rowconfigure(0, weight=1)
        self.export_frame.grid_rowconfigure(1, weight=1)
        self.export_frame.grid_columnconfigure(0, weight=1)
        self.export_frame.grid_columnconfigure(1, weight=1)

        self.export_engine_button = ctk.CTkButton(self.export_frame, text="Engine Sketch", command=lambda: self.export_sketch(self.user_settings, 'Engine'))
        self.export_engine_button.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        self.export_cover_button = ctk.CTkButton(self.export_frame, text="Cover Sketch", command=lambda: self.export_sketch(self.user_settings, 'Cover'))
        self.export_cover_button.grid(row=0, column=1, padx=10, pady=10, sticky='nswe')

        self.export_mount_button = ctk.CTkButton(self.export_frame, text="Mount Sketch", command=lambda: self.export_sketch(self.user_settings, 'Mount'))
        self.export_mount_button.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')

        self.export_tools_button = ctk.CTkButton(self.export_frame, text="Tools Sketch", command=lambda: self.export_sketch(self.user_settings, 'Tools'))
        self.export_tools_button.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')

        self.widgets_dict = {}

    def build_entries(self, on_load=False, file=None):
        if not on_load:
            file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        else:
            file_path = file

        if file_path:
            self.file_name = os.path.basename(file_path)
            try:
                nozzleData = get_data(type='Nozzles', file=self.file_name)
                nozzle_arch = nozzleData["Inputs"]["NozzleConfig"]

                if nozzle_arch != 'AS-Nozzle':

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
                        'r_elect':          "Radio posición electrodo (m)",
                        'd_elect':          "Diámetro del electrodo (m)",    
                        'upper_offset':     "Offset Superior Montura (m)",
                        'lower_offset':     "Offset Inferior Montura (m)",
                        'T_height':         "Altura de T (m)",
                        'T_Re':             "Anchura exterior de T(m)",
                        'T_Ri':             "Anchura interior de T(m)",
                        'mount_low_len':    "Longitud inferior de Montura (m)", 
                        'mount_high_len':   "Longitud superior de Montura (m)",
                        'rail_len':         "Longitud del rail (m)",
                        "oring":            "Junta tórica - Tobera",
                        "cring":            "Junta tórica - Cubierta",
                        "on_ORing":         "Mostrar Junta tórica - Tobera",
                        "on_CRing":         "Mostrar Junta tórica - Cubierta",
                        "on_Cartridge":     "Mostrar Cartucho",
                        "on_Propellant":    "Mostrar Propelente",
                        "on_Engine":        "Mostrar Motor",
                        "on_Cover":         "Mostrar Cubierta",
                        "on_Axis":          "Mostrar Eje",
                        "on_Background":    "Mostrar Fondo",
                        "on_Mount":         "Mostrar Montura",
                        "t_factor":         "Factor Espesor Tools (%)",
                        "extra_len":        "Longitud Extra de molde (m)",
                        "cover_len":        "Longitud exterior molde (m)",
                        "on_CoverCast1":    "Cubierta de molde",
                        "on_CoverCast2":    "Sujección de molde",
                        "on_CastNut":       "Tuerca de molde",
                        "nut_h":            "Altura de Tuerca (m)",
                        "nut_d":            "Incremento de radio tuerca (m)"
                    }

                    self.engineBuild = EngineCADBuilder_ConventionalNozzle(self.file_name)

                for widget in self.entries_tab.winfo_children():
                    widget.destroy()
                for widget in self.checkboxes_tab.winfo_children():
                    widget.destroy()

                row_entries = 1
                row_checkboxes = 1

                for key, label_text in self.entriesLabelsDic.items():
                    if key == 'type':
                        options = ["Fitted", "Bulk"]
                        optionTypeLabel = ctk.CTkLabel(self.entries_tab, text=label_text)
                        optionTypeLabel.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
                        optionTypeMenu = ctk.CTkOptionMenu(self.entries_tab, values=options, command=self.update_plots)
                        optionTypeMenu.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
                        self.widgets_dict[key] = optionTypeMenu

                    elif '(' in label_text:
                        label = ctk.CTkLabel(self.entries_tab, text=label_text)
                        label.grid(row=row_entries, column=0, padx=10, pady=5, sticky="nsew")
                        entry = ctk.CTkEntry(self.entries_tab)
                        entry.grid(row=row_entries, column=1, padx=10, pady=5, sticky="nsew")
                        entry.bind("<FocusOut>", self.update_plots)
                        self.widgets_dict[key] = entry
                        row_entries += 1
                    else:
                        label = ctk.CTkLabel(self.checkboxes_tab, text=label_text)
                        label.grid(row=row_checkboxes, column=0, padx=10, pady=5, sticky="nsew")
                        checkbox = ctk.CTkCheckBox(self.checkboxes_tab, text="", command=self.update_plots)
                        checkbox.grid(row=row_checkboxes, column=1, padx=10, pady=5, sticky="nsew")
                        checkbox.select()
                        self.widgets_dict[key] = checkbox
                        row_checkboxes += 1


                self.file_path_label.configure(text=self.file_name)
            except Exception as e:
                messagebox.showerror("Error", f"Archivo no válido: {e}", parent=self.content_frame)
                self.file_path_label.configure(text="Archivo Inválido")
                return
            
    def collect_widget_values(self):
        values_dict = {}
        for key, widget in self.widgets_dict.items():
            if isinstance(widget, ctk.CTkOptionMenu):
                values_dict[key] = widget.get()
            elif isinstance(widget, ctk.CTkEntry):
                values_dict[key] = float(get_entry_value(widget))
            elif isinstance(widget, ctk.CTkCheckBox):
                values_dict[key] = widget.get()
        return values_dict
    
    def update_plots(self, event=None):
        try:
            self.user_settings = self.collect_widget_values()
            engine_fig = self.engineBuild.plot_Engine(self.user_settings)
            cover_fig = self.engineBuild.plot_frontCover(self.user_settings)
            mount_fig = self.engineBuild.plot_mount_front(self.user_settings)

            tool_covers_fig = self.engineBuild.plot_Tools(self.user_settings)
            tool_coverFront_1_fig = self.engineBuild.plot_Front1_Tools(self.user_settings)
            tool_coverFront_2_fig = self.engineBuild.plot_Front2_Tools(self.user_settings)

            insert_fig(engine_fig, self.EngineView_frame)
            insert_fig(cover_fig, self.CoverView_frame)
            insert_fig(mount_fig, self.MountView_frame)

            insert_fig(tool_covers_fig, self.CastingMould_frame)
            insert_fig(tool_coverFront_1_fig, self.CoverView1_frame)
            insert_fig(tool_coverFront_2_fig, self.CoverView2_frame)

        except Exception as e:
            print("An error occurred:", e)
            traceback.print_exc()

    def export_sketch(self, user_settings, sketch_type):

        working_path = get_dir_path()
        if not working_path:
            messagebox.showerror("Error", "No se ha seleccionado un directorio de trabajo.", parent=self.content_frame)
            return
        # Preguntar al usuario el nombre del archivo
        file_name = simpledialog.askstring("Guardar archivo", "Introduce el nombre del archivo:", parent=self.content_frame)
        
        if file_name:
            # Asegurarse de que el nombre del archivo termine con '.json'
            if not file_name.endswith('.csv'):
                file_name += '.csv'
            
            # Crear una carpeta llamada "resultados" dentro del directorio de trabajo
            results_folder = os.path.join(working_path, "Sketches")
            os.makedirs(results_folder, exist_ok=True)

            # Construir la ruta completa del archivo
            file_path = os.path.join(results_folder, file_name)

        if sketch_type == 'Engine':
            self.engineBuild.export_engine(user_settings, file_path)

        elif sketch_type == 'Cover':
            self.engineBuild.export_cover(user_settings, file_path)

        elif sketch_type == 'Mount':
            self.engineBuild.export_mount(user_settings, file_path)
        
        elif sketch_type == 'Tools':
            self.engineBuild.export_tools(user_settings, file_path)