import socket
import sys
import threading
import time

def listen(sock, peer_addr, connected_event):
    """Listen for incoming messages"""
    print(f"[Listening] Waiting for messages from {peer_addr}...")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode()
            
            if message == "PING":
                print(f"\n[Received ping from {addr}]")
                # Send PONG back
                sock.sendto(b"PONG", addr)
                connected_event.set()
            elif message == "PONG":
                print(f"\n[Received pong from {addr}]")
                connected_event.set()
            else:
                print(f"\n[Received from {addr}]: {message}")
                if connected_event.is_set():
                    print("Your message: ", end='', flush=True)
        except Exception as e:
            print(f"\n[Error receiving]: {e}")

def send_messages(sock, peer_addr, connected_event):
    """Send messages to peer"""
    time.sleep(1)  # Give listener time to start
    
    # Send initial ping to punch hole
    print("\n[Establishing connection...]")
    for i in range(5):
        try:
            sock.sendto(b"PING", peer_addr)
            print(f"[Sent ping {i+1}/5] to {peer_addr}")
            time.sleep(1)
            
            if connected_event.wait(timeout=0.1):
                break
        except Exception as e:
            print(f"[Error sending ping]: {e}")
    
    if not connected_event.is_set():
        print("\n[Warning] No response from peer yet. You can still try sending messages.")
        print("[Info] Connection will establish once peer comes online.\n")
    else:
        print("\n=== Connection established! Start chatting ===\n")
    
    while True:
        try:
            msg = input("Your message: ")
            if msg.strip():  # Only send non-empty messages
                sock.sendto(msg.encode(), peer_addr)
                if not connected_event.is_set():
                    print("[Info] Message queued. Waiting for peer...")
        except KeyboardInterrupt:
            print("\n[Exiting...]")
            sys.exit(0)
        except Exception as e:
            print(f"[Error sending]: {e}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python socket.py <your_port> <peer_ipv6:port>")
        print("Example: python socket.py 5000 [2001:db8::1]:5000")
        sys.exit(1)
    
    local_port = int(sys.argv[1])
    peer_str = sys.argv[2]
    
    # Parse peer address with better error handling
    try:
        if peer_str.startswith('['):
            # Format: [ipv6]:port
            closing_bracket = peer_str.rfind(']')
            if closing_bracket == -1:
                raise ValueError("Missing closing bracket in IPv6 address")
            
            peer_ip = peer_str[1:closing_bracket]
            port_part = peer_str[closing_bracket+1:]
            
            if not port_part.startswith(':'):
                raise ValueError("Missing colon before port number")
            
            peer_port = int(port_part[1:])
        else:
            raise ValueError("Use format [ipv6]:port for IPv6 addresses")
    except Exception as e:
        print(f"[Error] Invalid peer address format: {e}")
        print("Example: [2001:db8::1]:5000")
        sys.exit(1)
    
    peer_addr = (peer_ip, peer_port)
    
    # Create UDP socket with IPv6
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('::', local_port))
    except Exception as e:
        print(f"[Error] Failed to create socket: {e}")
        sys.exit(1)
    
    print(f"[Started] Listening on port {local_port}")
    print(f"[Target] Peer at {peer_addr}")
    
    # Event to track connection status
    connected_event = threading.Event()
    
    # Start listener thread
    listener = threading.Thread(target=listen, args=(sock, peer_addr, connected_event), daemon=True)
    listener.start()
    
    # Start sender
    send_messages(sock, peer_addr, connected_event)

if __name__ == "__main__":
    main()