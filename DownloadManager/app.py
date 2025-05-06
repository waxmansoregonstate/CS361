#python -m PyInstaller --onefile --add-binary "ffmpeg/bin/ffmpeg.exe;ffmpeg/bin" app.py
#python -m PyInstaller --onefile --noconsole --add-binary "ffmpeg/bin/ffmpeg.exe;ffmpeg/bin" app.py

import os
import sys
import yt_dlp
from yt_dlp.utils import download_range_func
import subprocess
import tkinter as tk
import tkinter.filedialog as fd

CONFIG_FILE = "config.txt"

vid_options = [
    "mp4",
    "mov",
    "avi"
]
aud_options = [
    "mp3",
    "wav"
]

ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg", "bin", "ffmpeg.exe")
if not os.path.exists(ffmpeg_path):
    raise FileNotFoundError(f"FFmpeg not found at {ffmpeg_path}")
subprocess.run([ffmpeg_path, "-version"], check=True)

def getOptions(url, output_filename, file_location, start_time, end_time, format_error=False):
    if start_time:
        start_time = get_sec(start_time)
    if end_time:
        end_time = get_sec(end_time)

    ydl_opts = {
        'outtmpl': fr'{file_location}{output_filename}',
        'quiet': True,
        'preferedformat': f'{output_filename.split('.', 1)[1]}'
    }

    # Handle partial downloads
    if "youtube" in url.lower() and (start_time is not None or end_time is not None):
        ydl_opts['download_ranges'] = download_range_func(None, [(start_time or 0, end_time or float('inf'))])
        ydl_opts['force_keyframes_at_cuts'] = True


    # Only set format if not in fallback mode
    if not format_error:
        ext = os.path.splitext(output_filename)[1].lower().lstrip('.')
        if ext in aud_options:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ext,
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = 'best'

    return ydl_opts


def download_video(url, output_filename, file_location, start_time=None, end_time=None):
    if not file_location[-1] == "\\":
        file_location = file_location + "\\"
    ydl_opts = getOptions(url, output_filename, file_location, start_time, end_time)
    print(ydl_opts)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            return "successfully downloaded"
        except Exception as e:
            print(ydl_opts)
            print(f"Error downloading video: {e}")
            ydl_opts = getOptions(url, output_filename, file_location, start_time, end_time, True)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                    return "successfully downloaded"
                except Exception as e:
                    print(ydl_opts)
                    print(f"Error downloading video: {e}")
                    return e
#            sys.exit(1)

def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h)*3600+int(m)*60+int(s)

def save_path(path):
    with open(CONFIG_FILE, 'w') as file:
        file.write(path)

def load_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return file.read().strip()
    return ""

