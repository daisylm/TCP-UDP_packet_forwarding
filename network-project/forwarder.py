#!/usr/bin/env python3
"""
Packet Forwarder and Logger for Network Project
Listens on Tracker VM and forwards packets between Sender and Receiver
"""

import socket
import threading
import time
import sys
from datetime import datetime

# Configuration
SENDER_IP = "192.168.56.10"
RECEIVER_IP = "192.168.57.30"
TRACKER_IP_SENDER_SIDE = "192.168.56.20"
TRACKER_IP_RECEIVER_SIDE = "192.168.57.20"

# Ports for our services
UDP_FORWARD_PORT = 5000
TCP_FORWARD_PORT = 5001
LOG_FILE = "/vagrant/packet_log.txt"

def log_message(message):
    """Log messages to file and stdout"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def udp_forwarder():
    """Forward UDP packets from Sender to Receiver and log them"""
    log_message("Starting UDP forwarder...")
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to tracker's sender-side interface
    sock.bind((TRACKER_IP_SENDER_SIDE, UDP_FORWARD_PORT))
    
    log_message(f"UDP forwarder listening on {TRACKER_IP_SENDER_SIDE}:{UDP_FORWARD_PORT}")
    
    while True:
        try:
            # Receive from sender
            data, addr = sock.recvfrom(1024)
            log_message(f"UDP from {addr}: {len(data)} bytes")
            
            # Forward to receiver
            sock.sendto(data, (RECEIVER_IP, UDP_FORWARD_PORT))
            log_message(f"UDP forwarded to {RECEIVER_IP}:{UDP_FORWARD_PORT}")
            
        except Exception as e:
            log_message(f"UDP Error: {e}")
            time.sleep(1)

def tcp_forwarder():
    """Forward TCP connections from Sender to Receiver and log them"""
    log_message("Starting TCP forwarder...")
    
    # Create TCP server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to tracker's sender-side interface
    server.bind((TRACKER_IP_SENDER_SIDE, TCP_FORWARD_PORT))
    server.listen(5)
    
    log_message(f"TCP forwarder listening on {TRACKER_IP_SENDER_SIDE}:{TCP_FORWARD_PORT}")
    
    while True:
        try:
            # Accept connection from sender
            sender_socket, sender_addr = server.accept()
            log_message(f"TCP connection from {sender_addr}")
            
            # Connect to receiver
            receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            receiver_socket.connect((RECEIVER_IP, TCP_FORWARD_PORT))
            log_message(f"TCP connected to {RECEIVER_IP}:{TCP_FORWARD_PORT}")
            
            # Create two threads for bidirectional forwarding
            def forward(src, dst, direction):
                try:
                    while True:
                        data = src.recv(1024)
                        if not data:
                            break
                        log_message(f"TCP {direction}: {len(data)} bytes")
                        dst.send(data)
                except:
                    pass
                finally:
                    src.close()
                    dst.close()
            
            # Start forwarding threads
            threading.Thread(target=forward, 
                           args=(sender_socket, receiver_socket, "sender→receiver"),
                           daemon=True).start()
            threading.Thread(target=forward,
                           args=(receiver_socket, sender_socket, "receiver→sender"),
                           daemon=True).start()
            
        except Exception as e:
            log_message(f"TCP Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    log_message("=" * 60)
    log_message("Packet Forwarder and Logger Started")
    log_message(f"Sender: {SENDER_IP}, Receiver: {RECEIVER_IP}")
    log_message("=" * 60)
    
    # Start UDP forwarder in a thread
    udp_thread = threading.Thread(target=udp_forwarder, daemon=True)
    udp_thread.start()
    
    # Start TCP forwarder in a thread
    tcp_thread = threading.Thread(target=tcp_forwarder, daemon=True)
    tcp_thread.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_message("Shutting down forwarder...")
        sys.exit(0)