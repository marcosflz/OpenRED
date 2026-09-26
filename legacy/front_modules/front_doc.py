from imports import *
from functions import *


class DocModule:
    def __init__(self, content_frame: ctk.CTkFrame):
        """
        Initializes the Adiabatic Temperature Module.

        Args:
            content_frame (ctk.CTkFrame): The frame in which this module will be displayed.
        """
        self.content_frame = content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self.content_frame, text='Soon')
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
