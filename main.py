import tkinter as tk
from tkinter import ttk, filedialog
import threading
import os  # Import the 'os' module
from process_data import process_data  # Assuming process_data.py exists


class SubtitleAudioGUI(tk.Tk):
    """
    A GUI for adding audio and subtitles to video files.

    This class provides a user interface for selecting a series directory,
    adding multiple audio and subtitle tracks, specifying their languages
    and track names, choosing an output directory, and initiating the
    processing of the files. It uses a scrollable canvas to handle a
    potentially large number of audio/subtitle fields.  Progress and status
    updates are displayed during processing.
    """

    def __init__(self):
        """
        Initializes the main window and creates the UI elements.
        """
        super().__init__()
        self.title("Добавление озвучки и субтитров")
        self.geometry("700x450")
        self.minsize(500, 450)

        self.audio_fields = []
        self.subtitle_fields = []

        self._create_widgets()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def _create_widgets(self):
        """
        Creates all the widgets for the GUI.  Uses a Canvas with a scrollbar
        for the main layout to allow for dynamic addition of audio and subtitle fields.
        """

        # --- Canvas and Scrollbar ---
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Main Frame (inside scrollable_frame) ---
        self.frame = ttk.Frame(self.scrollable_frame, padding="10")
        self.frame.grid(row=0, column=0, sticky="nsew")

        # --- Series Path ---
        ttk.Label(self.frame, text="Выберите папку сериала:").grid(row=0, column=0, sticky="w", pady=(0, 5),
                                                                 columnspan=3)
        self.series_path_entry = ttk.Entry(self.frame, width=40)
        self.series_path_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.series_choose_button = ttk.Button(self.frame, text="Выбрать папку",
                                               command=self.choose_series_directory)
        self.series_choose_button.grid(row=1, column=1, padx=5, pady=5)

        # --- Separator ---
        self.separator1 = ttk.Separator(self.frame, orient='horizontal')
        self.separator1.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)
        self.separator1.grid_remove()

        # --- Audio Section ---
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

        # --- Subtitle Section ---
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

        # --- Output Path ---
        self.output_label = ttk.Label(self.frame, text="Куда положить готовые файлы:")
        self.output_label.grid(row=7, column=0, sticky="w", pady=(10, 5), columnspan=3)
        self.output_label.grid_remove()

        self.output_path_entry = ttk.Entry(self.frame, width=40)
        self.output_path_entry.grid(row=8, column=0, padx=5, pady=5, sticky="ew")
        self.output_path_entry.grid_remove()

        self.output_choose_button = ttk.Button(self.frame, text="Выбрать папку", command=self.choose_output_directory)
        self.output_choose_button.grid(row=8, column=1, padx=5, pady=5)
        self.output_choose_button.grid_remove()

        # --- Confirm Button ---
        self.confirm_button = ttk.Button(self.frame, text="Подтвердить", command=self.confirm)
        self.confirm_button.grid(row=9, column=0, columnspan=3, pady=15)
        self.confirm_button.grid_remove()

        # --- Progress Bar and Status ---
        self.progress_bar = ttk.Progressbar(self.frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=10, column=0, columnspan=3, padx=10, pady=(10, 0), sticky="ew")
        self.progress_bar.grid_remove()

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(row=11, column=0, columnspan=3, pady=(0, 10))
        self.status_label.grid_remove()

        self.scrollable_frame.columnconfigure(0, weight=1)

    def _on_canvas_configure(self, event):
        """
        Updates the scroll region of the canvas to encompass all widgets.
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Adjust canvas window width to match canvas width, prevents horizontal scrollbar
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """
        Handles mousewheel scrolling on the canvas.
        """
        # Normalize wheel delta across different OS
        if event.num == 4:  # Linux scroll up
            delta = -1
        elif event.num == 5:  # Linux scroll down
            delta = 1
        else:  # Windows and macOS
            delta = -1 * (event.delta // 120)
        self.canvas.yview_scroll(delta, "units")

    def choose_series_directory(self):
        """
        Opens a directory selection dialog and updates the series path entry.
        If a directory is chosen, shows additional UI fields.
        """
        directory_path = filedialog.askdirectory()
        if directory_path:
            self.series_path_entry.delete(0, tk.END)
            self.series_path_entry.insert(0, directory_path)
            self.show_additional_fields()

    def choose_output_directory(self):
        """
        Opens a directory selection dialog and updates the output path entry.
        """
        directory_path = filedialog.askdirectory()
        if directory_path:
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, directory_path)

    def show_additional_fields(self):
        """
        Makes the initially hidden UI elements visible.
        """
        for widget in (self.separator1, self.audio_label, self.add_audio_button, self.audio_frame,
                       self.subtitle_label, self.add_subtitle_button, self.subtitle_frame,
                       self.output_label, self.output_path_entry, self.output_choose_button,
                       self.confirm_button, self.progress_bar, self.status_label):
            widget.grid()

    def _add_field(self, parent_frame, field_list, remove_command):
        """
        Adds a new row with fields for audio/subtitle selection, language, and track name.

        Args:
            parent_frame: The frame to which the new row will be added.
            field_list:  The list to which the new field data will be appended.
            remove_command: The function to call when the remove button is pressed.
        """
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
        trackname_label.grid(row=0, column=4, padx=(5, 0), pady=5, sticky="e")

        trackname_var = tk.StringVar()
        trackname_entry = ttk.Entry(row_frame, textvariable=trackname_var, width=15)
        trackname_entry.grid(row=0, column=5, padx=(0, 5), pady=5, sticky="w")

        remove_button = ttk.Button(row_frame, text="-", command=lambda: remove_command(row_frame, field_list))
        remove_button.grid(row=0, column=6, padx=5, pady=5)

        field_list.append((row_frame, entry, choose_button, lang_var, trackname_var))
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_audio_field(self):
        """Adds a new audio field row."""
        self._add_field(self.audio_frame, self.audio_fields, self.remove_audio_field)

    def add_subtitle_field(self):
        """Adds a new subtitle field row."""
        self._add_field(self.subtitle_frame, self.subtitle_fields, self.remove_subtitle_field)

    def choose_directory(self, entry_widget):
        """
        Opens a directory selection dialog and updates the given entry widget.

        Args:
            entry_widget: The Entry widget to update with the selected directory.
        """
        directory_path = filedialog.askdirectory()
        if directory_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, directory_path)

    def _remove_field(self, field_list, row_frame):
        """
        Removes a field row from the UI and updates the field list.

        Args:
            field_list: The list of field data.
            row_frame: The Frame widget representing the row to be removed.
        """
        row_frame.destroy()
        for i, field_data in enumerate(field_list):
            if field_data[0] == row_frame:
                del field_list[i]
                break
        self._update_positions(field_list)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def remove_audio_field(self, row_frame, field_list):
        """Removes the specified audio field row."""
        self._remove_field(field_list, row_frame)

    def remove_subtitle_field(self, row_frame, field_list):
        """Removes the specified subtitle field row."""
        self._remove_field(field_list, row_frame)

    def _update_positions(self, field_list):
        """
        Updates the grid row positions of the remaining fields after a row is removed.

        Args:
            field_list: The list of field data.
        """
        for i, (row_frame, *_) in enumerate(field_list):
            row_frame.grid(row=i, column=0, sticky="ew")

    def update_progress(self, value):
        """
        Updates the progress bar with the given value.

        Args:
            value: The new progress value (0-100).
        """
        self.progress_bar["value"] = value
        self.update_idletasks()  # Important to refresh the GUI

    def update_status(self, text):
        """
        Updates the status label with the given text.

        Args:
            text: The new status text.
        """
        self.status_label["text"] = text

    def confirm(self):
        """
        Collects the user input, validates it, and starts the processing in a separate thread.
        """
        series_path = self.series_path_entry.get().strip()
        output_path = self.output_path_entry.get().strip()

        if not series_path:
            tk.messagebox.showerror("Ошибка", "Выберите папку сериала.")
            return
        if not os.path.isdir(series_path):
            tk.messagebox.showerror("Ошибка", "Указанная папка сериала не существует.")
            return
        if not output_path:
            tk.messagebox.showerror("Ошибка", "Выберите папку для сохранения результатов.")
            return
        if not os.path.isdir(output_path):
            tk.messagebox.showerror("Ошибка", "Указанная папка для сохранения результатов не существует.")
            return

        audio_data = []
        for _, entry, _, lang_var, trackname_var in self.audio_fields:
            audio_path = entry.get().strip()
            audio_lang = lang_var.get().strip()
            audio_trackname = trackname_var.get().strip()

            if not audio_path:
                tk.messagebox.showerror("Ошибка", "Укажите путь для всех аудио дорожек.")
                return
            if not os.path.isdir(audio_path):
                tk.messagebox.showerror("Ошибка", "Указанный путь аудио дорожки не существует.")
                return
            if not audio_lang:
                tk.messagebox.showerror("Ошибка", "Укажите язык для всех аудио дорожек.")
                return
            audio_data.append({
                "path": audio_path,
                "language": audio_lang,
                "track_name": audio_trackname,
            })

        subtitle_data = []
        for _, entry, _, lang_var, trackname_var in self.subtitle_fields:
            sub_path = entry.get().strip()
            sub_lang = lang_var.get().strip()
            sub_trackname = trackname_var.get().strip()

            if not sub_path:
                tk.messagebox.showerror("Ошибка", "Укажите путь для всех дорожек субтитров.")
                return
            if not os.path.isdir(sub_path):
                tk.messagebox.showerror("Ошибка", "Указанный путь дорожки субтитров не существует.")
                return
            if not sub_lang:
                tk.messagebox.showerror("Ошибка", "Укажите язык для всех дорожек субтитров.")
                return
            subtitle_data.append({
                "path": sub_path,
                "language": sub_lang,
                "track_name": sub_trackname,
            })

        # Start processing in a separate thread
        thread = threading.Thread(target=process_data, args=(series_path, output_path, audio_data, subtitle_data, self))
        thread.start()


if __name__ == "__main__":
    gui = SubtitleAudioGUI()
    gui.mainloop()