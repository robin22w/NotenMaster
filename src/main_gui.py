import tkinter as tk
from tkinter import ttk
from tkinter import LEFT
from tkinter import filedialog
import os
import sys
import pandas as pd
import yaml

from dataclass import PDF_File
from save_pdf import save_pdf_files


class GUI_NOTENMASTER():
    """ This class will be executed if the start.bat file starts.
    It is the main script and processes the pdf- and exel-file.
    """
    def __init__(self) -> None:
        """ Initiate the GUI
        """
        # Load config yml-file
        with open(os.path.join(os.getcwd(), "config.yml"), encoding='utf8') as f:
            self.config = yaml.safe_load(f)
        self.folder_options = self.config["folder_options"]
        self.instruments_list = self.config["instruments"]

        # Initiate dataclass
        self.Pdf_File = PDF_File()

        # Erstelle Hauptfenster
        self.root = tk.Tk()
        self.root.title("NotenMaster")

        # Rahmengröße
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)  # Strecke den Rahmen horizontal und vertikal

        # Button zum Dateiauswählen
        button_select_file = ttk.Button(frame, text="PDF-Datei auswählen", command=self.select_file)
        button_select_file.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Eingabefeld für Dateinamen
        label_file = tk.Label(frame, text="Dateiname:")
        label_file.grid(row=0, column=1, padx=5, pady=5)
        self.entry_file = tk.Entry(frame, width=30)
        self.entry_file.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Button zum Dateiauswählen
        button_select_file = ttk.Button(frame, text="Excel-Datei auswählen", command=self.select_excel)
        button_select_file.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        # Eingabefeld für Dateinamen
        self.entry_file_excel = tk.Entry(frame, width=30)
        self.entry_file_excel.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # Dropdown-Menü für Optionen
        label_option = tk.Label(frame, text="Option wählen:")
        label_option.grid(row=2, column=0, padx=5, pady=5)
        self.dropdown_var = tk.StringVar(self.root)
        self.dropdown_var.set(self.folder_options[0])  # Standardoption
        max_width = max(len(option) for option in self.folder_options)  # Längste Option
        dropdown_menu = tk.OptionMenu(frame, self.dropdown_var, *self.folder_options)
        dropdown_menu.config(width=max_width + 2, font=("Arial", 10))
        dropdown_menu.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # Leere Zeile für Trennung
        separator = ttk.Separator(frame, orient="horizontal")
        separator.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        # Button zum Ausführen des Programms
        button_run = ttk.Button(frame, text="Run", command=self.run_program)
        button_run.grid(row=4, column=0, columnspan=1, padx=5, pady=5, sticky="ew")

        # Infofenster
        self.output_text = tk.Text(frame, height=5, width=50, state=tk.DISABLED)
        self.output_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")  # Mitwachsen in alle Richtungen

        # Strecke die letzte Zeile des Rahmens vertikal
        frame.grid_rowconfigure(5, weight=1)

        global running  # Flag to control the processing loop
        running = False

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        self.Pdf_File.filepath = filepath
        if filepath:
            self.filename = os.path.basename(filepath)
            self.filename = os.path.splitext(self.filename)[0]  # Entferne Dateierweiterung
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, self.filename)

    def select_excel(self):
        excelpath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        self.Pdf_File.excelpath = excelpath
        if excelpath:
            self.excelname = os.path.basename(excelpath)
            self.excelname = os.path.splitext(self.excelname)[0]  # Entferne Dateierweiterung
            self.entry_file_excel.config(state="normal")
            self.entry_file_excel.delete(0, tk.END)
            self.entry_file_excel.insert(0, self.excelname)
            self.entry_file_excel.config(state="disabled")

    def update_info(self):
        self.filename = self.entry_file.get()
        dropdown_selection = self.dropdown_var.get()
        info_text = f"Datei: {self.filename} | {dropdown_selection}"
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, info_text)
        self.output_text.config(state=tk.DISABLED)

    def run_program(self):
        global running
        running = True
        self.Pdf_File.filename = self.entry_file.get()
        self.Pdf_File.folder_option = self.dropdown_var.get()

        input_correct, error_message = self.check_inputs()

        if input_correct:
            self.update_info()  # Aktualisiere Infofenster nach Ausführung des Programms

            # Get savedir
            self.Pdf_File.save_path = filedialog.askdirectory()

            # Check if empty
            if self.Pdf_File.save_path == "":
                pass
            else:
                xlsx = pd.ExcelFile(self.Pdf_File.excelpath)
                books = pd.read_excel(xlsx, xlsx.sheet_names[0])

                books = self.preprocess_dataframe(books)

                save_pdf_files(Pdf_File=self.Pdf_File,
                            instruments_list=self.instruments_list,
                            folder_options=self.folder_options,
                            final_df=books)
                
                self.root.destroy()
                sys.exit()
        else:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, error_message)
            self.output_text.config(state=tk.DISABLED)
    
    def preprocess_dataframe(self, df):

        # Filter only for rows with page entries
        filtered_data = df.loc[~df['Seite'].isna()]
        return filtered_data
    
    def check_inputs(self):

        if self.Pdf_File.filepath == "": return (False, "Select Pdf-file!")
        if self.Pdf_File.excelpath == "": return (False, "Select Excel-file!")
        if self.Pdf_File.filename == "": return (False, "Choose filename!")
        return (True, "")
    

if __name__ == "__main__":

    GUI = GUI_NOTENMASTER()
    GUI.root.mainloop()