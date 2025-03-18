import os
import subprocess
import platform
import sys
import glob

# Константы для расширений
AUDIO_EXTENSIONS = ['.mka', '.aac', '.mp3', '.ac3', '.dts', '.flac', '.ogg', '.wav']
SUBTITLE_EXTENSIONS = ['.srt', '.ass', '.ssa', '.vtt']

def find_mkvmerge():
    """Ищет исполняемый файл mkvmerge."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled_path = os.path.join(sys._MEIPASS, 'mkvtoolnix', 'mkvmerge.exe')
        if os.path.exists(bundled_path):
            print(f"Using bundled mkvmerge: {bundled_path}")
            return bundled_path

    try:
        command = 'where' if platform.system() == 'Windows' else 'which'
        result = subprocess.run([command, 'mkvmerge'], capture_output=True, text=True, check=True)
        mkvmerge_path = result.stdout.strip()
        if mkvmerge_path and os.path.isfile(mkvmerge_path):
            print(f"Using PATH mkvmerge: {mkvmerge_path}")
            return mkvmerge_path
    except (subprocess.CalledProcessError, OSError):
        pass

    if platform.system() == 'Windows':
        for pf_path in [os.path.expandvars("%ProgramFiles%"), os.path.expandvars("%ProgramFiles(x86)%")]:
            if pf_path:
                for sub_path in ["MKVToolNix", "MKVToolNix GUI"]:
                    potential_path = os.path.join(pf_path, sub_path, "mkvmerge.exe")
                    if os.path.exists(potential_path):
                        print(f"Using Program Files mkvmerge: {potential_path}")
                        return potential_path

    print("mkvmerge not found.")
    return None

def find_track(base_name, track_dir, extensions):
    """
    Ищет трек, который начинается с base_name и заканчивается одним из extensions.

    Args:
        base_name:  Начало имени файла (без расширения, как у .mkv).
        track_dir:  Каталог для поиска.
        extensions: Список допустимых расширений.

    Returns:
        Полный путь к найденному файлу или None.
    """
    if not track_dir or not os.path.isdir(track_dir):
        return None

    base_name_escaped = glob.escape(base_name)

    for ext in extensions:
        pattern = os.path.join(track_dir, f"{base_name_escaped}*{ext}")
        try:
            for file in glob.glob(pattern):  # Iterate through the list
                if os.path.isfile(file):
                   return file
        except OSError as e:
            print(f"Error accessing directory {track_dir}: {e}")
            return None

    return None
def process_data(series_path, output_path, audio_data, subtitle_data, gui_instance=None):
    """Объединяет видео, аудио и субтитры."""
    mkvmerge_path = find_mkvmerge()
    if not mkvmerge_path:
        error_message = "Error: mkvmerge not found."
        if gui_instance:
            gui_instance.update_status(error_message)
        print(error_message)
        return

    try:
        video_files = glob.glob(os.path.join(series_path, "*.mkv"))
        if not video_files:
            error_message = "No video files found."
            if gui_instance:
                gui_instance.update_status(error_message)
            print(error_message)
            return

        total_videos = len(video_files)

        for index, video_file in enumerate(video_files):
            base_name = os.path.splitext(os.path.basename(video_file))[0]
            output_file = os.path.join(output_path, f"{base_name}_merged.mkv")
            command = [mkvmerge_path, '-o', output_file, video_file]

            for audio in audio_data:
                audio_file = find_track(base_name, audio.get('path'), AUDIO_EXTENSIONS)
                if audio_file:
                    command.extend([
                        '--language', f'0:{audio.get("language", "")}',
                        '--track-name', f'0:{audio.get("track_name", "")}',
                        audio_file
                    ])
                else:
                    message = f"Warning: No audio file found for {base_name} in {audio.get('path')}"
                    if gui_instance:
                        gui_instance.update_status(message)
                    print(message)

            for subtitle in subtitle_data:
                subtitle_file = find_track(base_name, subtitle.get('path'), SUBTITLE_EXTENSIONS)
                if subtitle_file:
                    command.extend([
                        '--language', f'0:{subtitle.get("language", "")}',
                        '--track-name', f'0:{subtitle.get("track_name", "")}',
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

                if platform.system() == 'Windows':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE  # Явно указываем скрытие окна
                else:
                    startupinfo = None  # Для других ОС оставляем как есть

                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    error_message = f"Error merging {base_name}:\n{stderr}"
                    if gui_instance:
                        gui_instance.update_status("Error merging:")
                        gui_instance.update_status(stderr)
                    print(error_message)
                else:
                    if gui_instance:
                        gui_instance.update_status(f"Successfully merged: {base_name}")

            except (OSError, subprocess.SubprocessError) as e:
                error_message = f"Error during mkvmerge execution: {e}"
                if gui_instance:
                    gui_instance.update_status(error_message)
                print(error_message)
                return

            if gui_instance:
                progress_percent = (index + 1) / total_videos * 100
                gui_instance.update_progress(progress_percent)

    except (OSError, PermissionError) as e:
        error_message = f"Critical error in process_data: {e}"
        if gui_instance:
            gui_instance.update_status(error_message)
        print(error_message)

    if gui_instance:
        gui_instance.update_status("All files merged!")
# Пример использования (без GUI):
if __name__ == '__main__':
    series_path = 'E:/Steins;Gate Soumei Eichi no Cognitive Computing'  # Замените на ваши пути
    output_path = 'E:/Steins;Gate Soumei Eichi no Cognitive Computing/Output'
    audio_data = [
        {'path': 'E:/Steins;Gate Soumei Eichi no Cognitive Computing/RUS Sound', 'language': 'ru', 'track_name': 'RUS'}
    ]
    subtitle_data = [
        {'path': 'E:/Steins;Gate Soumei Eichi no Cognitive Computing/RUS Sub', 'language': 'ru', 'track_name': 'RUS Sub'}
    ]

    os.makedirs(output_path, exist_ok=True)
    process_data(series_path, output_path, audio_data, subtitle_data)