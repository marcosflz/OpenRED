from imports import *
from functions import *

class CFD_Module:
    def __init__(self, content_frame):
        self.content_frame = content_frame

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=10)

        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)   
        self.content_frame.grid_columnconfigure(2, weight=3)   

        self.buttonsFrame = ctk.CTkFrame(self.content_frame, height=10)
        self.buttonsFrame.grid(row=0, column=0, columnspan=3 ,padx=10, pady=10, sticky='nswe')

        self.treeFrame = ctk.CTkScrollableFrame(self.content_frame)
        self.treeFrame.grid(row=1, column=0, padx=10, pady=10, sticky='nswe')

        self.optionsFrame = ctk.CTkScrollableFrame(self.content_frame)
        self.optionsFrame.grid(row=1, column=1, padx=10, pady=10, sticky='nswe')

        self.textboxFrame = ctk.CTkTextbox(self.content_frame)
        self.textboxFrame.grid(row=1, column=2, padx=10, pady=10, sticky='nswe')
