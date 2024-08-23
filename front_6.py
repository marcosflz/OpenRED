from imports import *
from functions import *

from back_0 import *
from back_1 import *
from back_2 import *
from back_3 import *



class TestingBedModule:
    def __init__(self, content_frame):
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=5)
        self.content_frame.grid_rowconfigure(2, weight=5)

        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=5)
        self.content_frame.grid_columnconfigure(2, weight=5)

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
        self.optionsFrame.grid_propagate(False)

        self.ports_label = ctk.CTkLabel(self.optionsFrame, text="Puerto de Conexión USB:")
        self.ports_label.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')

        self.com_ports = [port.device for port in serial.tools.list_ports.comports()]
    
        if not self.com_ports:  
            self.com_ports = ["No COM ports found"]

        # Connect the com_port_changed method to the OptionMenu's command parameter
        self.com_option_menu = ctk.CTkOptionMenu(self.optionsFrame, values=self.com_ports, command=self.com_port_changed)
        self.com_option_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.connect_com_button = ctk.CTkButton(self.optionsFrame, text="Conectar", command=self.toggle_com_connection)
        self.connect_com_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.com_connected = False

        self.connection_indicator_com = ctk.CTkLabel(self.optionsFrame, text="USB-PORT", fg_color="red", width=10, height=10)
        self.connection_indicator_com.grid(row=0, column=3, padx=5, pady=10, sticky="w")

        self.testBed_SSID_label = ctk.CTkLabel(self.optionsFrame, text="SSID:")
        self.testBed_SSID_label.grid(row=0, column=4, padx=10, pady=10, sticky='nswe') 

        self.testBed_SSID_entry = ctk.CTkEntry(self.optionsFrame)
        self.testBed_SSID_entry.grid(row=0, column=5, padx=10, pady=10, sticky='nswe') 

        self.testBed_password_label = ctk.CTkLabel(self.optionsFrame, text="Password:")
        self.testBed_password_label.grid(row=0, column=6, padx=10, pady=10, sticky='nswe') 

        self.testBed_password_entry = ctk.CTkEntry(self.optionsFrame)
        self.testBed_password_entry.grid(row=0, column=7, padx=10, pady=10, sticky='nswe') 

        self.connect_wifi_button = ctk.CTkButton(self.optionsFrame, text="Conectar", command=self.toggle_wifi_connection)
        self.connect_wifi_button.grid(row=0, column=8, padx=10, pady=10, sticky="e")
        self.wifi_connected = False

        self.connection_indicator_wifi = ctk.CTkLabel(self.optionsFrame, text="TEST-BED", fg_color="red", width=10, height=10)
        self.connection_indicator_wifi.grid(row=0, column=9, padx=5, pady=10, sticky="w")
        
        self.checkListFrame = ctk.CTkFrame(self.content_frame)
        self.checkListFrame.grid(row=1, rowspan=2, column=0, padx=10, pady=10, sticky='nswe')
        self.checkListFrame.grid_propagate(False)





        self.display_1_frame = ctk.CTkFrame(self.content_frame)
        self.display_1_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')
        self.display_1_frame.grid_propagate(False)
        self.display_1_frame.grid_rowconfigure(0, weight=1)
        self.display_1_frame.grid_columnconfigure(0, weight=1)

        # Create a text box for displaying serial monitor output
        self.serial_monitor_text = ctk.CTkTextbox(self.display_1_frame)
        self.serial_monitor_text.grid(row=0, column=0, padx=10, pady=10, sticky='nswe')
        self.serial_monitor_text.configure(state="disabled")  # Initially disabled





        self.display_2_frame = ctk.CTkFrame(self.content_frame)
        self.display_2_frame.grid(row=1, column=2, padx=10, pady=10, sticky='nswe')
        self.display_2_frame.grid_propagate(False)

        self.display_3_frame = ctk.CTkFrame(self.content_frame)
        self.display_3_frame.grid(row=2, column=1, padx=10, pady=10, sticky='nswe')
        self.display_3_frame.grid_propagate(False)

        self.display_4_frame = ctk.CTkFrame(self.content_frame)
        self.display_4_frame.grid(row=2, column=2, padx=10, pady=10, sticky='nswe')
        self.display_4_frame.grid_propagate(False)

        # Crear el checklist en checkListFrame
        self.create_checklist()

        # Deshabilitar el checklist y los widgets de optionsFrame inicialmente
        self.disable_checklist()
        self.disable_options()

        # Iniciar el hilo de monitoreo de puertos
        self.monitor_thread = threading.Thread(target=self.monitor_ports, daemon=True)
        self.monitor_thread.start()











    def toggle_com_connection(self):
        """Toggle the connection status for the USB (COM) port."""
        if self.com_connected:
            # Disconnect logic for COM port
            self.connect_com_button.configure(text="Conectar")
            self.connection_indicator_com.configure(fg_color="red")
            self.com_connected = False
            
            # Disable IP-related widgets when COM is disconnected
            self.testBed_SSID_label.configure(state="normal")
            self.testBed_SSID_entry.configure(state="normal")

            self.testBed_password_label.configure(state="normal")
            self.testBed_password_entry.configure(state="normal")

            self.connect_wifi_button.configure(state="normal")
            
            # Stop reading from the serial port and disconnect it
            if self.serial_thread and self.serial_thread.is_alive():
                self.serial_running = False
                self.serial_thread.join()  # Wait for the thread to finish
                
            # Disconnect the IP connection if it was connected
            if self.wifi_connected:
                self.toggle_wifi_connection()
        else:
            # Connect logic for COM port
            self.connect_com_button.configure(text="Desconectar")
            self.connection_indicator_com.configure(fg_color="green")
            self.com_connected = True
            
            # Enable IP-related widgets when COM is connected
            self.testBed_SSID_label.configure(state="normal")
            self.testBed_SSID_entry.configure(state="normal")

            self.testBed_password_label.configure(state="normal")
            self.testBed_password_entry.configure(state="normal")

            self.connect_wifi_button.configure(state="normal")
            
            # Start reading from the serial port
            self.start_serial_monitor()

    def start_serial_monitor(self):
        """Start a thread to read from the serial port and display the output."""
        self.serial_running = True
        self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.serial_thread.start()

    def read_serial(self):
        """Read from the serial port and display the output in the text box."""
        try:
            # Assuming serial is already imported and serial.Serial is available
            with serial.Serial(self.com_option_menu.get(), 115200, timeout=1) as ser:
                while self.serial_running:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8', errors='replace').strip()
                        if line:
                            self.serial_monitor_text.configure(state="normal")
                            self.serial_monitor_text.insert("end", line + "\n")
                            self.serial_monitor_text.see("end")  # Scroll to the end
                            self.serial_monitor_text.configure(state="disabled")
        except Exception as e:
            self.serial_monitor_text.configure(state="normal")
            self.serial_monitor_text.insert("end", f"Error: {str(e)}\n")
            self.serial_monitor_text.configure(state="disabled")
        finally:
            if ser.is_open:
                ser.close()

    def com_port_changed(self, selected_port):
        """Handle changes to the COM port selection."""
        # If the COM port changes, reset the COM connection and indicator
        self.com_connected = False
        self.connection_indicator_com.configure(fg_color="red")
        self.connect_com_button.configure(text="Conectar")
        
        # Disable IP-related widgets if COM port changes
        self.testBed_SSID_label.configure(state="disabled")
        self.testBed_SSID_entry.configure(state="disabled")

        self.testBed_password_label.configure(state="disabled")
        self.testBed_password_entry.configure(state="disabled")

        self.connect_wifi_button.configure(state="disabled")
        
        # Disconnect the IP connection if it was connected
        if self.wifi_connected:
            self.toggle_wifi_connection()











    def toggle_wifi_connection(self):
        """Toggle the connection status for the IP."""
        if self.wifi_connected:
            # Disconnect logic for IP connection
            self.connect_wifi_button.configure(text="Conectar")
            self.connection_indicator_wifi.configure(fg_color="red")
            self.wifi_connected = False

            # Enviar comando de desconexión al ESP32 Slave
            self.send_serial_command("DISCONNECT")

            # Disable the checklist when IP is disconnected
            self.disable_checklist()

            # Reset the checklist (deselect all checkboxes)
            self.reset_checklist()

        else:
            # Get the IP from the entry widget
            ssid = self.testBed_SSID_entry.get()
            password = self.testBed_password_entry.get()
            # Enviar la IP al ESP32 Slave para que intente conectarse al banco de ensayos
            self.send_serial_command(f"CONNECT {ssid} {password}")

            # Connect logic for IP connection
            self.connect_wifi_button.configure(text="Desconectar")
            self.connection_indicator_wifi.configure(fg_color="green")
            self.wifi_connected = True

            # Enable the checklist when IP is connected
            self.enable_checklist()



    def send_serial_command(self, command):
        """Enviar un comando al ESP32 conectado por USB."""
        try:
            if not hasattr(self, 'ser') or not self.ser.is_open:
                self.ser = serial.Serial(self.com_option_menu.get(), 115200, timeout=1)
            
            self.ser.write(f"{command}\n".encode('utf-8'))
            self.serial_monitor_text.configure(state="normal")
            self.serial_monitor_text.insert("end", f"Enviado: {command}\n")
            self.serial_monitor_text.see("end")  # Scroll to the end
            self.serial_monitor_text.configure(state="disabled")
        except Exception as e:
            self.serial_monitor_text.configure(state="normal")
            self.serial_monitor_text.insert("end", f"Error al enviar comando: {str(e)}\n")
            self.serial_monitor_text.configure(state="disabled")










    def reset_checklist(self):
        """Deselect all checkboxes in the checklist."""
        for checkbox in self.checkboxes:
            checkbox.deselect()  # Uncheck each checkbox

    def create_checklist(self):
        # Configurar columnas para alineación
        self.checkListFrame.grid_columnconfigure(0, weight=1)  # Columna para labels
        self.checkListFrame.grid_columnconfigure(1, weight=1)  # Columna para checkboxes

        # Lista de textos para los labels
        label_texts = ["Option 1", "Option 2", "Option 3", "Option 4"]

        # Crear listas para guardar los labels y checkboxes
        self.labels = []
        self.checkboxes = []

        # Crear labels y checkboxes usando un for loop
        for i, text in enumerate(label_texts):
            label = ctk.CTkLabel(self.checkListFrame, text=text)
            checkbox = ctk.CTkCheckBox(self.checkListFrame, text="")

            # Posicionar label y checkbox
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            checkbox.grid(row=i, column=1, padx=10, pady=5, sticky="e")

            # Añadir a las listas
            self.labels.append(label)
            self.checkboxes.append(checkbox)

    def disable_checklist(self):
        # Deshabilitar todos los checkboxes y oscurecer los labels
        for label, checkbox in zip(self.labels, self.checkboxes):
            label.configure(text_color="gray")  # Oscurecer el texto del label
            checkbox.configure(state="disabled", fg_color="gray")  # Deshabilitar y cambiar el color del checkbox

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
        self.connection_indicator_com.configure(state="disabled")
        self.connection_indicator_wifi.configure(state="disabled")

    def run_test(self):
        # Abrir cuadro de diálogo para guardar archivo
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo",
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        )
        
        if file_path:  # Si el usuario no cancela el cuadro de diálogo
            # Crear archivo vacío o realizar otras acciones con el archivo
            with open(file_path, 'w') as file:
                file.write("")

            # Habilitar el checklist y los widgets de optionsFrame
            #self.enable_checklist()
            
            self.ports_label.configure(state="normal")
            self.com_option_menu.configure(state="normal")
            self.connect_com_button.configure(state="normal")

            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "Archivo creado y checklist habilitado.")

    def monitor_ports(self):
        """Monitorea continuamente los puertos COM y actualiza el OptionMenu si hay cambios."""
        previous_ports = self.com_ports
        while True:
            current_ports = [port.device for port in serial.tools.list_ports.comports()]
            if current_ports != previous_ports:
                self.com_ports = current_ports
                if not self.com_ports:
                    self.com_ports = ["No COM ports found"]
                self.com_option_menu.configure(values=self.com_ports)
                previous_ports = current_ports
                
                # Reset connection indicator if ports change
                self.com_port_changed(None)
                
            time.sleep(1)  # Monitorea cada segundo