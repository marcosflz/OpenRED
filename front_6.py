from imports import *
from functions import *

from back_0 import *
from back_1 import *
#from back_2 import *
from back_3 import *



class TestingBedModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=5)
        self.content_frame.grid_rowconfigure(2, weight=5)

        self.content_frame.grid_columnconfigure(0, weight=2)
        self.content_frame.grid_columnconfigure(1, weight=5)
        self.content_frame.grid_columnconfigure(2, weight=5)

        self.serialRecording = False
        self.last_processed_line = ""
        self.maxThrust = 0
        self.maxTemp = 0

        self.records = np.array([]).reshape(0, 3)

        self.runFrame = ctk.CTkFrame(self.content_frame, height=10)
        self.runFrame.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.runFrame.grid_rowconfigure(0, weight=1)
        self.runFrame.grid_columnconfigure(0, weight=1)
        self.runFrame.grid_propagate(False)

        self.run_button = ctk.CTkButton(self.runFrame, text="Run", command=self.run_test)
        self.run_button.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        self.optionsFrame = ctk.CTkFrame(self.content_frame, height=10)
        self.optionsFrame.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky='nswe')
        self.optionsFrame.grid_rowconfigure(0, weight=1)
        self.optionsFrame.grid_columnconfigure(0, weight=1)
        self.optionsFrame.grid_columnconfigure(1, weight=1)
        self.optionsFrame.grid_columnconfigure(2, weight=1)
        self.optionsFrame.grid_columnconfigure(3, weight=1)
        self.optionsFrame.grid_columnconfigure(4, weight=1)
        self.optionsFrame.grid_columnconfigure(5, weight=1)
        self.optionsFrame.grid_columnconfigure(6, weight=1)
        self.optionsFrame.grid_columnconfigure(7, weight=1)
        self.optionsFrame.grid_columnconfigure(8, weight=1)
        self.optionsFrame.grid_propagate(False)

        self.ports_label = ctk.CTkLabel(self.optionsFrame, text="Puerto de Conexión USB:")
        self.ports_label.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        self.com_ports = [port.device for port in serial.tools.list_ports.comports()]

        if not self.com_ports:
            self.com_ports = ["No COM ports found"]

        # Connect the com_port_changed method to the OptionMenu's command parameter
        self.com_option_menu = ctk.CTkOptionMenu(self.optionsFrame, values=self.com_ports, command=self.com_port_changed)
        self.com_option_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.connect_com_button = ctk.CTkButton(self.optionsFrame, text="Conectar", command=self.connect_com)
        self.connect_com_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.connect_com_button.configure(fg_color="red")
        self.com_connected = False

        # self.connection_indicator_com = ctk.CTkLabel(self.optionsFrame, text="USB-PORT", fg_color="red", width=10, height=10)
        # self.connection_indicator_com.grid(row=0, column=3, padx=5, pady=10, sticky="w")
        # self.connection_indicator_com.configure(state="disabled")  # Disable indicator

        self.testBed_SSID_label = ctk.CTkLabel(self.optionsFrame, text="SSID:")
        self.testBed_SSID_label.grid(row=0, column=3, padx=10, pady=10, sticky='nswe')

        self.testBed_SSID_entry = ctk.CTkEntry(self.optionsFrame)
        self.testBed_SSID_entry.grid(row=0, column=4, padx=10, pady=10, sticky='nswe')

        self.testBed_password_label = ctk.CTkLabel(self.optionsFrame, text="Password:")
        self.testBed_password_label.grid(row=0, column=5, padx=10, pady=10, sticky='nswe')

        self.testBed_password_entry = ctk.CTkEntry(self.optionsFrame)
        self.testBed_password_entry.grid(row=0, column=6, padx=10, pady=10, sticky='nswe')

        self.connect_wifi_button = ctk.CTkButton(self.optionsFrame, text="Conectar", command=self.connect_wifi)
        self.connect_wifi_button.grid(row=0, column=7, padx=10, pady=10, sticky="e")
        self.connect_wifi_button.configure(fg_color="red")
        self.wifi_connected = False

        # self.connection_indicator_wifi = ctk.CTkLabel(self.optionsFrame, text="TEST-BED", fg_color="red", width=10, height=10)
        # self.connection_indicator_wifi.grid(row=0, column=9, padx=5, pady=10, sticky="w")
        # self.connection_indicator_wifi.configure(state="disabled")  # Disable indicator

        self.abort_button = ctk.CTkButton(self.optionsFrame, text="Abortar", command=self.abort_test)
        self.abort_button.grid(row=0, column=8, padx=10, pady=10, sticky='nswe')

        self.serialFrame = ctk.CTkFrame(self.content_frame)
        self.serialFrame.grid(row=1, column=0, rowspan=2, padx=10, pady=10, sticky='nswe')
        self.serialFrame.grid_propagate(False)
        self.serialFrame.grid_rowconfigure(0, weight=1)
        self.serialFrame.grid_columnconfigure(0, weight=1)


        # Create a text box for displaying serial monitor output
        self.serial_monitor_text = ctk.CTkTextbox(self.serialFrame)
        self.serial_monitor_text.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.serial_monitor_text.configure(state="disabled")  # Initially disabled
        self.serial_monitor_text.bind("<<Modified>>", self.on_textbox_change)




        self.display_1_frame = ctk.CTkFrame(self.content_frame)
        self.display_1_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')
        self.display_1_frame.grid_propagate(False)

        self.display_2_frame = ctk.CTkFrame(self.content_frame)
        self.display_2_frame.grid(row=1, column=2, padx=10, pady=10, sticky='nswe')
        self.display_2_frame.grid_propagate(False)

        self.display_3_frame = ctk.CTkFrame(self.content_frame)
        self.display_3_frame.grid(row=2, column=1, padx=10, pady=10, sticky='nswe')
        self.display_3_frame.grid_propagate(False)
        self.display_3_frame.grid_rowconfigure(0, weight=1)
        self.display_3_frame.grid_rowconfigure(1, weight=1)
        self.display_3_frame.grid_columnconfigure(0, weight=1)
        self.display_3_frame.grid_columnconfigure(1, weight=1)

        self.display_4_frame = ctk.CTkFrame(self.content_frame)
        self.display_4_frame.grid(row=2, column=2, padx=10, pady=10, sticky='nswe')
        self.display_4_frame.grid_propagate(False)



        self.fig_Thrust, self.ax_Thrust = plt.subplots()
        self.update_Thrust_plot()
        insert_fig(self.fig_Thrust, self.display_2_frame)

        self.fig_Temp, self.ax_Temp = plt.subplots()
        self.update_Temp_plot()
        insert_fig(self.fig_Temp, self.display_4_frame)

        self.fig_Gauge = gaugePlot(instValues=[0,0,0,0], maxValues=[1,1,1,1])
        insert_fig(self.fig_Gauge, self.display_3_frame, resize='Manual', l=0.05, r=0.95, t=0.95, b=0.05)

        self.reset_plots()

        # Crear el checklist en checkListFrame
        self.create_checklist()
        self.checklist_completed = False

        # Deshabilitar el checklist y los widgets de optionsFrame inicialmente
        self.disable_checklist()
        self.disable_options()

        # Iniciar el hilo de monitoreo de puertos
        self.monitor_thread = threading.Thread(target=self.monitor_ports, daemon=True)
        self.monitor_thread.start()

        # Deshabilitar inicialmente las entradas y el botón de WiFi
        self.disable_wifi_options()






    def on_textbox_change(self, event):
        """Callback que se ejecuta cuando se modifica el contenido del CTkTextbox."""
        # Obtener la última línea del CTkTextbox
        last_line = self.serial_monitor_text.get("end-2l", "end-1c").strip()

        # Verificar si la grabación está habilitada y procesar la última línea
        if self.serialRecording and last_line != self.last_processed_line:
            result = getSerialValues(last_line)
            if result:
                # Convertir el resultado a una tupla para comparar fácilmente
                record_tuple = tuple(result)
                
                # Convertir la tupla en un array numpy
                record_array = np.array(record_tuple).reshape(1, 3)

                # Verificar si el registro no está ya en el array
                if not any(np.all(record_array == row) for row in self.records):
                    # Append el nuevo registro al array de numpy
                    self.records = np.vstack([self.records, record_array])

                    # Guardar el nuevo registro en el archivo CSV
                    self.save_record_to_csv(record_tuple)

                    # Run the plot updates in a separate thread
                    threading.Thread(target=self.update_plots, daemon=True).start()

                # Actualizar la última línea procesada
                self.last_processed_line = last_line

        # Restablecer el estado modificado del TextBox para futuras detecciones
        self.serial_monitor_text.edit_modified(False)

    def update_plots(self):
        """Run all plot updates in a separate thread."""
        # Schedule GUI updates on the main thread
        self.content_frame.after(0, self.update_Thrust_plot)
        self.content_frame.after(0, self.update_Temp_plot)
        self.content_frame.after(0, self.update_Gauge_plot)

    def reset_plots(self):
        """Reinicia los gráficos a su estado inicial."""
        # Run the plot resets in a separate thread
        threading.Thread(target=self._reset_plots_thread, daemon=True).start()

    def _reset_plots_thread(self):
        """Thread-safe method to reset plots."""
        self.content_frame.after(0, self._reset_plots_gui)

    def _reset_plots_gui(self):
        """Reset plots on the main GUI thread."""
        # Limpiar y redibujar el gráfico de Thrust
        self.ax_Thrust.clear()
        self.update_Thrust_plot()
        self.fig_Thrust.canvas.draw()

        # Limpiar y redibujar el gráfico de Temperatura
        self.ax_Temp.clear()
        self.update_Temp_plot()
        self.fig_Temp.canvas.draw()

        self.fig_Gauge = gaugePlot(instValues=[0, 0, 0, 0], maxValues=[1, 1, 1, 1])
        insert_fig(self.fig_Gauge, self.display_3_frame, resize='Manual', l=0.05, r=0.95, t=0.95, b=0.05)

        # Limpiar los registros
        self.records = np.array([]).reshape(0, 3)  # Reiniciar el array a vacío

    def update_Thrust_plot(self):
        """Función de actualización para el gráfico en tiempo real."""
        self.ax_Thrust.clear()

        if len(self.records) > 0:
            times = self.records[:, 0]  # Extraer la columna de tiempo
            thrusts = self.records[:, 1]  # Extraer la columna de fuerza
            self.ax_Thrust.plot(times, thrusts)

        self.ax_Thrust.set_xlabel('Tiempo (s)')
        self.ax_Thrust.set_ylabel('F(Kg)')
        self.ax_Thrust.set_title('Thrust')

        self.fig_Thrust.canvas.draw_idle()
        plt.close(self.fig_Thrust)

    def update_Temp_plot(self):
        """Función de actualización para el gráfico en tiempo real."""
        self.ax_Temp.clear()

        if len(self.records) > 0:
            times = self.records[:, 0]  # Extraer la columna de tiempo
            temps = self.records[:, 2]  # Extraer la columna de temperatura
            self.ax_Temp.plot(times, temps, label='Temperatura (K)')

        self.ax_Temp.set_xlabel('Tiempo (s)')
        self.ax_Temp.set_ylabel('T(K)')
        self.ax_Temp.set_title('Temperature')

        self.fig_Temp.canvas.draw_idle()
        plt.close(self.fig_Temp)

    def update_Gauge_plot(self):
        if len(self.records) != 0:
            thrust = self.records[-1, 1]
            temp = self.records[-1, 2]
        else:
            thrust = 0
            temp = 0

        self.fig_Gauge = gaugePlot(instValues=[thrust, temp, 1, 1], maxValues=[self.maxThrust, self.maxTemp, 1, 1])
        insert_fig(self.fig_Gauge, self.display_3_frame, resize='Manual', l=0.05, r=0.95, t=0.95, b=0.05)















    def abort_test(self):
        """Abort the current test, send a RESET command, and reset the class state."""
        # Send the RESET command if the serial connection is open
        if hasattr(self, 'serial_connection') and self.serial_connection.is_open:
            try:
                self.serial_connection.write(b'ABORT\n')
                self.send_serial_reset()  # Send RESET command
                self.serial_monitor_text.insert("end", "\nTest aborted. Reset command sent.\n")
                self.serial_monitor_text.yview("end")
            except serial.SerialException as e:
                messagebox.showerror("Error", f"Failed to send RESET command: {e}")

        # Reset the class state
        
        self.com_port_changed(None)
        

    def checklist_status(self):
        """Verifica si la checklist está completa y envía un comando por serial."""
        self.checklist_completed = all(checkbox.get() for checkbox in self.checkboxes)
            
        if self.checklist_completed:
            if hasattr(self, 'serial_connection') and self.serial_connection.is_open:
                try:
                    self.serial_connection.write(b'SWITCH START-RECORDING-LED\n')
                    self.serialRecording = True
                    self.reset_plots()
                except serial.SerialException as e:
                    messagebox.showerror("Error", f"Error al enviar comando por serial: {e}")
                        
            else:
                messagebox.showerror("Error", "La conexión serial no está abierta.")
                


    def on_close(self):
        """Método que se ejecuta al cerrar la ventana principal."""
        # Enviar comandos para poner los LEDs en azul
        if hasattr(self, 'serial_connection') and self.serial_connection.is_open:
            try:
                self.send_serial_blue()
                self.send_wifi_blue()
                self.send_serial_reset()
            except serial.SerialException as e:
                print(f"Error al enviar comandos de cierre: {e}")

        # Cerrar la conexión serial si está abierta
        if hasattr(self, 'serial_connection') and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
            except serial.SerialException as e:
                print(f"Error al cerrar la conexión serial: {e}")

        # Cerrar la aplicación
        self.content_frame.master.destroy()

    def reset_checklist(self):
        """Deselect all checkboxes in the checklist."""
        for checkbox in self.checkboxes:
            checkbox.deselect()  # Uncheck each checkbox

    def create_checklist(self):
        """
        Crea una checklist dinámicamente en el frame correspondiente.
        Si no se encuentra el archivo o hay un error al cargar los datos, no se muestra nada.
        """
        try:
            # Leer el directorio de trabajo desde el archivo temp_dir.txt
            with open('temp_dir.txt', 'r') as file:
                working_directory = file.read().strip()

            # Construir la ruta completa al archivo checklist.json
            checklist_file_path = os.path.join(working_directory, 'checklist.json')

            # Leer el archivo checklist.json
            with open(checklist_file_path, 'r') as file:
                checklist_data = json.load(file)

            # Obtener los títulos de las actividades desde el archivo JSON
            label_texts = checklist_data.get('Checklist', [])

        except (FileNotFoundError, json.JSONDecodeError):
            # Si hay un error, no se muestra nada en el frame de la checklist
            label_texts = []

        # Configurar columnas para alineación
        self.display_1_frame.grid_columnconfigure(0, weight=8)  # Columna para labels
        self.display_1_frame.grid_columnconfigure(1, weight=1)  # Columna para checkboxes

        # Añadir un título al frame
        title_label = ctk.CTkLabel(self.display_1_frame, text="TEST CHECKLIST", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky="n")

        # Crear listas para guardar los labels y checkboxes
        self.labels = []
        self.checkboxes = []

        # Crear labels y checkboxes usando un for loop
        for i, text in enumerate(label_texts):
            label = ctk.CTkLabel(self.display_1_frame, text=text)
            checkbox = ctk.CTkCheckBox(self.display_1_frame, text="", command=self.checklist_status)

            # Posicionar label y checkbox
            label.grid(row=i + 1, column=0, padx=10, pady=5, sticky="w")
            checkbox.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")

            # Añadir a las listas
            self.labels.append(label)
            self.checkboxes.append(checkbox)

        # Deshabilitar la checklist inicialmente
        self.disable_checklist()

    def disable_checklist(self):
        # Deshabilitar todos los checkboxes y oscurecer los labels
        for label, checkbox in zip(self.labels, self.checkboxes):
            label.configure(text_color="gray")  # Oscurecer el texto del label
            checkbox.configure(state="disabled", fg_color="gray")  # Deshabilitar y cambiar el color del checkbox

    def off_checklist(self):
        """Desmarca todos los checkboxes en el checklist."""
        for checkbox in self.checkboxes:
            checkbox.deselect()  # Desmarcar cada checkbox

    def enable_checklist(self):
        # Habilitar todos los checkboxes y restaurar los labels
        for label, checkbox in zip(self.labels, self.checkboxes):
            label.configure(text_color="white")  # Restaurar el color del texto del label
            checkbox.configure(state="normal", fg_color="green")  # Habilitar y restaurar el color del checkbox

    def disable_options(self):
        """Deshabilitar todos los widgets en optionsFrame."""
        self.ports_label.configure(state="disabled")
        self.com_option_menu.configure(state="disabled")

        self.testBed_SSID_label.configure(state="disabled")
        self.testBed_SSID_entry.configure(state="disabled")

        self.testBed_password_label.configure(state="disabled")
        self.testBed_password_entry.configure(state="disabled")

        self.connect_com_button.configure(state="disabled")
        self.connect_wifi_button.configure(state="disabled")

    def disable_wifi_options(self):
        """Deshabilitar las entradas de SSID y contraseña, y el botón de conexión WiFi."""
        self.testBed_SSID_entry.configure(state="disabled")
        self.testBed_password_entry.configure(state="disabled")
        self.connect_wifi_button.configure(state="disabled")

    def enable_wifi_options(self):
        """Habilitar las entradas de SSID y contraseña, y el botón de conexión WiFi."""
        self.testBed_SSID_entry.configure(state="normal")
        self.testBed_password_entry.configure(state="normal")
        self.connect_wifi_button.configure(state="normal")

    def run_test(self):
        # Leer el directorio de trabajo desde el archivo 'temp_dir.txt'
        try:
            with open('temp_dir.txt', 'r') as temp_file:
                working_directory = temp_file.read().strip()
        except FileNotFoundError:
            messagebox.showerror("Error", "No se ha abierto ningun directorio de trabajo'.")
            return

        # Definir la subcarpeta 'Nozzles' dentro del directorio de trabajo
        nozzles_folder = os.path.join(working_directory, 'Nozzles')

        # Abrir cuadro de diálogo para seleccionar un archivo JSON dentro de la subcarpeta 'Nozzles'
        nozzle_file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de boquillas",
            initialdir=nozzles_folder,
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )

        if nozzle_file_path:  # Si el usuario selecciona un archivo
            # Extraer el nombre del archivo sin la extensión
            nozzle_name = os.path.splitext(os.path.basename(nozzle_file_path))[0]

            # Obtener la hora y fecha actual para el nombre del archivo CSV
            current_time = datetime.now().strftime("%H.%M.%S-%d.%m.%y")  # Formato: HH.MM.SS-DD.MM.AA

            # Crear el nombre del archivo CSV en la subcarpeta 'Tests'
            tests_folder = os.path.join(working_directory, 'Tests')
            csv_filename = f"{nozzle_name}-{current_time}.csv"
            csv_file_path = os.path.join(tests_folder, csv_filename)

            # Leer el archivo JSON seleccionado para extraer los valores de interés
            with open(nozzle_file_path, 'r') as json_file:
                nozzle_data = json.load(json_file)

            # Extraer valores de 'Med. Thrust (kg)' y 'Ts (Med.)'
            
            engineUsed = nozzle_data["Inputs"]["EngineConfig"]
            engineData = get_data(type='Engines', file=engineUsed)

            self.maxThrust = nozzle_data["calculatedResults"]["Med. Thrust (kg)"]
            propellant = engineData["Propellant"]
            self.maxTemp = get_propellant_value('T_ad', propellant)[0]
            

            # Crear el archivo CSV y escribir la hora en la primera línea
            with open(csv_file_path, 'w', newline='') as file:
                file.write(f"t(s),F(kg),T(K)\n")

            # Guardar la ruta del archivo CSV en una variable de la clase
            self.file_path = csv_file_path

            # Habilitar el checklist y los widgets de optionsFrame
            self.ports_label.configure(state="normal")
            self.com_option_menu.configure(state="normal")
            self.connect_com_button.configure(state="normal")

            self.disable_checklist()
            self.off_checklist()

            self.disable_wifi_options()
            self.com_port_changed(None)
            self.reset_plots()

            # Mostrar mensaje de éxito con la ruta del archivo CSV creado
            messagebox.showinfo("Éxito", f"Archivo CSV creado: {csv_file_path}")
        else:
            messagebox.showinfo("Cancelado", "No se seleccionó ningún archivo JSON.")



    def monitor_ports(self):
        """Monitorea continuamente los puertos COM y actualiza el OptionMenu si hay cambios."""
        previous_ports = self.com_ports
        while True:
            # Retrieve current list of ports with description
            current_ports_info = serial.tools.list_ports.comports()

            # Extract descriptions or names for each port
            current_ports = [f"{port.device} - {port.description}" for port in current_ports_info]

            # Check if the ports have changed
            if current_ports != previous_ports:
                self.com_ports = current_ports if current_ports else ["No COM ports found"]
                self.com_option_menu.configure(values=self.com_ports)
                previous_ports = current_ports

                # Reset connection indicator if ports change
                self.com_port_changed(None)

            time.sleep(1)  # Monitorea cada segundo

    def connect_com(self):
        """Función para conectar al puerto COM y enviar el comando RESET."""
        # Get the selected port (e.g., "COM3 - USB Serial Device")
        selected_port_info = self.com_option_menu.get()

        if selected_port_info == "No COM ports found":
            messagebox.showerror("Error", "No hay puertos COM disponibles.")
            return

        # Extract only the COM port (e.g., "COM3") from the selected option
        selected_port = selected_port_info.split(' - ')[0]  # Split and take the first part

        # Cerrar cualquier conexión serial previa si está abierta
        if hasattr(self, 'serial_connection') and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                self.serial_monitor_text.insert("end", "\nConexión serial previa cerrada.\n")
                self.serial_monitor_text.yview("end")
            except serial.SerialException as e:
                messagebox.showerror("Error", f"No se pudo cerrar la conexión serial previa: {e}")

        try:
            # Conectar al puerto COM seleccionado
            self.serial_connection = serial.Serial(port=selected_port, baudrate=115200, timeout=1)
            self.com_connected = True

            # Enviar el comando RESET
            self.serial_connection.write(b'RESET\n')

            # Iniciar un hilo para leer y mostrar la salida del serial en el Textbox
            self.read_serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.read_serial_thread.start()

        except serial.SerialException as e:
            messagebox.showerror("Error", f"No se pudo conectar al puerto COM: {e}")
            self.com_connected = False
            self.connect_com_button.configure(fg_color="red")  # Change button color







    


























