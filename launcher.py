import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import sys
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.join(BASE_DIR, "server.py")
CLIENT_PATH = os.path.join(BASE_DIR, "client.py")

server_process = None

def start_server():
    global server_process

    if server_process is not None:
        messagebox.showinfo("Server Running", "Server is already running!")
        return

    try:
        server_process = subprocess.Popen(
            [sys.executable, SERVER_PATH],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        server_status.config(text="● RUNNING", foreground="#00ff88")
        start_btn.config(state="disabled", cursor="arrow")
        stop_btn.config(state="normal", cursor="hand2")
        messagebox.showinfo("Server Started", "StreamNest Server is now running!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start server:\n{e}")

def start_client():
    try:
        subprocess.Popen(
            [sys.executable, CLIENT_PATH],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except Exception as e:
        messagebox.showerror("Error", f"Could not start client:\n{e}")

def stop_server():
    global server_process
    if server_process is None:
        messagebox.showinfo("Server Not Running", "Server is not started.")
        return
    
    server_process.terminate()
    server_process = None
    server_status.config(text="● STOPPED", foreground="#ff4444")
    start_btn.config(state="normal", cursor="hand2")
    stop_btn.config(state="disabled", cursor="arrow")
    messagebox.showinfo("Server Stopped", "Server has been stopped.")

def exit_app():
    if server_process:
        server_process.terminate()
    app.destroy()

def on_enter(e):
    e.widget.config(bg="#a366ff")

def on_leave(e):
    e.widget.config(bg="#9147ff")

def on_enter_exit(e):
    e.widget.config(bg="#ff6666")

def on_leave_exit(e):
    e.widget.config(bg="#ff4444")


app = tk.Tk()
app.title("StreamNest Launcher")
app.geometry("500x550")
app.configure(bg="#0e0e10")
app.resizable(False, False)

app.eval('tk::PlaceWindow . center')

style = ttk.Style()
style.theme_use('clam')


style.configure("Custom.TFrame", background="#1f1f23")
style.configure("Title.TLabel", background="#0e0e10", foreground="#9147ff", 
                font=("Segoe UI", 24, "bold"))
style.configure("Subtitle.TLabel", background="#1f1f23", foreground="#efeff1", 
                font=("Segoe UI", 10))
style.configure("Status.TLabel", background="#1f1f23", foreground="#ff4444", 
                font=("Segoe UI", 11, "bold"))


main_frame = ttk.Frame(app, style="Custom.TFrame", relief="raised", borderwidth=1)
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

header_frame = ttk.Frame(main_frame, style="Custom.TFrame")
header_frame.pack(fill="x", padx=30, pady=(30, 20))

title = ttk.Label(header_frame, text="StreamNest", style="Title.TLabel")
title.pack()

subtitle = ttk.Label(header_frame, text="Media Streaming Platform", style="Subtitle.TLabel")
subtitle.pack(pady=(5, 0))

status_frame = ttk.Frame(main_frame, style="Custom.TFrame")
status_frame.pack(fill="x", padx=30, pady=20)

ttk.Label(status_frame, text="Server Status:", style="Subtitle.TLabel").pack(anchor="w")
server_status = ttk.Label(status_frame, text="● STOPPED", style="Status.TLabel")
server_status.pack(anchor="w", pady=(5, 0))

button_frame = ttk.Frame(main_frame, style="Custom.TFrame")
button_frame.pack(fill="x", padx=30, pady=20)


btn_style = {
    "font": ("Segoe UI", 12, "bold"),
    "width": 22,
    "height": 2,
    "bg": "#9147ff",
    "fg": "white",
    "border": 0,
    "cursor": "hand2",
    "relief": "flat",
    "activebackground": "#a366ff",
    "activeforeground": "white"
}


start_btn = tk.Button(button_frame, text="Start a Server", command=start_server, **btn_style)
start_btn.pack(pady=12)
start_btn.bind("<Enter>", on_enter)
start_btn.bind("<Leave>", on_leave)

client_btn = tk.Button(button_frame, text="Enter as Client", command=start_client, **btn_style)
client_btn.pack(pady=12)
client_btn.bind("<Enter>", on_enter)
client_btn.bind("<Leave>", on_leave)

stop_btn = tk.Button(button_frame, text="Stop Server", command=stop_server, **btn_style)
stop_btn.pack(pady=12)
stop_btn.config(state="disabled", bg="#666666", cursor="arrow")
stop_btn.bind("<Enter>", on_enter)
stop_btn.bind("<Leave>", on_leave)

exit_btn_style = btn_style.copy()
exit_btn_style.update({"bg": "#ff4444", "activebackground": "#ff6666", "width": 18})

exit_btn = tk.Button(button_frame, text="Exit Application", command=exit_app, **exit_btn_style)
exit_btn.pack(pady=(20, 10))
exit_btn.bind("<Enter>", on_enter_exit)
exit_btn.bind("<Leave>", on_leave_exit)

footer_frame = ttk.Frame(main_frame, style="Custom.TFrame")
footer_frame.pack(fill="x", padx=30, pady=(10, 20))

ttk.Label(footer_frame, text="StreamNest v1.0", style="Subtitle.TLabel").pack(side="left")
ttk.Label(footer_frame, text="© 2024", style="Subtitle.TLabel").pack(side="right")
separator = ttk.Separator(button_frame, orient='horizontal')
separator.pack(fill='x', pady=10)

app.mainloop()