def main():
    def check_site():
        print(f"url changed to: {url.get()}")
        if "youtube.com" in url.get() or "youtu.be" in url.get():
            bounds_block.grid(row=3,column=0)
            gui.configure(background="red")
        elif "instagram.com" in url.get():
            bounds_block.grid_forget()
            gui.configure(background="purple")      
        elif "twitter.com" in url.get() or "x.com" in url.get():
            bounds_block.grid_forget()
            gui.configure(background="cyan")            
        else:
            bounds_block.grid_forget()
            gui.configure(background="black")

    def change_output_type(str):
        if str == "Video":
            file_types = tk.OptionMenu(frame_2, file_type, *vid_options)
            file_type.set("mp4")
            file_types.grid(row=1, column=1, padx=5, pady=(0,10), sticky="S")
        if str == "Audio":
            file_types = tk.OptionMenu(frame_2, file_type, *aud_options)
            file_type.set("mp3")
            file_types.grid(row=1, column=1, padx=5, pady=(0,10), sticky="S")

    def browse_folder():
        selected_path = fd.askdirectory()
        if selected_path:
            file_location.set(selected_path)
    
    gui = tk.Tk()
    gui.configure(background="black")
    gui.title("download script")
    gui.geometry("640x360")

    frame = tk.Frame(gui)
    frame.pack(fill="both", expand=True, pady=10, padx=10, anchor=tk.CENTER)

    frame_2 = tk.Frame(frame)
    frame_2.pack(fill="both", expand=True, anchor=tk.CENTER)
    frame_2.config(background="")

    frame_2.columnconfigure(0, weight=1)
    frame_2.columnconfigure(1, weight=0)

    #url prompt
    block1 = tk.Frame(frame_2)
    block1.columnconfigure(0, weight=1)
    url = tk.StringVar()
    url.trace_add("write", lambda *args: check_site())
    url_field = tk.Entry(block1, textvariable=url, justify=tk.CENTER)

    tk.Label(block1, text="URL: ").grid(row=0, column=0, sticky="W")
    url_field.grid(row=1, column=0, sticky="EW")
    block1.grid(row=0, column=0, padx=5, pady=10, sticky="EW")

    #file name / type prompt
    block2 = tk.Frame(frame_2)
    block2.columnconfigure(0, weight=1)
    block2.columnconfigure((1,2), weight=0)
    output_filename = tk.StringVar()
    file_name_field = tk.Entry(block2, textvariable=output_filename, justify=tk.CENTER, font=(0, 18))
    file_type = tk.StringVar()

    tk.Label(block2, text="Output File Name: ").grid(row=0, column=0, sticky="W")
    file_name_field.grid(row=1, column=0, sticky="EW", columnspan=3)
    block2.grid(row=1, column=0, padx=5, pady=(0,10), sticky="EW")

    files_used = tk.IntVar(value=0)
    video_button = tk.Radiobutton(block2, text="Video", variable = files_used, value=0, command = lambda : change_output_type("Video")) 
    audio_button = tk.Radiobutton(block2, text="Audio", variable = files_used, value=1, command = lambda : change_output_type("Audio"))
    video_button.grid(row=0, column=1)
    audio_button.grid(row=0, column=2)
    file_types = tk.OptionMenu(frame_2, file_type, *vid_options)
    file_type.set("mp4")
    file_types.grid(row=1, column=1, padx=5, pady=(0,10), sticky="S")

    #path prompt
    block3 = tk.Frame(frame_2)
    block3.columnconfigure(0, weight=1)
    file_location = tk.StringVar()
    file_location.set(load_path())
    file_location_field = tk.Entry(block3, textvariable=file_location, justify=tk.CENTER)

    tk.Label(block3, text="Output File Location: ").grid(row=4, column=0, sticky="W")
    file_location_field.grid(row=5, column=0, sticky="EW")

    file_location_browse = tk.Button(frame_2, text="Browse", command=lambda : browse_folder())
    file_location_browse.grid(row=2, column=1, sticky="EW")
    
    block3.grid(row=2,column=0, padx=5, pady=(0,10), sticky="EW")

    #youtube timestamp editors
    bounds_block = tk.Frame(frame_2)
    st_label = tk.Label(bounds_block, text="Start Time [HH:MM:SS]: ")
    start_time = tk.StringVar()
    start_time_field = tk.Entry(bounds_block, textvariable=start_time, width=20)
    et_label = tk.Label(bounds_block, text="End Time [HH:MM:SS]: ")
    end_time = tk.StringVar()
    end_time_field = tk.Entry(bounds_block, textvariable=end_time, width=20)
    st_label.grid(row=0, column=0, sticky="E")
    start_time_field.grid(row=0, column=1, sticky="W")
    et_label.grid(row=1, column=0, sticky="E")
    end_time_field.grid(row=1, column=1, sticky="W")

    def reset_settings():
        url.set("")
        output_filename.set("")
        start_time.set("")
        end_time.set("")
    
    #submit button and console output
    output_bounds = tk.Frame(frame)
    console_output = tk.StringVar()
    console_output_field = tk.Entry(output_bounds, textvariable=console_output)
    submission_button = tk.Button(
                                output_bounds, text="DOWNLOAD", fg='black', bg='green',
                                command=lambda: [
                                            console_output.set(
                                                download_video( 
                                                    url.get(), 
                                                    output_filename.get()+"."+file_type.get(), 
                                                    file_location.get(),
                                                    start_time.get(), 
                                                    end_time.get()
                                                )
                                            ),
                                            save_path(file_location.get()),
                                            reset_settings(),
                                ],
                            )
    output_bounds.pack(fill="x")
    output_bounds.config(background="cyan")

    output_bounds.columnconfigure(0, weight=1)
    output_bounds.columnconfigure(1, weight=0)
    console_output_field.grid(row=0, column=0, padx=(5,0), pady=5, sticky="NSEW")
    submission_button.grid(row=0, column=1, padx=5, pady=5, sticky="E")

    gui.mainloop()

if __name__ == "__main__":
    main()
