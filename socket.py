import socket
import sys
import threading
import time

def listen(sock, peer_addr):
    """Listen for incoming messages"""
    print(f"[Listening] Waiting for messages from {peer_addr}...")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"\n[Received from {addr}]: {data.decode()}")
            print("Your message: ", end='', flush=True)
        except Exception as e:
            print(f"[Error receiving]: {e}")

def send_messages(sock, peer_addr):
    """Send messages to peer"""
    time.sleep(1)  # Give listener time to start
    
    # Send initial ping to punch hole
    for i in range(3):
        try:
            sock.sendto(b"PING", peer_addr)
            print(f"[Sent ping {i+1}] to {peer_addr}")
            time.sleep(0.5)
        except Exception as e:
            print(f"[Error sending ping]: {e}")
    
    print("\n=== Connection established! Start chatting ===\n")
    
    while True:
        try:
            msg = input("Your message: ")
            sock.sendto(msg.encode(), peer_addr)
        except KeyboardInterrupt:
            print("\n[Exiting...]")
            sys.exit(0)
        except Exception as e:
            print(f"[Error sending]: {e}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python p2p_test.py <your_port> <peer_ipv6:port>")
        print("Example: python p2p_test.py 5000 [2001:db8::1]:5000")
        sys.exit(1)
    
    local_port = int(sys.argv[1])
    peer_str = sys.argv[2]
    
    # Parse peer address
    if peer_str.startswith('['):
        # Format: [ipv6]:port
        peer_ip = peer_str[1:peer_str.rfind(']')]
        peer_port = int(peer_str[peer_str.rfind(':')+1:])
    else:
        print("Error: Use format [ipv6]:port")
        sys.exit(1)
    
    peer_addr = (peer_ip, peer_port)
    
    # Create UDP socket with IPv6
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to all interfaces
    sock.bind(('::', local_port))
    
    print(f"[Started] Listening on port {local_port}")
    print(f"[Target] Peer at {peer_addr}")
    
    # Start listener thread
    listener = threading.Thread(target=listen, args=(sock, peer_addr), daemon=True)
    listener.start()
    
    # Start sender
    send_messages(sock, peer_addr)

if __name__ == "__main__":
    main()