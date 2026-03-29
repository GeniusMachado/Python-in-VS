import socket
import itertools
import threading

# Define the backend servers (address, port)
BACKEND_SERVERS = [
    ("127.0.0.1", 8000),
    ("127.0.0.1", 8001),
    # Add more servers as needed
]

# Round-robin iterator for cycling through servers
server_cycle = itertools.cycle(BACKEND_SERVERS)

def forward_connection(client_sock, client_addr):
    """Forwards client requests to the next backend server."""
    try:
        # Choose the next server using round robin
        server_host, server_port = next(server_cycle)
        print(f"Received connection from {client_addr}. Forwarding to {server_host}:{server_port}")

        # Connect to the backend server
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((server_host, server_port))

        # Forward data between client and server
        while True:
            client_data = client_sock.recv(1024)
            if not client_data:
                break
            server_sock.sendall(client_data)
            server_data = server_sock.recv(1024)
            if not server_data:
                break
            client_sock.sendall(server_data)

    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        if client_sock:
            client_sock.close()
        if server_sock:
            server_sock.close()

def start_load_balancer(lb_host='127.0.0.1', lb_port=8080):
    """Starts the load balancer server."""
    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allows the socket to be reused immediately after it's closed
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        # Bind to the specified port
        sock.bind((lb_host, lb_port))
        # Listen for incoming connections (max 5 queued)
        sock.listen(5)
        print(f"Load balancer listening on {lb_host}:{lb_port}")

        while True:
            # Accept incoming connections
            client_sock, client_addr = sock.accept()
            # Handle each connection in a new thread for concurrency
            client_thread = threading.Thread(target=forward_connection, args=(client_sock, client_addr))
            client_thread.start()

    except KeyboardInterrupt:
        print("Load balancer stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    # Ensure you have backend servers running on ports 8000 and 8001 (e.g., simple Python HTTP servers)
    # Example: python3 -m http.server 8000 & python3 -m http.server 8001 &
    start_load_balancer()
