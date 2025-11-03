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
            time.sleep(1)  # Prevent spam on persistent errors

def send_pings(sock, peer_addr, connected_event):
    """Continuously send pings to keep connection alive"""
    print("[Keep-alive] Starting ping service...")
    time.sleep(2)  # Initial delay
    
    while True:
        try:
            if not connected_event.is_set():
                # Send pings more frequently when not connected
                sock.sendto(b"PING", peer_addr)
                print(f"[{time.strftime('%H:%M:%S')}] Sent ping to {peer_addr}")
                time.sleep(5)
            else:
                # Send keep-alive pings less frequently when connected
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
            # Handle pipe closed
            time.sleep(1)
        except Exception as e:
            print(f"[Error sending message]: {e}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python socket1.py <your_port> <peer_ipv6:port>")
        print("Example: python socket1.py 5000 [2001:db8::1]:5000")
        sys.exit(1)
    
    local_port = int(sys.argv[1])
    peer_str = sys.argv[2]
    
    # Parse peer address
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
    
    peer_addr = (peer_ip, peer_port)
    
    # Create persistent UDP socket
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('::', local_port))
        print(f"\n{'='*50}")
        print(f"[Server Started] Listening on port {local_port}")
        print(f"[Target Peer] {peer_addr}")
        print(f"[Status] Server will stay online persistently")
        print(f"{'='*50}\n")
    except Exception as e:
        print(f"[Error] Failed to create socket: {e}")
        sys.exit(1)
    
    # Connection status
    connected_event = threading.Event()
    
    # Start listener thread (daemon=True so it closes with main)
    listener = threading.Thread(target=listen, args=(sock, peer_addr, connected_event), daemon=True)
    listener.start()
    
    # Start ping thread for keep-alive
    pinger = threading.Thread(target=send_pings, args=(sock, peer_addr, connected_event), daemon=True)
    pinger.start()
    
    # Handle user input in main thread
    send_messages(sock, peer_addr, connected_event)

if __name__ == "__main__":
    main()