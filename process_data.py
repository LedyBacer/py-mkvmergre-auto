import os
import subprocess
import time
import platform  # Import the platform module


def find_mkvmerge():
    """
    Searches for the mkvmerge executable.  Prioritizes the system PATH,
    then checks common installation locations in Program Files.

    Returns:
        The full path to mkvmerge if found, otherwise None.
    """

    # 1. Check if mkvmerge is in the PATH
    try:
        # Use 'where' on Windows, 'which' on other platforms
        command = 'where' if platform.system() == 'Windows' else 'which'
        result = subprocess.run([command, 'mkvmerge'], capture_output=True, text=True, check=True)
        mkvmerge_path = result.stdout.strip()
        if mkvmerge_path:  # Check if the command returned a path
            return mkvmerge_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # mkvmerge not found in PATH, continue searching

    # 2. If not in PATH, check Program Files (Windows only)
    if platform.system() == 'Windows':
        program_files_paths = [
            os.environ.get('ProgramFiles'),
            os.environ.get('ProgramFiles(x86)'),
            os.environ.get('ProgramW6432')  # For 64-bit programs on 64-bit Windows
        ]

        for pf_path in program_files_paths:
            if pf_path:  # Check if the environment variable is set
                # Common MKVToolNix installation paths within Program Files
                for sub_path in ["MKVToolNix", "MKVToolNix GUI"]:
                    potential_path = os.path.join(pf_path, sub_path, "mkvmerge.exe")
                    if os.path.exists(potential_path):
                        return potential_path

    return None  # mkvmerge not found


def process_data(series_path, output_path, audio_data, subtitle_data, gui_instance=None):
    """
    Combines video, audio, and subtitle files using mkvmerge.

    Args:
        series_path: Path to the directory containing the video files.
        output_path: Path to the directory where the merged files should be saved.
        audio_data: List of dictionaries, each containing 'path', 'language', and 'track_name' for audio tracks.
        subtitle_data: List of dictionaries, each containing 'path', 'language', and 'track_name' for subtitle tracks.
        gui_instance:  An optional GUI instance for progress updates (if used in a GUI).
    """

    # Find mkvmerge
    mkvmerge_path = find_mkvmerge()
    if not mkvmerge_path:
        if gui_instance:
            gui_instance.update_status("Error: mkvmerge not found.  Make sure it's installed and in your PATH or Program Files.")
        print("Error: mkvmerge not found.  Make sure it's installed and in your PATH or Program Files.")
        return

    try:
        # 1. Find video files
        video_files = [f for f in os.listdir(series_path) if f.endswith('.mkv')]
        if not video_files:
            if gui_instance:
                gui_instance.update_status("No video files found.")
            return

        total_videos = len(video_files)

        for index, video_file in enumerate(video_files):
            base_name = os.path.splitext(video_file)[0]
            video_path = os.path.join(series_path, video_file)
            output_file = os.path.join(output_path, f"{base_name}_merged.mkv")

            # 2. Build the mkvmerge command
            command = [mkvmerge_path, '-o', output_file, video_path]

            # 3. Add audio tracks
            for audio in audio_data:
                audio_dir = audio['path']
                audio_language = audio['language']
                audio_track_name = audio['track_name']

                audio_file = None
                for ext in ['.mka', '.aac', '.mp3', '.ac3', '.dts', '.flac', '.ogg', '.wav']:
                    potential_audio_file = os.path.join(audio_dir, f"{base_name}{ext}")
                    if os.path.exists(potential_audio_file):
                        audio_file = potential_audio_file
                        break

                if audio_file:
                    command.extend(['--language', f'0:{audio_language}', '--track-name', f'0:{audio_track_name}', audio_file])
                else:
                    if gui_instance:
                        gui_instance.update_status(f"Warning: No audio file found for {base_name} in {audio_dir}")

            # 4. Add subtitle tracks
            for subtitle in subtitle_data:
                subtitle_dir = subtitle['path']
                subtitle_language = subtitle['language']
                subtitle_track_name = subtitle['track_name']

                subtitle_file = None
                for ext in ['.srt', '.ass', '.ssa', '.vtt']:
                    potential_subtitle_file = os.path.join(subtitle_dir, f"{base_name}{ext}")
                    if os.path.exists(potential_subtitle_file):
                        subtitle_file = potential_subtitle_file
                        break

                if subtitle_file:
                    command.extend(['--language', f'0:{subtitle_language}', '--track-name', f'0:{subtitle_track_name}', subtitle_file])
                else:
                    if gui_instance:
                        gui_instance.update_status(f"Warning: No subtitle file found for {base_name} in {subtitle_dir}")

            # 5. Execute mkvmerge
            try:
                if gui_instance:
                    gui_instance.update_status(f"Merging: {base_name}...")
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    if gui_instance:
                        gui_instance.update_status(f"Error merging {base_name}:")
                        gui_instance.update_status(stderr)
                    print(f"Error merging {base_name}:\n{stderr}")
                else:
                    if gui_instance:
                        gui_instance.update_status(f"Successfully merged: {base_name}")

            except FileNotFoundError:
                # This should not happen now, as we already checked for mkvmerge
                if gui_instance:
                    gui_instance.update_status("Error: mkvmerge execution failed.")
                print("Error: mkvmerge execution failed.")
                return
            except Exception as e:
                if gui_instance:
                    gui_instance.update_status(f"An unexpected error occurred: {e}")
                print(f"An unexpected error occurred: {e}")
                return

            if gui_instance:
                progress_percent = (index + 1) / total_videos * 100
                gui_instance.update_progress(progress_percent)

    except Exception as e:
        if gui_instance:
            gui_instance.update_status(f"Critical Error Occurred: {e}")
        print(f"Critical error in process_data: {e}")

    if gui_instance:
        gui_instance.update_status("All files merged!")



# Example Usage (without a GUI):
if __name__ == '__main__':
    series_path = 'D:/Bacer/Рабочий стол/py-mkvtoolnux-auto/.conda/share/zoneinfo/Atlantic'
    output_path = 'D:/Bacer/Downloads'
    audio_data = [
        {'path': 'D:/Bacer/Рабочий стол/py-mkvtoolnux-auto/.conda/share/zoneinfo', 'language': 'ru', 'track_name': 'dsa'}
    ]
    subtitle_data = [
        {'path': 'D:/Bacer/Рабочий стол/py-mkvtoolnux-auto/.conda/share/zoneinfo/Atlantic', 'language': 'ru', 'track_name': 'asd'}
    ]

    os.makedirs(output_path, exist_ok=True)
    process_data(series_path, output_path, audio_data, subtitle_data)