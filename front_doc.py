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