import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import pandas as pd

# Globale Variable zur Verfolgung des Bearbeitungsstatus
editing_row = False

def select_file():
    filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filepath:
        filename = os.path.basename(filepath)
        filename = os.path.splitext(filename)[0]  # Entferne Dateierweiterung
        entry_file.delete(0, tk.END)
        entry_file.insert(0, filename)

def update_info():
    filename = entry_file.get()
    dropdown_selection = dropdown_var.get()
    info_text = f"Datei: {filename} | {dropdown_selection}"
    output_text.config(state=tk.NORMAL)
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, info_text)
    output_text.config(state=tk.DISABLED)

def run_program():
    filename = entry_file.get()
    selected_option = dropdown_var.get()
    process_file(filename, selected_option)
    show_results()

def process_file(filename, selected_option):
    # Hier kannst du den Code einfügen, um das DataFrame aus der Datei zu laden und zu verarbeiten
    # Beispiel: df = pd.read_csv(filename)
    pass

def show_results():
    result_window = tk.Toplevel(root)
    result_window.title("Results")

    # Erstelle eine Tabelle für die Ergebnisse
    tree = ttk.Treeview(result_window, columns=("Instrument", "Stimme", "Genauigkeit"))
    tree.heading("#0", text="Index")
    tree.heading("Instrument", text="Instrument", command=lambda: sort_column(tree, "Instrument", False))
    tree.heading("Stimme", text="Stimme", command=lambda: sort_column(tree, "Stimme", False))
    tree.heading("Genauigkeit", text="Genauigkeit", command=lambda: sort_column(tree, "Genauigkeit", False))

    # Fülle die Tabelle mit Dummy-Daten
    for i in range(10):
        item = tree.insert("", "end", text=str(i+1), values=("Klarinette", i % 3 + 1, "99%"))

    tree.pack(fill="both", expand=True)

    # Ereignisbindung für Zeilenklicks
    tree.bind("<ButtonRelease-1>", lambda event: edit_row(tree, event))

def edit_row(tree, event):
    global editing_row
    if editing_row:
        return  # Verlasse die Funktion, wenn bereits eine Zeile bearbeitet wird

    item = tree.identify("item", event.x, event.y)  # Erhalte das Element unter dem Mauszeiger
    if item and tree.index(item):  # Überprüfe, ob das Element eine Zeile ist und kein Header
        editing_row = True
        values = tree.item(item, "values")
        edit_window = tk.Toplevel(root)
        edit_window.title("Edit Row")

        # Erstelle Eingabefelder für die Bearbeitung der Werte
        instrument_label = tk.Label(edit_window, text="Instrument:")
        instrument_label.grid(row=0, column=0, padx=5, pady=5)
        instrument_entry = tk.Entry(edit_window)
        instrument_entry.grid(row=0, column=1, padx=5, pady=5)
        instrument_entry.insert(0, values[0])

        stimme_label = tk.Label(edit_window, text="Stimme:")
        stimme_label.grid(row=1, column=0, padx=5, pady=5)
        stimme_entry = tk.Entry(edit_window)
        stimme_entry.grid(row=1, column=1, padx=5, pady=5)
        stimme_entry.insert(0, values[1])

        genauigkeit_label = tk.Label(edit_window, text="Genauigkeit:")
        genauigkeit_label.grid(row=2, column=0, padx=5, pady=5)
        genauigkeit_entry = tk.Entry(edit_window)
        genauigkeit_entry.grid(row=2, column=1, padx=5, pady=5)
        genauigkeit_entry.insert(0, values[2])

        def update_row():
            global editing_row
            new_values = (instrument_entry.get(), stimme_entry.get(), genauigkeit_entry.get())
            tree.item(item, values=new_values)
            edit_window.destroy()
            editing_row = False  # Setze den Bearbeitungsstatus zurück

        # Button zum Aktualisieren der Zeile
        update_button = ttk.Button(edit_window, text="Ändern", command=update_row)
        update_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # Ereignisbindung zum Schließen des Bearbeitungsfensters
        edit_window.protocol("WM_DELETE_WINDOW", lambda: cancel_edit(edit_window))

def cancel_edit(edit_window):
    global editing_row
    edit_window.destroy()
    editing_row = False  # Setze den Bearbeitungsstatus zurück

def sort_column(tree, col, reverse):
    if col == "#0":
        # Spezielle Behandlung für die Sortierung nach dem Index
        items = [(int(tree.item(child, "text")), child) for child in tree.get_children()]
        items.sort(reverse=reverse)
        for index, (idx, child) in enumerate(items):
            tree.move(child, "", index)
    else:
        # Standard-Sortierung für andere Spalten
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        data.sort(reverse=reverse)
        for index, (value, child) in enumerate(data):
            tree.move(child, "", index)
    tree.heading(col, command=lambda: sort_column(tree, col, not reverse))

# Erstelle Hauptfenster
root = tk.Tk()
root.title("NotenMaster")

# Rahmengröße
frame = tk.Frame(root, padx=20, pady=20)
frame.pack(fill="both", expand=True)  # Strecke den Rahmen horizontal und vertikal

# Button zum Dateiauswählen
button_select_file = ttk.Button(frame, text="Datei auswählen", command=select_file)
button_select_file.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

# Eingabefeld für Dateinamen
label_file = tk.Label(frame, text="Dateiname:")
label_file.grid(row=0, column=1, padx=5, pady=5)
entry_file = tk.Entry(frame, width=30)
entry_file.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

# Dropdown-Menü für Optionen
label_option = tk.Label(frame, text="Option wählen:")
label_option.grid(row=1, column=0, padx=5, pady=5)
options = ["Rot", "Schwarz", "Marsch"]
dropdown_var = tk.StringVar(root)
dropdown_var.set(options[0])  # Standardoption
dropdown_menu = tk.OptionMenu(frame, dropdown_var, *options)
dropdown_menu.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

# Button zum Ausführen des Programms
button_run = ttk.Button(frame, text="Run", command=run_program)
button_run.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

# Ausgabefenster für Informationen
output_text = tk.Text(frame, height=2, state=tk.DISABLED)
output_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

# Ereignisbindung für die Aktualisierung der Informationen
entry_file.bind("<KeyRelease>", lambda event: update_info())
dropdown_var.trace("w", lambda *args: update_info())

# Starte die GUI
root.mainloop()
