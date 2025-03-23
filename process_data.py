import os
import subprocess
import platform
import sys
import glob
import logging
from typing import Optional, List, Dict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы
AUDIO_EXTENSIONS = ['.mka', '.aac', '.mp3', '.ac3', '.dts', '.flac', '.ogg', '.wav']
SUBTITLE_EXTENSIONS = ['.srt', '.ass', '.ssa', '.vtt']


class MkvProcessor:
    def __init__(self, worker=None):
        self.worker = worker
        self._stop_requested = False

    def find_mkvmerge(self) -> Optional[str]:
        """Поиск исполняемого файла mkvmerge с приоритетом для bundled версии."""
        search_paths = []

        # Проверка bundled версии (для PyInstaller)
        if getattr(sys, 'frozen', False):
            bundled_dir = os.path.join(sys._MEIPASS, 'mkvtoolnix')
            exe_name = 'mkvmerge.exe' if platform.system() == 'Windows' else 'mkvmerge'
            bundled_path = os.path.join(bundled_dir, exe_name)
            search_paths.append(bundled_path)

        # Поиск в системном PATH
        search_paths.append('mkvmerge')

        # Windows-specific paths
        if platform.system() == 'Windows':
            for env_var in ["ProgramFiles", "ProgramFiles(x86)"]:
                program_files = os.environ.get(env_var)
                if program_files:
                    search_paths.extend([
                        os.path.join(program_files, "MKVToolNix", "mkvmerge.exe"),
                        os.path.join(program_files, "MKVToolNix GUI", "mkvmerge.exe")
                    ])

        for path in search_paths:
            try:
                if os.path.isfile(path):
                    logger.info(f"Found mkvmerge at: {path}")
                    return path
                result = subprocess.run(
                    [path, '--version'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                )
                if result.returncode == 0:
                    return path
            except (OSError, subprocess.SubprocessError):
                continue

        self._emit_error("mkvmerge not found. Please install MKVToolNix.")
        return None

    def _emit_status(self, message: str):
        if self.worker:
            self.worker.status_updated.emit(message)
        logger.info(message)

    def _emit_progress(self, value: int):
        if self.worker:
            self.worker.progress_updated.emit(value)

    def _emit_error(self, message: str):
        if self.worker:
            self.worker.status_updated.emit(f"Error: {message}")
        logger.error(message)

    def stop(self):
        self._stop_requested = True

    def _find_track(self, base_name: str, track_dir: str, extensions: List[str]) -> Optional[str]:
        """Поиск файла трека с улучшенным экранированием и отладкой."""
        try:
            # Нормализация и проверка пути
            track_dir = os.path.normpath(track_dir)
            if not os.path.exists(track_dir):
                logger.warning(f"Track directory does not exist: {track_dir}")
                return None

            logger.debug(f"Searching track in: {track_dir}")
            logger.debug(f"Base name: {base_name}")
            logger.debug(f"Extensions: {extensions}")

            # Экранирование каждой части пути
            dir_parts = track_dir.split(os.sep)
            escaped_dir = os.sep.join(glob.escape(part) for part in dir_parts)

            # Создание базового паттерна
            base_pattern = f"{glob.escape(base_name)}*"

            # Поиск по всем расширениям
            for ext in extensions:
                full_pattern = os.path.join(escaped_dir, f"{base_pattern}{glob.escape(ext)}")
                logger.debug(f"Trying pattern: {full_pattern}")

                # Поиск с учетом регистра для Windows
                for file in glob.glob(full_pattern, recursive=False):
                    logger.debug(f"Found candidate: {file}")
                    if os.path.isfile(file):
                        logger.info(f"Matched track: {file}")
                        return file

            logger.debug("No matches found")
            return None

        except Exception as e:
            logger.error(f"Error in _find_track: {str(e)}", exc_info=True)
            return None
    
    def _build_mkvmerge_command(self, video_file: str, output_file: str,
                              audio_data: List[Dict], subtitle_data: List[Dict]) -> List[str]:
        """Сборка команды для mkvmerge."""
        command = ['mkvmerge', '-o', output_file, video_file]

        # Добавление аудио дорожек
        for audio in audio_data:
            audio_file = self._find_track(
                os.path.splitext(os.path.basename(video_file))[0],
                audio.get('path'),
                AUDIO_EXTENSIONS
            )
            if audio_file:
                command.extend([
                    '--language', f'0:{audio.get("language", "")}',
                    '--track-name', f'0:{audio.get("track_name", "")}',
                    audio_file
                ])
            else:
                self._emit_status(f"Audio track not found: {audio.get('path')}")

        # Добавление субтитров
        for subtitle in subtitle_data:
            subtitle_file = self._find_track(
                os.path.splitext(os.path.basename(video_file))[0],
                subtitle.get('path'),
                SUBTITLE_EXTENSIONS
            )
            if subtitle_file:
                command.extend([
                    '--language', f'0:{subtitle.get("language", "")}',
                    '--track-name', f'0:{subtitle.get("track_name", "")}',
                    subtitle_file
                ])
            else:
                self._emit_status(f"Subtitle track not found: {subtitle.get('path')}")

        return command

    def process_files(self, series_path: str, output_path: str,
                audio_data: List[Dict], subtitle_data: List[Dict]):
        """Основная функция обработки файлов."""
        try:
            if self._stop_requested:
                return

            # Валидация путей
            for path in [series_path, output_path]:
                if not os.path.isdir(path):
                    self._emit_error(f"Directory not found: {path}")
                    return

            mkvmerge_path = self.find_mkvmerge()
            if not mkvmerge_path:
                return

            # Исправлено: экранирование пути к папке с файлами
            escaped_series_path = glob.escape(series_path)
            video_files = glob.glob(os.path.join(escaped_series_path, "*.mkv"))
            
            if not video_files:
                self._emit_error(f"No MKV files found in input directory. Path:{series_path}")
                return

            total = len(video_files)
            for index, video_file in enumerate(video_files):
                if self._stop_requested:
                    self._emit_status("Processing stopped by user")
                    return

                base_name = os.path.splitext(os.path.basename(video_file))[0]
                output_file = os.path.join(output_path, f"{base_name}_merged.mkv")

                self._emit_status(f"Processing: {base_name}...")

                command = self._build_mkvmerge_command(video_file, output_file, audio_data, subtitle_data)
                command[0] = mkvmerge_path  # Заменяем первый аргумент на полный путь

                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                    )
                    stdout, stderr = process.communicate()

                    if process.returncode != 0:
                        self._emit_error(f"Failed to process {base_name}:\n{stderr}")
                    else:
                        self._emit_status(f"Successfully processed: {base_name}")

                except subprocess.SubprocessError as e:
                    self._emit_error(f"Error processing {base_name}: {str(e)}")

                # Обновление прогресса
                progress = int((index + 1) / total * 100)
                self._emit_progress(progress)

            self._emit_status("All files processed successfully")

        except Exception as e:
            self._emit_error(f"Critical error: {str(e)}")
            raise


# Адаптер для совместимости со старым кодом
def process_data(series_path: str, output_path: str,
               audio_data: List[Dict], subtitle_data: List[Dict],
               worker: Optional[object] = None):
    processor = MkvProcessor(worker)
    processor.process_files(series_path, output_path, audio_data, subtitle_data)