#    def on_textbox_change(self, event):
#        """Callback que se ejecuta cuando se modifica el contenido del CTkTextbox."""
#        # Obtener la última línea del CTkTextbox
#        last_line = self.serial_monitor_text.get("end-2l", "end-1c").strip()
#
#        # Verificar si la grabación está habilitada y procesar la última línea
#        if self.serialRecording and last_line != self.last_processed_line:
#            result = getSerialValues(last_line)
#            if result:
#                # Convertir el resultado a una tupla para comparar fácilmente
#                record_tuple = tuple(result)
#                
#                # Convertir la tupla en un array numpy
#                record_array = np.array(record_tuple).reshape(1, 3)
#
#                # Verificar si el registro no está ya en el array
#                if not any(np.all(record_array == row) for row in self.records):
#                    # Append el nuevo registro al array de numpy
#                    self.records = np.vstack([self.records, record_array])
#
#                    # Guardar el nuevo registro en el archivo CSV
#                    self.save_record_to_csv(record_tuple)
#
#                    # Actualizar los gráficos
#                    self.update_Thrust_plot()
#                    self.update_Temp_plot()
#                    self.update_Gauge_plot()
#
#                # Actualizar la última línea procesada
#                self.last_processed_line = last_line
#
#        # Restablecer el estado modificado del TextBox para futuras detecciones
#        self.serial_monitor_text.edit_modified(False)

    def save_record_to_csv(self, record_tuple):
        """Guarda un registro individual en el archivo CSV."""
        # Verificar si el directorio del archivo CSV está definido
        if hasattr(self, 'file_path') and self.file_path:
            with open(self.file_path, 'a', newline='') as csvfile:  # Abre el archivo en modo de agregar
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(record_tuple)  # Escribe el registro como una nueva línea en el archivo CSV




    def read_serial_data(self):
        """Leer datos del puerto serial y mostrarlos en el CTkTextbox."""
        self.serial_monitor_text.configure(state="normal")
        self.serial_monitor_text.delete("1.0", "end")  # Limpiar el CTkTextbox antes de mostrar nuevo contenido

        try:
            while self.serial_connection.is_open:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting).decode('utf-8')

                    # Si se detecta "SERIAL STARTED", limpiar contenido previo
                    if "SERIAL STARTED" in data:
                        self.serial_monitor_text.delete("1.0", "end")
                        serial_started_index = data.index("SERIAL STARTED") + len("SERIAL STARTED")
                        self.serial_monitor_text.insert("end", "SERIAL STARTED\n")
                        remaining_data = data[serial_started_index:].strip()
                        if remaining_data:
                            self.serial_monitor_text.insert("end", remaining_data)
                        self.serial_monitor_text.yview("end")
                        self.connect_com_button.configure(fg_color="green")
                        self.connect_com_button.configure(state="disabled")
                        self.send_serial_green()
                        continue

                    # Si se recibe el mensaje RESET, habilitar las opciones de WiFi
                    if "RESET" in data:
                        self.enable_wifi_options()

                    if "ABORT" in data:
                        self.abort_test()

                    # Si se recibe el mensaje TEST-BENCH CONNECTED, cambiar el estado
                    if "TEST-BENCH CONNECTED" in data:
                        self.disable_wifi_options()
                        self.connect_wifi_button.configure(fg_color="green")
                        self.send_wifi_green()
                        self.enable_checklist()

                    # Insertar los datos en el CTkTextbox
                    self.serial_monitor_text.insert("end", data)
                    self.serial_monitor_text.yview("end")  # Desplazar automáticamente hacia abajo

        except (serial.SerialException, OSError) as e:
            # Capturar la excepción y manejarla si el puerto se cierra inesperadamente
            self.serial_monitor_text.insert("end", f"\nError de conexión serial: {e}\n")
            self.serial_monitor_text.yview("end")
        finally:
            self.serial_monitor_text.configure(state="disabled")


















    def send_serial_reset(self):
        self.serial_connection.write(b'RESET\n')

    def send_serial_green(self):
        """Envia el comando para encender el LED Serial en verde."""
        self.serial_connection.write(b'SERIAL_GREEN\n')

    def send_serial_blue(self):
        """Envia el comando para encender el LED Serial en azul."""
        self.serial_connection.write(b'SERIAL_BLUE\n')

    def send_wifi_green(self):
        """Envia el comando para encender el LED WiFi en verde."""
        self.serial_connection.write(b'WIFI_GREEN\n')

    def send_wifi_blue(self):
        """Envia el comando para encender el LED WiFi en azul."""
        self.serial_connection.write(b'WIFI_BLUE\n')

    def connect_wifi(self):
        """Función para conectar a WiFi enviando el comando CONNECT con SSID y contraseña."""
        ssid = self.testBed_SSID_entry.get()
        password = self.testBed_password_entry.get()

        if ssid and password:
            connect_command = f"CONNECT {ssid} {password}\n"
            self.serial_connection.write(connect_command.encode('utf-8'))
            self.serial_monitor_text.insert("end", f"Enviado: {connect_command}")
            self.serial_monitor_text.yview("end")
    
    def com_port_changed(self, event):
        """Llamada cuando cambia el puerto COM seleccionado, para cerrar el puerto serial si está abierto."""
        if self.com_connected and self.serial_connection.is_open:
            try:
                # Bloquear las opciones de WiFi antes de cerrar la conexión
                self.disable_wifi_options()
                self.off_checklist()
                self.disable_checklist()

                # Enviar el comando RESET antes de cerrar la conexión
                self.serial_connection.write(b'RESET\n')
                self.send_serial_blue()
                self.send_wifi_blue()

                # Cerrar la conexión serial
                self.serial_connection.close()  
                self.com_connected = False
                self.wifi_connected = False

                # Disable the connection indicator labels
                # self.connection_indicator_com.configure(state="disabled")
                # self.connection_indicator_wifi.configure(state="disabled")

                # Change button color to indicate disconnection
                self.connect_com_button.configure(fg_color="red")
                self.connect_wifi_button.configure(fg_color="red")

                self.serial_monitor_text.insert("end", "\nConexión serial cerrada.\n")
                self.serial_monitor_text.yview("end")

                # Habilitar el botón de conexión de nuevo
                self.connect_com_button.configure(state="normal")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cerrar la conexión serial: {e}")

                # Ensure buttons show error state
                self.connect_com_button.configure(fg_color="red")
                self.connect_wifi_button.configure(fg_color="red")

                # Disable input fields
                self.connect_com_button.configure(state="enabled")
                self.connect_wifi_button.configure(state="disabled")

                self.testBed_SSID_entry.configure(state="disabled")
                self.testBed_password_entry.configure(state="disabled")