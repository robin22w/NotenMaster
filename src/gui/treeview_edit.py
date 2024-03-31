import tkinter as tk
from tkinter import ttk
import pandas as pd
import os


class TreeViewEdit(ttk.Treeview):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        self.bind("<Double-1>", self.on_double_click)
        self.result_window = master

    def on_double_click(self, event):  # event contains the x,y coordinates of the mouse click
        
        # Identify the region that was double-clicked
        region_clicked = self.identify_region(event.x, event.y)  # heading, tree, cell
        
        # We're only interested in tree and cell
        if region_clicked not in ("tree", "cell"):
            return
        
        # Which item was double-clicked?
        column = self.identify_column(event.x)

        # "#0" will become -1
        column_index = int(column[1:]) - 1

        # For example #001
        selected_iid = self.focus()

        # This will contain both text and values
        selected_values = self.item(selected_iid)

        if column == "#0":
            selected_text = selected_values.get("text")
        else:
            selected_text = selected_values.get("values")[column_index]

        column_box = self.bbox(selected_iid, column)

        entry_edit = ttk.Entry(self.result_window, width=column_box[2])

        # Record the column index and item iid
        entry_edit.editing_column_index = column_index
        entry_edit.editing_item_iid = selected_iid

        entry_edit.insert(0, selected_text)
        entry_edit.select_range(0, tk.END)

        entry_edit.focus()

        entry_edit.bind("<FocusOut>", self.on_focus_out)
        entry_edit.bind("<Return>", self.on_enter_pressed)


        entry_edit.place(x=column_box[0],
                         y=column_box[1], 
                         w=column_box[2],
                         h=column_box[3])  # place instead of pack

    def on_enter_pressed(self, event):
        new_text = event.widget.get()

        # Such as I002
        selected_iid = event.widget.editing_item_iid

        # Such as -1 (tree column), 0 (first self-defined column), etc.
        column_index = event.widget.editing_column_index

        if column_index == -1:
            self.item(selected_iid, text=new_text)
        else:
            current_values = self.item(selected_iid).get("values")
            current_values[column_index] = new_text
            self.item(selected_iid, values=current_values)

        event.widget.destroy()
    
    def on_focus_out(self, event):
        event.widget.destroy()  # destroy entry widget if clicking outside
    
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


if __name__ == "__main__":

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

    root = tk.Tk()
    result_window = tk.Toplevel(root)
    result_window.title("Results")

    treeview = TreeViewEdit(result_window, columns = df_list[1:])
    treeview.heading("#0", text="Index", command=lambda: sort_column(treeview, "#0", False))
    treeview.heading("Instrument", text="Instrument", command=lambda: sort_column(treeview, "Instrument", False))
    treeview.heading("Stimme", text="Stimme", command=lambda: sort_column(treeview, "Stimme", False))
    treeview.heading("Genauigkeit", text="Genauigkeit", command=lambda: sort_column(treeview, "Genauigkeit", False))

    for i in df_list[1:]:
        treeview.column(i,width=100,anchor='c')
        treeview.heading(i,text=i)
    for dt in df_rset:
        v=[r for r in dt]
        treeview.insert('','end',text=int(v[0]), values=v[1:])
    treeview.column(0, anchor=tk.W)

    treeview.pack(fill=tk.BOTH, expand=True)

    root.mainloop()