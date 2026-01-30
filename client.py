import socket
import threading
import json
import tkinter as tk
from tkinter import filedialog, scrolledtext, font
from tkinter import ttk
import cv2 # type: ignore
import base64
import sys
import time
from PIL import Image, ImageTk # type: ignore
import numpy as np # type: ignore
import random

usercount = 1
username = f"User{usercount}"
s = socket.socket()
videopath = None
streaming = False
viewing = False
running = True

def connect():
    global s
    s = socket.socket()
    try:
        s.connect(('localhost', 5000))
        return True
    except:
        return False
    
def send(msg):
    try:
        data = json.dumps(msg).encode()
        length = len(data).to_bytes(4, 'big')
        s.sendall(length + data)
        return True
    except (ConnectionError, OSError, BrokenPipeError) as e:
        print(f"Send error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected send error: {e}")
        return False

def recv():
    try:
        length_bytes = s.recv(4)
        if len(length_bytes) != 4:
            raise ConnectionError("Connection closed")
        length = int.from_bytes(length_bytes, 'big')
        
        data = b''
        while len(data) < length:
            chunk = s.recv(length - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while receiving data")
            data += chunk
        
        return json.loads(data.decode())
    except (ConnectionError, OSError, json.JSONDecodeError) as e:
        raise ConnectionError(f"Receive error: {e}")

def startapp():
    global username, usercount
    startwin = tk.Tk()
    startwin.title("StreamNest")
    startwin.geometry("600x400")
    startwin.configure(bg="#0e0e10")
    startwin.update_idletasks()

    width = startwin.winfo_width()
    height = startwin.winfo_height()
    x = (startwin.winfo_screenwidth() // 2) - (width // 2)
    y = (startwin.winfo_screenheight() // 2) - (height // 2)

    startwin.geometry(f'{width}x{height}+{x}+{y}')
    titlefont = font.Font(family="Helvetica", size=28, weight="bold")
    title = tk.Label(startwin, text="StreamNest", font=titlefont, bg="#0e0e10", fg="#9147ff")
    title.pack(pady=(80, 10))

    descfont = font.Font(family="Helvetica", size=12)
    desc = tk.Label(startwin, text="Share your videos with friends in real-time", font=descfont, bg="#0e0e10", fg="#a19fa1")
    desc.pack(pady=(0, 40))

    userframe = tk.Frame(startwin, bg="#0e0e10")
    userframe.pack(pady=10)
    userlabel = tk.Label(userframe, text="Username:", font=("Helvetica", 10), bg="#0e0e10", fg="#a19fa1")
    userlabel.pack(side=tk.LEFT, padx=5)
    userentry = tk.Entry(userframe, width=20, font=("Helvetica", 10), bg="#18181b", fg="white", insertbackground="white")
    userentry.insert(0, username)
    userentry.pack(side=tk.LEFT, padx=5)

    btnframe = tk.Frame(startwin, bg="#0e0e10")
    btnframe.pack(pady=30)
    buttonstyle = {"font": ("Helvetica", 10), "width": 15, "height": 2, "cursor": "hand2"}
    
    def openstream():
        global username
        username = userentry.get() if userentry.get().strip() else username
        startwin.destroy()
        mainapp("stream")
    
    def openjoin():
        global username
        username = userentry.get() if userentry.get().strip() else username
        startwin.destroy()
        mainapp("join")
    
    streambtn = tk.Button(btnframe, text="Start Streaming", bg="#9147ff", fg="white", command=openstream, **buttonstyle)
    streambtn.pack(side=tk.LEFT, padx=10)
    joinbtn = tk.Button(btnframe, text="Join Stream", bg="#9147ff", fg="white", command=openjoin, **buttonstyle)
    joinbtn.pack(side=tk.LEFT, padx=10)
    statusmsg = tk.Label(startwin, text="Connecting to server...", font=("Helvetica", 8), bg="#0e0e10", fg="#a19fa1")
    statusmsg.pack(side=tk.BOTTOM, pady=10)

    if connect():
        statusmsg.config(text="Connected to server")
    else:
        statusmsg.config(text="Failed to connect to server. Please restart the application.", fg="#ff0000")
        streambtn.config(state=tk.DISABLED)
        joinbtn.config(state=tk.DISABLED)
    startwin.mainloop()

def mainapp(mode):
    global videopath, streaming, viewing, running, username
    send({"name": username})
    frame_count = 0
    last_fps_update = time.time()
    fps = 0.0
    bandwidth = 0.0
    latency = 0.0
    packet_loss = 0.0
    last_frame_time = 0
    expected_frame_seq = 0
    received_frames = 0
    total_frames_sent = 0
    bytes_sent = 0
    bytes_received = 0
    bandwidth_window = []
    latency_samples = []
    send_times = {}
    

    selected_quality = "720p"  
    quality_options = {
        "360p": (640, 360),
        "480p": (854, 480),
        "720p": (1280, 720),
        "1080p": (1920, 1080)
    }
    
    root = tk.Tk()
    root.title(f"StreamNest - {username}")
    root.geometry("1000x700")
    root.configure(bg="#0e0e10")

    headerframe = tk.Frame(root, bg="#18181b", height=60)
    headerframe.pack(fill=tk.X)
    logo = tk.Label(headerframe, text="StreamNest", font=("Helvetica", 18, "bold"), bg="#18181b", fg="#9147ff")
    logo.pack(side=tk.LEFT, padx=20, pady=10)
    contentframe = tk.Frame(root, bg="#0e0e10")
    contentframe.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    videoframe = tk.Frame(contentframe, bg="#18181b", width=700)
    videoframe.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    videoframe.pack_propagate(False)
    videoborder = tk.Frame(videoframe, bg="#18181b", bd=1, relief=tk.SOLID)
    videoborder.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    videolabel = tk.Label(videoborder, bg="black")
    videolabel.pack(fill=tk.BOTH, expand=True)

    controlframe = tk.Frame(videoframe, height=50, bg="#18181b")
    controlframe.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    
    qualityframe = tk.Frame(controlframe, bg="#18181b")
    qualityvar = tk.StringVar(value=selected_quality)
    qualitylabel = tk.Label(qualityframe, text="Quality:", font=("Helvetica", 9), bg="#18181b", fg="white")
    qualitylabel.pack(side=tk.LEFT, padx=(0, 5))
    qualitymenu = ttk.Combobox(qualityframe, textvariable=qualityvar, values=list(quality_options.keys()), 
                               state="readonly", width=8, font=("Helvetica", 9))
    
    
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TCombobox", fieldbackground="#18181b", background="#18181b", 
                   foreground="white", borderwidth=1, relief="solid")
    style.map("TCombobox", fieldbackground=[("readonly", "#18181b")],
             background=[("readonly", "#18181b")],
             foreground=[("readonly", "white")])
    
    qualitymenu.pack(side=tk.LEFT)
  
    if mode == "join":
        qualityframe.pack(side=tk.RIGHT, padx=10, pady=5)
    chatframe = tk.Frame(contentframe, bg="#18181b", width=280)
    chatframe.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
    chatframe.pack_propagate(False)
    right_paned = tk.PanedWindow(chatframe, orient=tk.VERTICAL, bg="#18181b", sashwidth=5, sashrelief=tk.FLAT)
    right_paned.pack(fill=tk.BOTH, expand=True)
    chatcontainer = tk.Frame(right_paned, bg="#18181b")
    right_paned.add(chatcontainer, minsize=200)
    
    chattitle = tk.Label(chatcontainer, text="Live Chat", font=("Helvetica", 12, "bold"), bg="#18181b", fg="#9147ff")
    chattitle.pack(pady=(10, 5))
    bottomframe = tk.Frame(chatcontainer, bg="#18181b")
    bottomframe.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))
    
    chatinput = tk.Entry(bottomframe, font=("Helvetica", 10), bg="#0e0e10", fg="white", insertbackground="white")
    chatinput.pack(fill=tk.X, side=tk.LEFT, expand=True)
    
    sendbtn = tk.Button(bottomframe, text="Send", bg="#9147ff", fg="white", font=("Helvetica", 9), height=1, cursor="hand2", width=8)
    sendbtn.pack(side=tk.RIGHT, padx=(5, 0))
    chatbox = scrolledtext.ScrolledText(chatcontainer, bg="#0e0e10", font=("Helvetica", 9), fg="white", insertbackground="white")
    chatbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
    chatbox.config(state='disabled')

    statsframe = tk.Frame(right_paned, bg="#18181b")
    right_paned.add(statsframe, minsize=150)
    statstitle = tk.Label(statsframe, text="Stream Stats", font=("Helvetica", 12, "bold"), bg="#18181b", fg="#9147ff")
    statstitle.pack(pady=(10, 5))
    statscontent = tk.Frame(statsframe, bg="#0e0e10")
    statscontent.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    statscontent.columnconfigure(0, weight=1)
    statscontent.rowconfigure(0, weight=1)
    statscontent.rowconfigure(1, weight=1)
    statscontent.rowconfigure(2, weight=1)
    statscontent.rowconfigure(3, weight=1)
    
    fpslbl = tk.Label(statscontent, text="FPS: 0", font=("Helvetica", 9), bg="#0e0e10", fg="white", anchor="w")
    fpslbl.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    bandwidthlbl = tk.Label(statscontent, text="Bandwidth: 0.0 kbps", font=("Helvetica", 9), bg="#0e0e10", fg="white", anchor="w")
    bandwidthlbl.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    latencylbl = tk.Label(statscontent, text="Latency: 0.0 ms", font=("Helvetica", 9), bg="#0e0e10", fg="white", anchor="w")
    latencylbl.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
    packetlosslbl = tk.Label(statscontent, text="Packet Loss: 0.0%", font=("Helvetica", 9), bg="#0e0e10", fg="white", anchor="w")
    packetlosslbl.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
    
    statusframe = tk.Frame(root, bg="#18181b", height=25)
    statusframe.pack(fill=tk.X, side=tk.BOTTOM)
    statuslbl = tk.Label(statusframe, text="Not connected", font=("Helvetica", 8), bg="#18181b", fg="#a19fa1")
    statuslbl.pack(side=tk.LEFT, padx=10)
    userlbl = tk.Label(statusframe, text=f"Logged in as: {username}", font=("Helvetica", 8), bg="#18181b", fg="#a19fa1")
    userlbl.pack(side=tk.RIGHT, padx=10)
    
    def select():
        global videopath
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        if path:
            videopath = path
            statuslbl.config(text=f"Selected: {path.split('/')[-1]}")
            filelbl.config(text=f"File: {path.split('/')[-1]}")
    
    def start():
        if not videopath:
            statuslbl.config(text="Select a video first")
            return
        send({"type": "start"})
    
    def stop():
        global streaming
        send({"type": "stop"})
        streaming = False
        streambtn.config(text="Start Stream", bg="#9147ff")
        statuslbl.config(text="Streaming stopped")
    
    def stream():
        global streaming
        nonlocal frame_count, last_fps_update, fps, bytes_sent, bandwidth_window, total_frames_sent, bandwidth
        cap = cv2.VideoCapture(videopath)
       
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
     
        send_width = min(1920, original_width)
        send_height = min(1080, original_height)
      
        if original_width > 0 and original_height > 0:
            aspect = original_width / original_height
            if send_width / send_height > aspect:
                send_width = int(send_height * aspect)
            else:
                send_height = int(send_width / aspect)
        
        while streaming and running:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
           
            h, w = frame.shape[:2]
            ratio = min(videolabel.winfo_width()/w, videolabel.winfo_height()/h)
            newsize = (int(w*ratio), int(h*ratio))
            display_frame = cv2.resize(frame.copy(), newsize)
            rgbframe = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgbframe)
            imgtk = ImageTk.PhotoImage(image=img)
            videolabel.imgtk = imgtk
            videolabel.config(image=imgtk)
            
            sendframe = cv2.resize(frame, (send_width, send_height))
            _, buf = cv2.imencode('.jpg', sendframe, [cv2.IMWRITE_JPEG_QUALITY, 85])
            b64 = base64.b64encode(buf).decode()
            
    
            timestamp = time.time()
            send_msg = {"type": "video", "data": b64, "seq": total_frames_sent, "timestamp": timestamp}
            frame_bytes = len(json.dumps(send_msg).encode())
            bandwidth_window.append((timestamp, frame_bytes * 8 / 1000))
            bandwidth_window = [(t, b) for t, b in bandwidth_window if timestamp - t < 2.0]
            
          
            if send(send_msg):
                total_frames_sent += 1
                frame_count += 1
            else:
                
                print("Connection lost during streaming")
                streaming = False
                root.after(0, lambda: statuslbl.config(text="Connection lost - streaming stopped"))
                root.after(0, lambda: streambtn.config(text="Start Stream", bg="#9147ff") if 'streambtn' in locals() else None)
                break
            
            # Calculate FPS every 0.5 seconds
            current_time = time.time()
            if current_time - last_fps_update >= 0.5:
                fps = frame_count / (current_time - last_fps_update)
                frame_count = 0
                last_fps_update = current_time
            
            time.sleep(0.03)
        cap.release()
    
    def toggle():
        global streaming
        if not streaming:
            start()
        else:
            stop()
    
    def chat(event=None):
        msg = chatinput.get()
        if msg.strip():
            send({"type": "chat", "msg": msg})
            chatinput.delete(0, tk.END)
    
    def change_quality(event=None):
        nonlocal selected_quality
        selected_quality = qualityvar.get()
        statuslbl.config(text=f"Quality changed to {selected_quality}")
       
        try:
            send({"type": "quality_change", "quality": selected_quality})
        except:
            pass  
    
    def updatevideo(img):
        label_w = videolabel.winfo_width()
        label_h = videolabel.winfo_height()
        if label_w > 1 and label_h > 1:
            img_array = np.array(img)
            h, w = img_array.shape[:2]
            aspect_ratio = w / h
            display_aspect = label_w / label_h
            
            if aspect_ratio > display_aspect:
                display_w = label_w
                display_h = int(label_w / aspect_ratio)
            else:
                display_h = label_h
                display_w = int(label_h * aspect_ratio)
            
            img_resized = img.resize((display_w, display_h), Image.Resampling.LANCZOS)
        else:
            img_resized = img
        
        imgtk = ImageTk.PhotoImage(image=img_resized)
        videolabel.imgtk = imgtk
        videolabel.config(image=imgtk)
    
    #stats are being updated every 5s
    def updatestats():
        nonlocal fps, bandwidth, latency, packet_loss, bandwidth_window
        if bandwidth_window:
            total_bits = sum(b for _, b in bandwidth_window)
            time_span = max(0.1, bandwidth_window[-1][0] - bandwidth_window[0][0])
            bandwidth = total_bits / time_span if time_span > 0 else 0.0
        else:
            bandwidth = 0.0
            
        fpslbl.config(text=f"FPS: {fps:.1f}")
        bandwidthlbl.config(text=f"Bandwidth: {bandwidth:.1f} kbps")
        latencylbl.config(text=f"Latency: {latency:.1f} ms")
        packetlosslbl.config(text=f"Packet Loss: {packet_loss:.1f}%")
        root.after(500, updatestats)  
    
    def endstream():
        send({"type": "endstream"})
        
    def listen():
        global streaming, viewing
        nonlocal frame_count, last_fps_update, fps, expected_frame_seq, received_frames, bytes_received, latency_samples, bandwidth_window, latency, packet_loss, bandwidth
        while running:
            try:
                msg = recv()
                t = msg.get("type")
                if t == "status":
                    active = msg.get("active", False)
                    if active:
                        if not streaming:
                            statuslbl.config(text="Someone is streaming")
                            if mode == "stream":
                                streambtn.config(state=tk.DISABLED)
                                
                                root.after(0, lambda: qualityframe.pack(side=tk.RIGHT, padx=10, pady=5))
                            viewing = True
                            
                            frame_count = 0
                            last_fps_update = time.time()
                            expected_frame_seq = 0
                            received_frames = 0
                            latency_samples = []
                            bandwidth_window = []
                    else:
                        statuslbl.config(text="No active streams")
                        if mode == "stream":
                            streambtn.config(state=tk.NORMAL)
                        
                            root.after(0, lambda: qualityframe.pack_forget())
                        viewing = False
                        videolabel.config(image="")
                    
                        fps = 0.0
                        bandwidth = 0.0
                        latency = 0.0
                        packet_loss = 0.0
                elif t == "start":
                    if msg.get("ok"):
                        streaming = True
                        streambtn.config(text="Stop Stream", bg="#ff0000")
                        statuslbl.config(text="Streaming started")
                    
                        if mode == "stream":
                            root.after(0, lambda: qualityframe.pack_forget())
                        frame_count = 0
                        last_fps_update = time.time()
                        bytes_sent = 0
                        bandwidth_window = []
                        total_frames_sent = 0
                        threading.Thread(target=stream, daemon=True).start()
                    else:
                        statuslbl.config(text="Cannot stream: Another user is streaming")
                elif t == "video":
                    if viewing or streaming:
                        b64 = msg.get("data")
                        seq = msg.get("seq", -1)
                        timestamp = msg.get("timestamp", 0)
                        if b64:
                            jpg_bytes = base64.b64decode(b64)
                            bytes_received += len(jpg_bytes)
                            
                            if timestamp > 0:
                                current_latency = (time.time() - timestamp) * 1000  
                                latency_samples.append(current_latency)
                                if len(latency_samples) > 20:
                                    latency_samples.pop(0)
                                latency = sum(latency_samples) / len(latency_samples) if latency_samples else 0.0
                            
                           
                            if seq >= 0:
                                if seq > expected_frame_seq:
                                    
                                    lost = seq - expected_frame_seq
                                    received_frames += lost + 1
                                    expected_frame_seq = seq + 1
                                elif seq == expected_frame_seq:
                                    received_frames += 1
                                    expected_frame_seq = seq + 1
                                else:
                                  
                                    received_frames += 1
                                
                                if received_frames > 0:
                                    total_expected = expected_frame_seq
                                    if total_expected > 0:
                                        packet_loss = max(0, (1 - received_frames / total_expected) * 100)
                            
                            
                            if viewing:
                                frame_count += 1
                                current_time = time.time()
                                if current_time - last_fps_update >= 0.5:
                                    fps = frame_count / (current_time - last_fps_update)
                                    frame_count = 0
                                    last_fps_update = current_time
                                
                               
                                frame_size_kbits = (len(jpg_bytes) * 8) / 1000
                                bandwidth_window.append((time.time(), frame_size_kbits))
                                bandwidth_window = [(t, b) for t, b in bandwidth_window if time.time() - t < 2.0]
                            
                            np_img = np.frombuffer(jpg_bytes, dtype=np.uint8)
                            frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
                            
                            quality_size = quality_options.get(selected_quality, (1280, 720))
                            h, w = frame.shape[:2]
                            target_w, target_h = quality_size
                            aspect_ratio = w / h
                            target_aspect = target_w / target_h
                            
                            if aspect_ratio > target_aspect:
                                new_w = target_w
                                new_h = int(target_w / aspect_ratio)
                            else:
                                new_h = target_h
                                new_w = int(target_h * aspect_ratio)
                            
                           
                            if new_w < w or new_h < h:
                                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                            
                            img = Image.fromarray(frame)
                            root.after(0, updatevideo, img)
                elif t == "chat":
                    sender = msg.get("name", "anon")
                    text = msg.get("msg", "")
                    chatbox.config(state='normal')
                    if sender == username:
                        chatbox.insert(tk.END, f"{sender}: ", "self")
                    else:
                        chatbox.insert(tk.END, f"{sender}: ", "other")
                    chatbox.insert(tk.END, f"{text}\n")
                    chatbox.yview(tk.END)
                    chatbox.config(state='disabled')
            except Exception as e:
                print(f"Error: {e}")
                break
    
    def close():
        global running
        running = False
        if streaming:
            stop()
        try:
            s.close()
        except:
            pass
        root.destroy()

    if mode == "stream":
        filebtn = tk.Button(controlframe, text="Select Video", bg="#9147ff", fg="white", font=("Helvetica", 9), command=select, width=15, cursor="hand2")
        filebtn.pack(side=tk.LEFT, padx=10, pady=5)
        filelbl = tk.Label(controlframe, text="No file selected", bg="#18181b", font=("Helvetica", 9), fg="white")
        filelbl.pack(side=tk.LEFT, padx=5, pady=5)
        streambtn = tk.Button(controlframe, text="Start Stream", bg="#9147ff", fg="white", font=("Helvetica", 9), command=toggle, width=15, cursor="hand2")
        streambtn.pack(side=tk.RIGHT, padx=10, pady=5)
    chatbox.tag_config("self", foreground="#9147ff", font=("Helvetica", 9, "bold"))
    chatbox.tag_config("other", foreground="#00b5ad", font=("Helvetica", 9, "bold"))
    sendbtn.config(command=chat)
    chatinput.bind("<Return>", chat)
    qualitymenu.bind("<<ComboboxSelected>>", change_quality)
    root.protocol("WM_DELETE_WINDOW", close)
    updatestats()  
    threading.Thread(target=listen, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    startapp()