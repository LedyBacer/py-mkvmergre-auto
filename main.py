import tkinter as tk
from tkinter import ttk, filedialog
from lang_options import lang_options  # Keep this for validation if needed
import time
import threading  # Import threading
from process_data import process_data


class SubtitleAudioGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Добавление озвучки и субтитров")
        self.geometry("700x450")  # Increased height for progress bar
        self.minsize(500, 450)  # Increased min height

        self.audio_fields = []
        self.subtitle_fields = []

        self._create_widgets()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def _create_widgets(self):
        # --- Canvas и Scrollbar ---
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Остальной интерфейс (внутри scrollable_frame) ---
        self.frame = ttk.Frame(self.scrollable_frame, padding="10")
        self.frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(self.frame, text="Выберите папку сериала:").grid(row=0, column=0, sticky="w", pady=(0, 5), columnspan=3)

        self.series_path_entry = ttk.Entry(self.frame, width=40)
        self.series_path_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.series_choose_button = ttk.Button(self.frame, text="Выбрать папку", command=self.choose_series_directory)
        self.series_choose_button.grid(row=1, column=1, padx=5, pady=5)

        self.separator1 = ttk.Separator(self.frame, orient='horizontal')
        self.separator1.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)
        self.separator1.grid_remove()

        self.audio_label = ttk.Label(self.frame, text="Добавить озвучку")
        self.audio_label.grid(row=3, column=0, sticky="w", pady=(0, 5), columnspan=2)
        self.audio_label.grid_remove()

        self.add_audio_button = ttk.Button(self.frame, text="+", command=self.add_audio_field)
        self.add_audio_button.grid(row=3, column=2, sticky="e")
        self.add_audio_button.grid_remove()

        self.audio_frame = ttk.Frame(self.frame, borderwidth=2, relief="groove", padding=5)
        self.audio_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5)
        self.audio_frame.grid_remove()
        self.audio_frame.columnconfigure(0, weight=1)

        self.subtitle_label = ttk.Label(self.frame, text="Добавить субтитры")
        self.subtitle_label.grid(row=5, column=0, sticky="w", pady=(0, 5), columnspan=2)
        self.subtitle_label.grid_remove()

        self.add_subtitle_button = ttk.Button(self.frame, text="+", command=self.add_subtitle_field)
        self.add_subtitle_button.grid(row=5, column=2, sticky="e")
        self.add_subtitle_button.grid_remove()

        self.subtitle_frame = ttk.Frame(self.frame, borderwidth=2, relief="groove", padding=5)
        self.subtitle_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5)
        self.subtitle_frame.grid_remove()
        self.subtitle_frame.columnconfigure(0, weight=1)

        # --- "Куда положить готовые файлы" ---
        self.output_label = ttk.Label(self.frame, text="Куда положить готовые файлы:")
        self.output_label.grid(row=7, column=0, sticky="w", pady=(10, 5), columnspan=3)
        self.output_label.grid_remove()

        self.output_path_entry = ttk.Entry(self.frame, width=40)
        self.output_path_entry.grid(row=8, column=0, padx=5, pady=5, sticky="ew")
        self.output_path_entry.grid_remove()

        self.output_choose_button = ttk.Button(self.frame, text="Выбрать папку", command=self.choose_output_directory)
        self.output_choose_button.grid(row=8, column=1, padx=5, pady=5)
        self.output_choose_button.grid_remove()

        # --- Кнопка "Подтвердить" ---
        self.confirm_button = ttk.Button(self.frame, text="Подтвердить", command=self.confirm)
        self.confirm_button.grid(row=9, column=0, columnspan=3, pady=15)
        self.confirm_button.grid_remove()

        # --- Progress Bar and Status ---
        self.progress_bar = ttk.Progressbar(self.frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=10, column=0, columnspan=3, padx=10, pady=(10, 0), sticky="ew")
        self.progress_bar.grid_remove() # Hide initially

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(row=11, column=0, columnspan=3, pady=(0, 10))
        self.status_label.grid_remove() # Hide initially


        self.scrollable_frame.columnconfigure(0, weight=1)


    def _on_mousewheel(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 * (event.delta // 120)
        self.canvas.yview_scroll(delta, "units")

    def choose_series_directory(self):
        directory_path = filedialog.askdirectory()
        if directory_path:
            self.series_path_entry.delete(0, tk.END)
            self.series_path_entry.insert(0, directory_path)
            self.show_additional_fields()

    def choose_output_directory(self):
        directory_path = filedialog.askdirectory()
        if directory_path:
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, directory_path)

    def show_additional_fields(self):
        for widget in (self.separator1, self.audio_label, self.add_audio_button, self.audio_frame,
                       self.subtitle_label, self.add_subtitle_button, self.subtitle_frame,
                       self.output_label, self.output_path_entry, self.output_choose_button,
                       self.confirm_button, self.progress_bar, self.status_label):  # Added progress and status
            widget.grid()

    def _add_field(self, parent_frame, field_list, remove_command, is_audio=False):
        row = len(field_list)
        row_frame = ttk.Frame(parent_frame)
        row_frame.grid(row=row, column=0, sticky="ew", columnspan=4)
        row_frame.columnconfigure(0, weight=1)
        entry = ttk.Entry(row_frame, width=30)
        entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        choose_button = ttk.Button(row_frame, text="Выбрать папку", command=lambda: self.choose_directory(entry))
        choose_button.grid(row=0, column=1, padx=5, pady=5)
        lang_label = ttk.Label(row_frame, text="Язык:")
        lang_label.grid(row=0, column=2, padx=(5, 0), pady=5, sticky="e")
        lang_var = tk.StringVar(value="ru")
        lang_entry = ttk.Entry(row_frame, textvariable=lang_var, width=5)
        lang_entry.grid(row=0, column=3, padx=(0, 5), pady=5, sticky="w")
        trackname_label = ttk.Label(row_frame, text="Название:")
        trackname_label.grid(row=0, column=4, padx=(5,0), pady=5, sticky="e")
        trackname_var = tk.StringVar()
        trackname_entry = ttk.Entry(row_frame, textvariable=trackname_var, width=15)
        trackname_entry.grid(row=0, column=5, padx=(0, 5), pady=5, sticky="w")
        remove_button = ttk.Button(row_frame, text="-", command=lambda: remove_command(row_frame, field_list))
        remove_button.grid(row=0, column=6, padx=5, pady=5)
        field_list.append((row_frame, entry, choose_button, lang_var, trackname_var))
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_audio_field(self):
        self._add_field(self.audio_frame, self.audio_fields, self.remove_audio_field, is_audio=True)

    def add_subtitle_field(self):
         self._add_field(self.subtitle_frame, self.subtitle_fields, self.remove_subtitle_field)

    def choose_directory(self, entry_widget):
        directory_path = filedialog.askdirectory()
        if directory_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, directory_path)

    def _remove_field(self, field_list, row_frame, *args):
        row_frame.destroy()
        for i, field_data in enumerate(field_list):
            if field_data[0] == row_frame:
                del field_list[i]
                break
        self._update_positions(field_list)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def remove_audio_field(self, row_frame, field_list):
        self._remove_field(field_list, row_frame)

    def remove_subtitle_field(self, row_frame, field_list):
        self._remove_field(field_list, row_frame)

    def _update_positions(self, field_list):
        for i, (row_frame, *_) in enumerate(field_list):
            row_frame.grid(row=i, column=0, sticky="ew")

    def update_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar["value"] = value
        self.update_idletasks()  # Important to refresh the GUI

    def update_status(self, text):
        """Updates the status label."""
        self.status_label["text"] = text

    def confirm(self):
        series_path = self.series_path_entry.get()
        output_path = self.output_path_entry.get()
        audio_data = []
        for _, entry, _, lang_var, trackname_var in self.audio_fields:
            audio_data.append({
                "path": entry.get(),
                "language": lang_var.get(),
                "track_name": trackname_var.get()
            })
        subtitle_data = []
        for _, entry, _, lang_var, trackname_var in self.subtitle_fields:
            subtitle_data.append({
                "path": entry.get(),
                "language": lang_var.get(),
                "track_name": trackname_var.get()
            })

        # Start processing in a separate thread
        thread = threading.Thread(target=process_data, args=(series_path, output_path, audio_data, subtitle_data, self))
        thread.start()



# def process_data(series_path, output_path, audio_data, subtitle_data, gui_instance):
#     """Example processing function with progress updates."""
#     total_steps = 5  # Simulate 5 seconds of work
#     for i in range(total_steps):
#         time.sleep(1)  # Simulate work
#         progress_percent = (i + 1) / total_steps * 100
#         gui_instance.update_progress(progress_percent)
#         gui_instance.update_status(f"Обработка... {progress_percent:.0f}%")

#     gui_instance.update_status("Готово!")

if __name__ == "__main__":
    gui = SubtitleAudioGUI()
    gui.mainloop()