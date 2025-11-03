import socket
import sys
import threading
import time

def listen(sock, peer_addr, connected_event):
    """Listen for incoming messages continuously"""
    print(f"[Listening] Waiting for messages on all interfaces...")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode()
            
            if message == "PING":
                print(f"\n[Received ping from {addr}]")
                sock.sendto(b"PONG", addr)
                if not connected_event.is_set():
                    print("[Connection established!]")
                    connected_event.set()
            elif message == "PONG":
                print(f"\n[Received pong from {addr}]")
                if not connected_event.is_set():
                    print("[Connection established!]")
                    connected_event.set()
            else:
                print(f"\n[{time.strftime('%H:%M:%S')}] {addr}: {message}")
                if connected_event.is_set():
                    print("Your message: ", end='', flush=True)
        except Exception as e:
            print(f"\n[Error receiving]: {e}")
            time.sleep(1)

def send_pings(sock, peer_addr, connected_event):
    """Continuously send pings to keep connection alive"""
    print("[Keep-alive] Starting ping service...")
    time.sleep(2)
    
    while True:
        try:
            if not connected_event.is_set():
                sock.sendto(b"PING", peer_addr)
                print(f"[{time.strftime('%H:%M:%S')}] Sent ping to {peer_addr}")
                time.sleep(5)
            else:
                sock.sendto(b"PING", peer_addr)
                time.sleep(30)
        except Exception as e:
            print(f"[Error sending ping]: {e}")
            time.sleep(10)

def send_messages(sock, peer_addr, connected_event):
    """Handle user input for sending messages"""
    print("\n[Ready] Type messages to send (Ctrl+C to exit)")
    print("=" * 50)
    
    while True:
        try:
            msg = input("Your message: ")
            if msg.strip():
                sock.sendto(msg.encode(), peer_addr)
                if not connected_event.is_set():
                    print("[Info] Message sent. Waiting for peer response...")
        except KeyboardInterrupt:
            print("\n\n[Shutdown] Closing server...")
            sys.exit(0)
        except EOFError:
            time.sleep(1)
        except Exception as e:
            print(f"[Error sending message]: {e}")

def get_user_input():
    """Get configuration from user via CLI menu"""
    print("\n" + "="*60)
    print(" "*15 + "P2P Chat Server Setup")
    print("="*60 + "\n")
    
    # Get local port
    while True:
        try:
            local_port = input("Enter your local port (e.g., 5000): ").strip()
            local_port = int(local_port)
            if 1024 <= local_port <= 65535:
                break
            else:
                print("[Error] Port must be between 1024 and 65535")
        except ValueError:
            print("[Error] Please enter a valid port number")
    
    print()
    
    # Get peer IPv6 address
    while True:
        peer_ip = input("Enter peer's IPv6 address (e.g., 2001:db8::1): ").strip()
        if peer_ip:
            # Basic validation
            if ':' in peer_ip:
                break
            else:
                print("[Error] Invalid IPv6 format. Must contain colons (:)")
        else:
            print("[Error] IPv6 address cannot be empty")
    
    # Get peer port
    while True:
        try:
            peer_port = input("Enter peer's port (e.g., 5000): ").strip()
            peer_port = int(peer_port)
            if 1024 <= peer_port <= 65535:
                break
            else:
                print("[Error] Port must be between 1024 and 65535")
        except ValueError:
            print("[Error] Please enter a valid port number")
    
    return local_port, peer_ip, peer_port

def main():
    # Check if arguments provided via command line
    if len(sys.argv) == 3:
        # Command line mode
        local_port = int(sys.argv[1])
        peer_str = sys.argv[2]
        
        try:
            if peer_str.startswith('['):
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
    else:
        # Interactive menu mode
        local_port, peer_ip, peer_port = get_user_input()
    
    peer_addr = (peer_ip, peer_port)
    
    # Create persistent UDP socket
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('::', local_port))
        print(f"\n{'='*60}")
        print(f"[Server Started] Listening on port {local_port}")
        print(f"[Target Peer] {peer_addr}")
        print(f"[Status] Server will stay online persistently")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"[Error] Failed to create socket: {e}")
        print(f"[Info] Make sure port {local_port} is not already in use")
        sys.exit(1)
    
    # Connection status
    connected_event = threading.Event()
    
    # Start listener thread
    listener = threading.Thread(target=listen, args=(sock, peer_addr, connected_event), daemon=True)
    listener.start()
    
    # Start ping thread for keep-alive
    pinger = threading.Thread(target=send_pings, args=(sock, peer_addr, connected_event), daemon=True)
    pinger.start()
    
    # Handle user input in main thread
    send_messages(sock, peer_addr, connected_event)

if __name__ == "__main__":
    main()