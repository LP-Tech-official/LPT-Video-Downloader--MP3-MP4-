import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import yt_dlp as youtube_dl
import os
import threading
import json
from datetime import datetime
import requests
from io import BytesIO
import sys

# Global Variables
current_language = 'en'
downloading = False
download_thread = None
video_title = ""
video_description = ""
video_duration = ""
download_history = []
history_file = "download_history.json"
status_message = ""
progress_popup = None
progress_bar = None

# Language Translations
translations = {
    'en': {
        'enter_url': 'Enter YouTube URL:',
        'download_video': 'Download Video',
        'select_quality': 'Select Quality',
        'select_format': 'Select Format',
        'downloading': 'Downloading...',
        'completed': 'Download completed!',
        'success': 'Video downloaded successfully!\nSaved to: ',
        'error': 'An error occurred: ',
        'warning': 'Please enter a valid YouTube video URL.',
        'footer_text': 'Made by LP-Tech Germany',
        'terms': 'Terms of Service',
        'privacy': 'Privacy Policy',
        'description': 'Description:',
        'duration': 'Duration:',
        'confirm': 'Confirm',
        'cancel': 'Cancel',
        'terms_text': (
            "Terms of Service\n\n"
            "1. Acceptance of Terms\n"
            "By accessing and using this application, you accept and agree to be bound by these terms and conditions.\n\n"
            "2. Use License\n"
            "You are granted a license to use this application for personal, non-commercial use only.\n\n"
            "3. Restrictions\n"
            "You shall not modify, copy, distribute, or reverse engineer the application.\n\n"
            "4. Disclaimer\n"
            "The application is provided 'as is' without warranties of any kind.\n\n"
            "5. Limitation of Liability\n"
            "In no event shall the developers be liable for any damages arising out of the use of this application.\n\n"
            "6. Changes to Terms\n"
            "The developers reserve the right to modify these terms at any time.\n\n"
        ),
        'privacy_text': (
            "Privacy Policy\n\n"
            "1. Data Collection\n"
            "We do not collect any personal data through this application.\n\n"
            "2. Data Usage\n"
            "No data is used for any purposes.\n\n"
            "3. Data Security\n"
            "We strive to protect your data but cannot guarantee its absolute security.\n\n"
            "4. Changes to Privacy Policy\n"
            "We may update our Privacy Policy from time to time.\n\n"
        )
    },
    'de': {
        'enter_url': 'YouTube-URL eingeben:',
        'download_video': 'Video herunterladen',
        'select_quality': 'Qualität auswählen',
        'select_format': 'Format auswählen',
        'downloading': 'Wird heruntergeladen...',
        'completed': 'Download abgeschlossen!',
        'success': 'Video erfolgreich heruntergeladen!\nGespeichert unter: ',
        'error': 'Ein Fehler ist aufgetreten: ',
        'warning': 'Bitte geben Sie eine gültige YouTube-Video-URL ein.',
        'footer_text': 'Hergestellt von LP-Tech Germany',
        'terms': 'Nutzungsbedingungen',
        'privacy': 'Datenschutzrichtlinie',
        'description': 'Beschreibung:',
        'duration': 'Dauer:',
        'confirm': 'Bestätigen',
        'cancel': 'Abbrechen',
        'terms_text': (
            "Nutzungsbedingungen\n\n"
            "1. Annahme der Bedingungen\n"
            "Durch den Zugriff auf und die Nutzung dieser Anwendung akzeptieren und stimmen Sie zu, an diese Bedingungen gebunden zu sein.\n\n"
            "2. Nutzungslizenz\n"
            "Ihnen wird eine Lizenz zur Nutzung dieser Anwendung für persönliche, nicht kommerzielle Zwecke gewährt.\n\n"
            "3. Einschränkungen\n"
            "Sie dürfen die Anwendung nicht modifizieren, kopieren, verteilen oder zurückentwickeln.\n\n"
            "4. Haftungsausschluss\n"
            "Die Anwendung wird 'wie besehen' ohne jegliche Garantien bereitgestellt.\n\n"
            "5. Haftungsbeschränkung\n"
            "Die Entwickler haften in keinem Fall für Schäden, die sich aus der Nutzung dieser Anwendung ergeben.\n\n"
            "6. Änderungen der Bedingungen\n"
            "Die Entwickler behalten sich das Recht vor, diese Bedingungen jederzeit zu ändern.\n\n"
        ),
        'privacy_text': (
            "Datenschutzrichtlinie\n\n"
            "1. Datenerhebung\n"
            "Wir erheben keine personenbezogenen Daten durch diese Anwendung.\n\n"
            "2. Datennutzung\n"
            "Es werden keine Daten für irgendwelche Zwecke verwendet.\n\n"
            "3. Datensicherheit\n"
            "Wir bemühen uns, Ihre Daten zu schützen, können jedoch keine absolute Sicherheit garantieren.\n\n"
            "4. Änderungen der Datenschutzrichtlinie\n"
            "Wir können unsere Datenschutzrichtlinie von Zeit zu Zeit aktualisieren.\n\n"
        )
    }
}

