import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QScrollArea, QFileDialog,
                             QProgressBar, QMessageBox, QSizePolicy, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from process_data import MkvProcessor  # Импорт вашей функции обработки


class Worker(QObject):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, series_path, output_path, audio_data, subtitle_data):
        super().__init__()
        self.series_path = series_path
        self.output_path = output_path
        self.audio_data = audio_data
        self.subtitle_data = subtitle_data
        self.processor = MkvProcessor(self)

    def run(self):
        try:
            self.processor.process_files(
                self.series_path,
                self.output_path,
                self.audio_data,
                self.subtitle_data
            )
        except Exception as e:
            self.status_updated.emit(f"Critical error: {str(e)}")
        finally:
            self.finished.emit()

    def stop(self):
        self.processor.stop()


class MediaTrackWidget(QWidget):
    removed = pyqtSignal(QWidget)

    def __init__(self, translations, parent=None):
        super().__init__(parent)
        self.translations = translations
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(self.translations["path_placeholder"])
        self.browse_btn = QPushButton(self.translations["browse_button"])
        self.browse_btn.clicked.connect(self.browse_directory)

        self.lang_edit = QLineEdit()
        self.lang_edit.setPlaceholderText(self.translations["language_placeholder"])
        self.lang_edit.setFixedWidth(100)

        self.track_edit = QLineEdit()
        self.track_edit.setPlaceholderText(self.translations["track_name_placeholder"])
        self.track_edit.setFixedWidth(150)

        self.remove_btn = QPushButton(self.translations["remove_button"])
        self.remove_btn.setFixedWidth(30)
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_btn)
        layout.addWidget(QLabel(self.translations["language_label"]))
        layout.addWidget(self.lang_edit)
        layout.addWidget(QLabel(self.translations["track_name_label"]))
        layout.addWidget(self.track_edit)
        layout.addWidget(self.remove_btn)

    def browse_directory(self):
        path = QFileDialog.getExistingDirectory(self, self.translations["select_directory"])
        if path:
            self.path_edit.setText(path)

    def get_data(self):
        return {
            "path": self.path_edit.text(),
            "language": self.lang_edit.text(),
            "track_name": self.track_edit.text()
        }

    def update_texts(self, translations):
        self.translations = translations
        self.path_edit.setPlaceholderText(translations["path_placeholder"])
        self.browse_btn.setText(translations["browse_button"])
        self.lang_edit.setPlaceholderText(translations["language_placeholder"])
        self.track_edit.setPlaceholderText(translations["track_name_placeholder"])
        self.layout().itemAt(2).widget().setText(translations["language_label"])
        self.layout().itemAt(4).widget().setText(translations["track_name_label"])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translations = {}
        self.load_translations("Русский")
        self.setup_ui()
        self.audio_widgets = []
        self.subtitle_widgets = []
        self.worker_thread = None

    def load_translations(self, lang):
        if lang == "English":
            from lang_en import TRANSLATIONS
        else:
            from lang_ru import TRANSLATIONS
        self.translations = TRANSLATIONS

    def setup_ui(self):
        self.setWindowTitle(self.translations["window_title"])
        self.setMinimumSize(800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Language selector
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(QLabel("Language:"))
        self.lang_combobox = QComboBox()
        self.lang_combobox.addItems(["English", "Русский"])
        self.lang_combobox.setCurrentText("Русский")
        self.lang_combobox.currentTextChanged.connect(self.change_language)
        top_bar.addWidget(self.lang_combobox)
        main_layout.addLayout(top_bar)

        # Основные поля ввода
        self.setup_path_inputs(main_layout)
        self.setup_media_sections(main_layout)
        self.setup_progress(main_layout)

    def setup_path_inputs(self, layout):
        # Папка сериала
        series_layout = QHBoxLayout()
        self.series_label = QLabel(self.translations["series_folder"])
        series_layout.addWidget(self.series_label)
        self.series_edit = QLineEdit()
        self.series_edit.setPlaceholderText(self.translations["series_folder"])
        self.series_browse = QPushButton(self.translations["browse_button"])
        self.series_browse.clicked.connect(self.browse_series)
        series_layout.addWidget(self.series_edit)
        series_layout.addWidget(self.series_browse)
        layout.addLayout(series_layout)

        # Выходная папка
        output_layout = QHBoxLayout()
        self.output_label = QLabel(self.translations["output_folder"])
        output_layout.addWidget(self.output_label)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(self.translations["output_folder"])
        self.output_browse = QPushButton(self.translations["browse_button"])
        self.output_browse.clicked.connect(self.browse_output)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.output_browse)
        layout.addLayout(output_layout)

    def setup_media_sections(self, layout):
        # Аудио секция
        self.audio_section = self.create_media_section(
            self.translations["audio_tracks"],
            self.translations["add_audio"],
            "audio"  # <- Добавляем третий параметр
        )
        layout.addWidget(self.audio_section)

        # Субтитры
        self.subtitle_section = self.create_media_section(
            self.translations["subtitles"],
            self.translations["add_subtitles"],
            "subtitles"  # <- Добавляем третий параметр
        )
        layout.addWidget(self.subtitle_section)

    def create_media_section(self, title, add_button_text, media_type):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)

        header = QHBoxLayout()
        header.addWidget(QLabel(title))
        add_btn = QPushButton(add_button_text)
        # Передаем media_type вместо title
        add_btn.clicked.connect(lambda: self.add_media_widget(media_type))
        header.addWidget(add_btn)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)

        layout.addWidget(scroll)
        return frame

    def setup_progress(self, layout):
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.confirm_btn = QPushButton(self.translations["start_processing"])
        self.confirm_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.confirm_btn)

    def browse_series(self):
        path = QFileDialog.getExistingDirectory(self, self.translations["select_directory"])
        if path:
            self.series_edit.setText(path)

    def browse_output(self):
        path = QFileDialog.getExistingDirectory(self, self.translations["select_directory"])
        if path:
            self.output_edit.setText(path)

    def add_media_widget(self, media_type):
        widget = MediaTrackWidget(self.translations)
        widget.removed.connect(self.remove_media_widget)

        # Проверяем тип медиа напрямую
        if media_type == "audio":
            self.audio_widgets.append(widget)
            container = self.audio_section
        else:
            self.subtitle_widgets.append(widget)
            container = self.subtitle_section

        container.layout().itemAt(1).widget().widget().layout().insertWidget(
            self.scroll_layout.count()-1, widget
        )

    def remove_media_widget(self, widget):
        if widget in self.audio_widgets:
            self.audio_widgets.remove(widget)
        else:
            self.subtitle_widgets.remove(widget)
        widget.deleteLater()

    def validate_inputs(self):
        errors = []
        if not os.path.isdir(self.series_edit.text()):
            errors.append(self.translations["invalid_series_folder"])
        if not os.path.isdir(self.output_edit.text()):
            errors.append(self.translations["invalid_output_folder"])

        for widget in self.audio_widgets + self.subtitle_widgets:
            data = widget.get_data()
            if not os.path.isdir(data['path']):
                errors.append(f"Invalid path in {widget}")
            if not data['language']:
                errors.append(self.translations["missing_language"].format(widget=widget))

        return errors

    def start_processing(self):
        errors = self.validate_inputs()
        if errors:
            QMessageBox.critical(self, "Error", "\n".join(errors))
            return

        audio_data = [w.get_data() for w in self.audio_widgets]
        subtitle_data = [w.get_data() for w in self.subtitle_widgets]

        self.progress.show()
        self.status_label.setText(self.translations["preparing_processing"])

        self.worker = Worker(
            self.series_edit.text(),
            self.output_edit.text(),
            audio_data,
            subtitle_data
        )

        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker.progress_updated.connect(self.progress.setValue)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def change_language(self, lang_text):
        self.load_translations(lang_text)   
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(self.translations["window_title"])
        self.series_label.setText(self.translations["series_folder"])
        self.output_label.setText(self.translations["output_folder"])
        self.series_edit.setPlaceholderText(self.translations["series_folder"])
        self.output_edit.setPlaceholderText(self.translations["output_folder"])
        self.series_browse.setText(self.translations["browse_button"])
        self.output_browse.setText(self.translations["browse_button"])
        self.confirm_btn.setText(self.translations["start_processing"])
        self.setup_path_inputs
        
        # Update sections
        self.audio_section.layout().itemAt(0).layout().itemAt(0).widget().setText(self.translations["audio_tracks"])
        self.audio_section.layout().itemAt(0).layout().itemAt(1).widget().setText(self.translations["add_audio"])
        self.subtitle_section.layout().itemAt(0).layout().itemAt(0).widget().setText(self.translations["subtitles"])
        self.subtitle_section.layout().itemAt(0).layout().itemAt(1).widget().setText(self.translations["add_subtitles"])
        
        # Update MediaTrackWidgets
        for widget in self.audio_widgets + self.subtitle_widgets:
            widget.update_texts(self.translations)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())