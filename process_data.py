import os
import subprocess
import platform
import sys
import glob

# Константы для расширений
AUDIO_EXTENSIONS = ['.mka', '.aac', '.mp3', '.ac3', '.dts', '.flac', '.ogg', '.wav']
SUBTITLE_EXTENSIONS = ['.srt', '.ass', '.ssa', '.vtt']

def find_mkvmerge():
    """
    Ищет исполняемый файл mkvmerge.  Сначала ищет bundled версию,
    затем в PATH, затем в стандартных местах установки в Program Files.

    Returns:
        Полный путь к mkvmerge, если найден, иначе None.
    """

    # 1. Проверка bundled mkvmerge (специфично для PyInstaller)
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled_path = os.path.join(sys._MEIPASS, 'mkvtoolnix', 'mkvmerge.exe')  # Путь нужно изменить при необходимости
        if os.path.exists(bundled_path):
            print(f"Using bundled mkvmerge: {bundled_path}")
            return bundled_path

    # 2. Проверка, есть ли mkvmerge в PATH
    try:
        command = 'where' if platform.system() == 'Windows' else 'which'
        result = subprocess.run([command, 'mkvmerge'], capture_output=True, text=True, check=True)
        mkvmerge_path = result.stdout.strip()
        # Дополнительная проверка, что where/which вернул путь к файлу
        if mkvmerge_path and os.path.isfile(mkvmerge_path):
            print(f"Using PATH mkvmerge: {mkvmerge_path}")
            return mkvmerge_path
    except (subprocess.CalledProcessError, OSError):  # Ловим OSError вместо FileNotFoundError
        pass

    # 3. Проверка Program Files (только для Windows)
    if platform.system() == 'Windows':
        program_files = os.path.expandvars("%ProgramFiles%")
        program_files_x86 = os.path.expandvars("%ProgramFiles(x86)%")

        for pf_path in [program_files, program_files_x86]:
             if not pf_path:
                 continue
             for sub_path in ["MKVToolNix", "MKVToolNix GUI"]:
                potential_path = os.path.join(pf_path, sub_path, "mkvmerge.exe")
                if os.path.exists(potential_path):
                    print(f"Using Program Files mkvmerge: {potential_path}")
                    return potential_path

    print("mkvmerge not found.")
    return None



def find_track(base_name, track_dir, extensions):
    """
    Ищет трек (аудио или субтитры) для данного базового имени файла.

    Args:
        base_name: Базовое имя файла (без расширения).
        track_dir: Каталог, в котором искать трек.
        extensions: Список возможных расширений файла.

    Returns:
        Полный путь к файлу трека, если найден, иначе None.
    """
    if not track_dir:  # Добавил проверку на None/""
        return None
    try:
        for ext in extensions:
            # glob.glob() returns a (possibly empty) list, so we use next() with a default value
            track_file = next(iter(glob.glob(os.path.join(track_dir, f"{base_name}{ext}"))), None)
            if track_file:
                return track_file
    except (OSError, PermissionError) as e:
        print(f"Error searching for track in {track_dir}: {e}")
        return None

    return None


def process_data(series_path, output_path, audio_data, subtitle_data, gui_instance=None):
    """
    Объединяет видео, аудио и субтитры, используя mkvmerge.
    """

    mkvmerge_path = find_mkvmerge()
    if not mkvmerge_path:
        error_message = "Error: mkvmerge not found. Make sure it's installed and in your PATH or Program Files, or bundled correctly."
        if gui_instance:
            gui_instance.update_status(error_message)
        print(error_message)
        return

    try:
        video_files = glob.glob(os.path.join(series_path, "*.mkv"))
        if not video_files:
            if gui_instance:
                gui_instance.update_status("No video files found.")
            print("No video files found.") # Добавил вывод в консоль
            return

        total_videos = len(video_files)

        for index, video_file in enumerate(video_files):
            base_name = os.path.splitext(os.path.basename(video_file))[0]
            output_file = os.path.join(output_path, f"{base_name}_merged.mkv")

            command = [mkvmerge_path, '-o', output_file, video_file]

            for audio in audio_data:
                audio_file = find_track(base_name, audio.get('path'), AUDIO_EXTENSIONS)  # Use .get()
                if audio_file:
                    command.extend([
                        '--language', f'0:{audio.get("language")}',
                        '--track-name', f'0:{audio.get("track_name")}',
                        audio_file
                    ])
                else:
                    message = f"Warning: No audio file found for {base_name} in {audio.get('path')}"
                    if gui_instance:
                        gui_instance.update_status(message)
                    print(message)

            for subtitle in subtitle_data:
                subtitle_file = find_track(base_name, subtitle.get('path'), SUBTITLE_EXTENSIONS)  # Use .get()
                if subtitle_file:
                    command.extend([
                        '--language', f'0:{subtitle.get("language")}',
                        '--track-name', f'0:{subtitle.get("track_name")}',
                        subtitle_file
                    ])
                else:
                    message = f"Warning: No subtitle file found for {base_name} in {subtitle.get('path')}"
                    if gui_instance:
                        gui_instance.update_status(message)
                    print(message)


            try:
                if gui_instance:
                    gui_instance.update_status(f"Merging: {base_name}...")

                result = subprocess.run(command, capture_output=True, text=True)  # Используем subprocess.run

                if result.returncode != 0:
                    error_message = f"Error merging {base_name}:\n{result.stderr}"
                    if gui_instance:
                        gui_instance.update_status(error_message)
                    print(error_message)
                else:
                    if gui_instance:
                        gui_instance.update_status(f"Successfully merged: {base_name}")

            except (OSError, PermissionError) as e:  # Более общая обработка ошибок
                error_message = f"Error during mkvmerge execution: {e}"  # Более информативное сообщение
                if gui_instance:
                    gui_instance.update_status(error_message)
                print(error_message)
                return


            if gui_instance:
                progress_percent = (index + 1) / total_videos * 100
                gui_instance.update_progress(progress_percent)

    except (OSError, PermissionError) as e: #Добавил обработку ошибок для поиска видео
        error_message = f"Critical error in process_data: {e}"
        if gui_instance:
            gui_instance.update_status(error_message)
        print(error_message)


    if gui_instance:
        gui_instance.update_status("All files merged!")



# Пример использования (без GUI):
# if __name__ == '__main__':
#     series_path = 'D:/Bacer/Рабочий стол/py-mkvtoolnux-auto/.conda/share/zoneinfo/Atlantic'  # Замените на ваши пути
#     output_path = 'D:/Bacer/Downloads'
#     audio_data = [
#         {'path': 'D:/Bacer/Рабочий стол/py-mkvtoolnux-auto/.conda/share/zoneinfo', 'language': 'ru', 'track_name': 'dsa'}
#     ]
#     subtitle_data = [
#         {'path': 'D:/Bacer/Рабочий стол/py-mkvtoolnux-auto/.conda/share/zoneinfo/Atlantic', 'language': 'ru', 'track_name': 'asd'}
#     ]

#     os.makedirs(output_path, exist_ok=True)
#     process_data(series_path, output_path, audio_data, subtitle_data)