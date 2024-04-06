import tkinter as tk
from tkinter import ttk
from tkinter import LEFT
from tkinter import filedialog
import os
import threading
import time
import pandas as pd
import yaml
import json

from gui.treeview_edit import TreeViewEdit, sort_column
from dataclass import PDF_File
from save_pdf import save_pdf_files
from utils.utils import create_lookup_table


class GUI_NOTENMASTER():
    def __init__(self) -> None:

        # Load yml-file
        with open(os.path.join(os.getcwd(), "instruments.yml"), encoding='utf8') as f:
            self.instruments = yaml.safe_load(f)
            print(json.dumps(self.instruments, indent=2, ensure_ascii=False))
        with open(os.path.join(os.getcwd(), "config.yml"), encoding='utf8') as f:
            self.config = yaml.safe_load(f)
        self.folder_options = self.config["folder_options"]

        # Create lookup-table
        self.lookup_table = create_lookup_table(self.instruments, debugmode=False)
        self.instruments_list = self.instruments.keys()

        # Initiate dataclass
        self.Pdf_File = PDF_File()

        # Erstelle Hauptfenster
        self.root = tk.Tk()
        self.root.title("NotenMaster")

        # Rahmengröße
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(fill="both", expand=True)  # Strecke den Rahmen horizontal und vertikal

        # Button zum Dateiauswählen
        button_select_file = ttk.Button(frame, text="Datei auswählen", command=self.select_file)
        button_select_file.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Eingabefeld für Dateinamen
        label_file = tk.Label(frame, text="Dateiname:")
        label_file.grid(row=0, column=1, padx=5, pady=5)
        self.entry_file = tk.Entry(frame, width=30)
        self.entry_file.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Dropdown-Menü für Optionen
        label_option = tk.Label(frame, text="Option wählen:")
        label_option.grid(row=1, column=0, padx=5, pady=5)
        self.dropdown_var = tk.StringVar(self.root)
        self.dropdown_var.set(self.folder_options[0])  # Standardoption
        max_width = max(len(option) for option in self.folder_options)  # Längste Option
        dropdown_menu = tk.OptionMenu(frame, self.dropdown_var, *self.folder_options)
        dropdown_menu.config(width=max_width + 2, font=("Arial", 10))
        dropdown_menu.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # Leere Zeile für Trennung
        separator = ttk.Separator(frame, orient="horizontal")
        separator.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)

        # Button zum Ausführen des Programms
        button_run = ttk.Button(frame, text="Run", command=self.run_program)
        button_run.grid(row=3, column=0, columnspan=1, padx=5, pady=5, sticky="ew")

        # Stop-Button
        button_stop = ttk.Button(frame, text="Stop", command=self.stop_program)
        button_stop.grid(row=3, column=1, columnspan=1, padx=5, pady=5, sticky="ew")

        # Fortschrittsanzeige
        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", length=300, mode='indeterminate')
        self.progress_bar.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Statusanzeige
        self.status_label = tk.Label(frame, text="")
        self.status_label.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

        # Infofenster
        self.output_text = tk.Text(frame, height=5, width=50, state=tk.DISABLED)
        self.output_text.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")  # Mitwachsen in alle Richtungen

        # Strecke die letzte Zeile des Rahmens vertikal
        frame.grid_rowconfigure(6, weight=1)

        running = False  # Variable zur Verfolgung des Programmzustands
        

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        self.Pdf_File.filepath = filepath
        if filepath:
            self.filename = os.path.basename(filepath)
            self.filename = os.path.splitext(self.filename)[0]  # Entferne Dateierweiterung
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, self.filename)

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
        self.progress_bar.start(10)  # Starte Fortschrittsanzeige für 10 Sekunden
        self.status_label.config(text="Verarbeitung läuft...")
        self.update_info()  # Aktualisiere Infofenster nach Ausführung des Programms
        threading.Thread(target=self.simulate_processing).start()

    def simulate_processing(self):
        global running
        while running:
            time.sleep(1)  # Regelmäßige Überprüfung alle 1 Sekunde
            # Hier kannst du den Code einfügen, der das Programm ausführt
            # Beispiel: process_file(filename, selected_option)
        self.progress_bar.stop()
        self.status_label.config(text="Verarbeitung gestoppt.")
        self.show_results()

    def stop_program(self):
        global running
        running = False

    def show_results(self):
        result_window = tk.Toplevel(self.root)
        result_window.title("Results")

        # Read csv-file into pandas dataframe
        csv_file = os.path.abspath(os.path.join(os.path.dirname( __file__ ), "..", "testdata/table_test.csv"))
        df = pd.read_csv(csv_file)
        df_list = list(df.columns.values)
        df_rset = df.to_numpy().tolist()
        for i, dt in enumerate(df_rset):
            try:
                df_rset[i][2] = int(df_rset[i][2])
                df_rset[i][3] = round(df_rset[i][3],2)
            except:
                continue

        self.treeview = TreeViewEdit(result_window, columns = df_list[1:])
        self.treeview.heading("#0", text="Index", command=lambda: sort_column(self.treeview, "#0", False))
        self.treeview.heading("Instrument", text="Instrument", command=lambda: sort_column(self.treeview, "Instrument", False))
        self.treeview.heading("Stimme", text="Stimme", command=lambda: sort_column(self.treeview, "Stimme", False))
        self.treeview.heading("Genauigkeit", text="Genauigkeit", command=lambda: sort_column(self.treeview, "Genauigkeit", False))

        for i in df_list[1:]:
            self.treeview.column(i,width=100,anchor='c')
            self.treeview.heading(i,text=i)
        for dt in df_rset:
            v=[r for r in dt]
            self.treeview.insert('','end',text=int(v[0]), values=v[1:])
        self.treeview.column(0, anchor=tk.W)

        self.treeview.pack(fill=tk.BOTH, expand=True)

        self.label_info = tk.Label(result_window, text="")
        self.label_info.pack(side="left", padx=10)

        # Button zum Speichern der Ergebnisse
        save_button = ttk.Button(result_window, text="Speichern", command=self.save_results)
        save_button.pack(side="left", padx=180, pady=10)



    def save_results(self):

        # Get current data
        final_df = pd.DataFrame(columns=["page","instrument","stimme"])
        for i,row_id in enumerate(self.treeview.get_children()):
            row = self.treeview.item(row_id)
            page = row["text"]
            instrument, stimme = row["values"][:2]
            final_df.loc[i] = [page,instrument,stimme]
        final_df = final_df.sort_values(by="page",ignore_index=True)

        # Check for spelling errors
        error_flag = False
        for instrument in final_df["instrument"]:
            if instrument in self.instruments_list:
                continue
            else:
                error_flag = True
        
        if error_flag:
            self.label_info.config(text="Spelling errors in instruments!", fg='#f00')
        else:
            self.Pdf_File.save_path = filedialog.askdirectory()

            if self.Pdf_File.save_path == "":
                self.label_info.config(text="Select Folder to save files!", fg='#f00')
            else:
                print(final_df)
                save_pdf_files(self.Pdf_File, self.instruments_list, self.folder_options, final_df)
                self.root.destroy()
    
    def destroy(self):
        self.root.destroy()
        

if __name__ == "__main__":

    GUI = GUI_NOTENMASTER()
    GUI.root.mainloop()