def translate_text(key):
    return translations[current_language].get(key, key)

def update_status_message(message):
    global status_message
    status_message = message
    status_label.config(text=status_message)
    root.update_idletasks()

def download_video(url, quality, file_format):
    global downloading, video_title, video_description, video_duration
    ydl_opts = {
        'format': f'{quality}/{file_format}',
        'outtmpl': os.path.join(get_videos_folder(), 'LPT-Downloader', '%(title)s.%(ext)s'),
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio' if file_format == 'mp3' else None,
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if file_format == 'mp3' else []
    }
    try:
        os.makedirs(os.path.dirname(ydl_opts['outtmpl']), exist_ok=True)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', '')
            video_description = info_dict.get('description', '')
            video_duration = info_dict.get('duration', 0)
            file_path = ydl.prepare_filename(info_dict)
            download_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Download thumbnail
            thumbnail_url = info_dict.get('thumbnail', '')
            if thumbnail_url:
                response = requests.get(thumbnail_url)
                img_data = response.content
                thumbnail_path = os.path.join('thumbnails', f"{video_title}.jpg")
                os.makedirs('thumbnails', exist_ok=True)
                with open(thumbnail_path, 'wb') as img_file:
                    img_file.write(img_data)

            download_history.append({
                'title': video_title,
                'description': video_description,
                'duration': video_duration,
                'file_path': file_path,
                'thumbnail': thumbnail_path if thumbnail_url else '',
                'date': download_date
            })
            save_history()
            update_status_message(f"{translate_text('success')} {file_path}")
            os.startfile(os.path.dirname(file_path))
            close_progress_popup()
    except Exception as e:
        update_status_message(f"{translate_text('error')} {str(e)}")
    finally:
        downloading = False
        download_button.config(state=tk.NORMAL)
        url_entry.config(state=tk.NORMAL)

def start_download():
    global downloading, download_thread
    if not downloading:
        url = url_entry.get()
        quality = quality_var.get()
        file_format = format_var.get()
        if not url:
            messagebox.showwarning(translate_text('warning'), translate_text('warning'))
            return
        downloading = True
        download_button.config(state=tk.DISABLED)
        url_entry.config(state=tk.DISABLED)
        download_thread = threading.Thread(target=download_video, args=(url, quality, file_format))
        download_thread.start()
        create_progress_popup()
    else:
        messagebox.showwarning(translate_text('warning'), translate_text('warning'))

def create_progress_popup():
    global progress_popup, progress_bar
    progress_popup = tk.Toplevel(root)
    progress_popup.title(translate_text('downloading'))
    progress_popup.geometry("400x150")
    progress_popup.configure(bg="#2c3e50")
    progress_label = tk.Label(progress_popup, text=translate_text('downloading'), bg="#2c3e50", fg="white", font=('Helvetica', 12))
    progress_label.pack(pady=20)
    progress_bar = ttk.Progressbar(progress_popup, mode='determinate', length=300)
    progress_bar.pack(pady=10)
    progress_popup.transient(root)
    progress_popup.grab_set()
    root.update_idletasks()

def progress_hook(d):
    if d['status'] == 'downloading':
        progress = d['downloaded_bytes'] / d['total_bytes'] * 100
        progress_bar['value'] = progress
        root.update_idletasks()

def close_progress_popup():
    global progress_popup
    if progress_popup:
        progress_popup.destroy()
        progress_popup = None

def save_history():
    with open(history_file, 'w') as file:
        json.dump(download_history, file)

def load_history():
    global download_history
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            download_history = json.load(file)

def get_videos_folder():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))

def switch_language():
    global current_language
    current_language = 'de' if current_language == 'en' else 'en'
    refresh_texts()

def refresh_texts():
    enter_url_label.config(text=translate_text('enter_url'))
    quality_label.config(text=translate_text('select_quality'))
    format_label.config(text=translate_text('select_format'))
    download_button.config(text=translate_text('download_video'))
    status_label.config(text=status_message)
    terms_button.config(text=translate_text('terms'))
    privacy_button.config(text=translate_text('privacy'))
    footer_label.config(text=translate_text('footer_text'))
    language_button.config(text="Switch to Deutsch" if current_language == 'en' else "Switch to English")

