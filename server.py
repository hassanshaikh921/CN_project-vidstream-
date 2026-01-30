import socket
import threading
import json
import time
clients = []
streamer = None
lock = threading.Lock()
# Track client info: {sock: {"name": str, "quality": str}}
client_info = {}

def send(sock, msg):
    data = json.dumps(msg).encode()
    length = len(data).to_bytes(4, 'big')
    sock.sendall(length + data)

def recv(sock):
    try:
        # Receive length header
        length_bytes = sock.recv(4)
        if len(length_bytes) != 4:
            raise ConnectionError("Connection closed")
        length = int.from_bytes(length_bytes, 'big')
        
        # Receive data in chunks if needed (important for large video frames)
        data = b''
        while len(data) < length:
            chunk = sock.recv(min(length - len(data), 4096))
            if not chunk:
                raise ConnectionError("Connection closed while receiving data")
            data += chunk
        
        return json.loads(data.decode())
    except (ConnectionError, OSError, json.JSONDecodeError) as e:
        raise ConnectionError(f"Receive error: {e}")

def sendall(msg, skip=None):
    """Send message to all clients except skip"""
    disconnected = []
    for c in clients[:]:  # Use copy to avoid modification during iteration
        if c != skip:
            try:
                send(c, msg)
            except (ConnectionError, OSError, BrokenPipeError):
                # Mark for removal
                disconnected.append(c)
            except Exception as e:
                print(f"Error sending to client: {e}")
    
    # Remove disconnected clients
    for c in disconnected:
        if c in clients:
            clients.remove(c)
        with lock:
            if c in client_info:
                name = client_info[c].get("name", "Unknown")
                print(f"Removed disconnected client: {name}")
                del client_info[c]

def get_stats():
    """Get server statistics"""
    with lock:
        quality_dist = {}
        for info in client_info.values():
            q = info.get("quality", "720p")
            quality_dist[q] = quality_dist.get(q, 0) + 1
        return {
            "total_clients": len(clients),
            "streamer_active": streamer is not None,
            "quality_distribution": quality_dist
        }

def handle(sock, addr):
    global streamer
    try:
        clients.append(sock)
        print(f"{addr} joined")
        send(sock, {"type": "status", "active": streamer is not None})
        name = recv(sock).get("name", "anon")
        # Initialize client info
        with lock:
            client_info[sock] = {"name": name, "quality": "720p"}
        print(f"User {name} connected from {addr}")
        sendall({"type": "chat", "name": "Server", "msg": f"{name} has joined"})
        while True:
            try:
                msg = recv(sock)
            except ConnectionError as e:
                print(f"Connection error with {name}: {e}")
                break
            except Exception as e:
                print(f"Error receiving from {name}: {e}")
                break
            
            t = msg.get("type")
            if t == "start":
                with lock:
                    if not streamer:
                        streamer = sock
                        viewer_count = len(clients) - 1  # Exclude streamer
                        send(sock, {"type": "start", "ok": True})
                        sendall({"type": "status", "active": True})
                        print(f"{name} started streaming ({viewer_count} viewer{'s' if viewer_count != 1 else ''} ready)")
                        sendall({"type": "chat", "name": "Server", "msg": f"{name} started streaming"})
                    else:
                        send(sock, {"type": "start", "ok": False})
                        print(f"{name} tried to stream but another stream is active")
            elif t == "stop":
                with lock:
                    if streamer == sock:
                        streamer = None
                        sendall({"type": "status", "active": False})
                        print(f"{name} stopped streaming")
                        sendall({"type": "chat", "name": "Server", "msg": f"{name} stopped streaming"})
            elif t == "video":
                if sock == streamer:
                    # Broadcast video to all viewers with their quality preferences
                    # Currently sends full quality, clients handle downscaling
                    sendall({"type": "video", "data": msg["data"], 
                            "seq": msg.get("seq", 0), 
                            "timestamp": msg.get("timestamp", 0)}, skip=None)
            elif t == "quality_change":
                # Handle quality preference change from client
                quality = msg.get("quality", "720p")
                with lock:
                    if sock in client_info:
                        client_info[sock]["quality"] = quality
                print(f"User {name} changed quality to {quality}")
            elif t == "chat":
                chatmsg = msg.get("msg", "")
                print(f"Chat: {name}: {chatmsg}")
                sendall({"type": "chat", "name": name, "msg": chatmsg}, skip=None)
    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        if sock in clients:
            clients.remove(sock)
        with lock:
            if sock in client_info:
                name = client_info[sock].get("name", "Unknown")
                del client_info[sock]
        if sock == streamer:
            streamer = None
            sendall({"type": "status", "active": False})
            print(f"Streamer {name} disconnected")
            sendall({"type": "chat", "name": "Server", "msg": f"{name} has left"})
        else:
            print(f"User {name} disconnected")
            sendall({"type": "chat", "name": "Server", "msg": f"{name} has left"})
        try:
            sock.close()
        except:
            pass

def run():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 5000))
    s.listen(5)
    print("StreamNest Server running on port 5000")
    print("Waiting for connections...")
    try:
        while True:
            c, a = s.accept()
            threading.Thread(target=handle, args=(c, a), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        for client in clients[:]:
            try:
                client.close()
            except:
                pass
        s.close()
        print("Server stopped")

if __name__ == "__main__":
    run()