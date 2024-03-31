import tkinter
import tkinter.messagebox
from tkinter import filedialog
import customtkinter

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("NotenMaster")
        self.geometry(f"{900}x{500}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=400, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        # self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="NotenMaster", font=customtkinter.CTkFont(size=20, weight="bold"))
        # self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Select file", command=self.sidebar_button_event_select_file)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=20)
        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_button_event)
        self.sidebar_button_3.grid(row=4, column=0, padx=20, pady=10)
        self.sidebar_entry = customtkinter.CTkEntry(self.sidebar_frame)
        self.sidebar_entry.grid(row=3, column=0, padx=20, pady=10)
        #self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        #self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        # self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
        #                                                                command=self.change_appearance_mode_event)
        # self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))


        # create textbox
        self.infobox = customtkinter.CTkTextbox(self, width=50)
        self.infobox.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")




        self.combobox = customtkinter.CTkComboBox(self.sidebar_frame,
                                            values=["Rot", "Schwarz", "Marsch"],
                                            command=self.combobox_callback)
        self.combobox.grid(row=2, column=0, padx=20, pady=(10, 10))
        #combobox.pack(padx=20, pady=20)
        self.combobox.set("Select folder")  # set initial value



        # create slider and progressbar frame
        self.slider_progressbar_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.slider_progressbar_frame.grid(row=1, column=1, columnspan=2, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.slider_progressbar_frame.grid_columnconfigure(0, weight=1)
        self.slider_progressbar_frame.grid_rowconfigure(4, weight=1)
        self.progressbar_2 = customtkinter.CTkProgressBar(self.sidebar_frame)
        self.progressbar_2.grid(row=4, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        #self.label = customtkinter.CTkLabel(self.slider_progressbar_frame, text="Appearance Mode:", anchor="w")
        #self.label.grid(row=1, column=0, padx=(20, 10), pady=(10, 10))


        # set default values
        #self.sidebar_button_3.configure(state="disabled", text="Run")
        self.sidebar_button_3.configure(text="Run")
        #self.checkbox_2.configure(state="disabled")
        #self.switch_2.configure(state="disabled")
        #self.checkbox_1.select()
        #self.switch_1.select()
        #self.radio_button_3.configure(state="disabled")
        # self.appearance_mode_optionemenu.set("Dark")
        #self.scaling_optionemenu.set("100%")
        #self.optionmenu_1.set("CTkOptionmenu")
        #self.combobox_1.set("CTkComboBox")
        # self.slider_1.configure(command=self.progressbar_2.set)
        # self.slider_2.configure(command=self.progressbar_3.set)
        self.progressbar_2.set(0)
        # self.progressbar_1.configure(mode="indeterminnate")
        # self.progressbar_1.start()
        self.infobox.insert("0.0", "Info\n\n")
        self.infobox.configure(state= "disabled")
        # self.seg_button_1.configure(values=["CTkSegmentedButton", "Value 2", "Value 3"])
        # self.seg_button_1.set("Value 2")

    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    # def change_appearance_mode_event(self, new_appearance_mode: str):
    #     customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def sidebar_button_event(self):
        print("sidebar_button click")
        self.set_info_text("test")

    def sidebar_button_event_select_file(self):
        self.file_path = filedialog.askopenfilename()
        self.set_info_text("Filepath:\n{}".format(self.file_path))
        self.sidebar_entry.insert(-1, self.file_path.split("/")[-1])

    def sidebar_button_event_select_folder(self):
        self.save_dir = filedialog.askdirectory()
        print(self.save_dir)

    def combobox_callback(choice):
        print("combobox dropdown clicked:", choice)

    def set_info_text(self, text):
        self.infobox.configure(state= "normal")
        self.infobox.delete("0.0","end")
        self.infobox.insert("0.0", "Info\n\n" + text)
        self.infobox.configure(state= "disabled")



if __name__ == "__main__":
    app = App()
    app.mainloop()