def on_closing():
    if downloading:
        if messagebox.askokcancel(translate_text('cancel'), translate_text('confirm')):
            root.destroy()
    else:
        root.destroy()

def show_terms():
    messagebox.showinfo(translate_text('terms'), translate_text('terms_text'))

def show_privacy():
    messagebox.showinfo(translate_text('privacy'), translate_text('privacy_text'))

# Create main application window
root = tk.Tk()
root.title("LP-Tech Video Downloader")
root.geometry("1200x800")
root.configure(bg="#2c3e50")

# Set up logo
logo_path = os.path.join(get_videos_folder(), "Logo.png")
logo_image = Image.open(logo_path)
logo_image = logo_image.resize((300, 300), Image.LANCZOS)
logo_photo = ImageTk.PhotoImage(logo_image)
logo_label = tk.Label(root, image=logo_photo, bg="#2c3e50")
logo_label.grid(row=0, column=0, columnspan=4, pady=20, padx=20)

# URL entry
url_frame = tk.Frame(root, bg="#34495e")
url_frame.grid(row=1, column=0, columnspan=4, pady=10, padx=30, sticky="ew")
enter_url_label = tk.Label(url_frame, text=translate_text('enter_url'), bg="#34495e", fg="white", font=('Helvetica', 16))
enter_url_label.pack(side=tk.LEFT, padx=10)
url_entry = tk.Entry(url_frame, font=('Helvetica', 16))
url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

# Quality selection
quality_frame = tk.Frame(root, bg="#34495e")
quality_frame.grid(row=2, column=0, columnspan=4, pady=10, padx=30, sticky="ew")
quality_label = tk.Label(quality_frame, text=translate_text('select_quality'), bg="#34495e", fg="white", font=('Helvetica', 16))
quality_label.pack(side=tk.LEFT, padx=10)
quality_var = tk.StringVar(value="best")
quality_options = ["best", "worst", "medium"]
quality_dropdown = ttk.Combobox(quality_frame, textvariable=quality_var, values=quality_options, font=('Helvetica', 16), state='readonly')
quality_dropdown.pack(side=tk.LEFT, padx=10)

# Format selection
format_frame = tk.Frame(root, bg="#34495e")
format_frame.grid(row=3, column=0, columnspan=4, pady=10, padx=30, sticky="ew")
format_label = tk.Label(format_frame, text=translate_text('select_format'), bg="#34495e", fg="white", font=('Helvetica', 16))
format_label.pack(side=tk.LEFT, padx=10)
format_var = tk.StringVar(value="mp4")
format_options = ["mp4", "mp3"]
format_dropdown = ttk.Combobox(format_frame, textvariable=format_var, values=format_options, font=('Helvetica', 16), state='readonly')
format_dropdown.pack(side=tk.LEFT, padx=10)

# Download button
download_button = tk.Button(root, text=translate_text('download_video'), command=start_download, font=('Helvetica', 16), bg="#2980b9", fg="white", activebackground="#3498db", activeforeground="white")
download_button.grid(row=4, column=0, columnspan=4, pady=30, padx=20)

# Status message
status_label = tk.Label(root, text=status_message, bg="#2c3e50", fg="white", font=('Helvetica', 14))
status_label.grid(row=5, column=0, columnspan=4, pady=30, padx=20)

# Terms and Privacy buttons
footer_frame = tk.Frame(root, bg="#2c3e50")
footer_frame.grid(row=6, column=0, columnspan=4, pady=20, padx=20, sticky="ew")
terms_button = tk.Button(footer_frame, text=translate_text('terms'), command=show_terms, bg="#34495e", fg="white", font=('Helvetica', 12))
terms_button.pack(side=tk.LEFT, padx=15)
privacy_button = tk.Button(footer_frame, text=translate_text('privacy'), command=show_privacy, bg="#34495e", fg="white", font=('Helvetica', 12))
privacy_button.pack(side=tk.LEFT, padx=15)

# Language switch button
language_button = tk.Button(footer_frame, text="Switch to Deutsch", command=switch_language, bg="#34495e", fg="white", font=('Helvetica', 12))
language_button.pack(side=tk.RIGHT, padx=15)

# Footer
footer_label = tk.Label(root, text=translate_text('footer_text'), bg="#2c3e50", fg="white", font=('Helvetica', 12))
footer_label.grid(row=7, column=0, columnspan=4, pady=20, padx=20)

# Configure column and row weights
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(2, weight=1)
root.grid_rowconfigure(3, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_rowconfigure(5, weight=1)
root.grid_rowconfigure(6, weight=1)
root.grid_rowconfigure(7, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)

# Load download history
load_history()

# Handle closing of the window
root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the main loop
root.mainloop()
