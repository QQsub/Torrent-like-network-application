import socket
import json
import hashlib
import os
import threading
import time
import bencodepy
from urllib.parse import urlparse
import zlib

# Configuration section
PEER_DOWNLOAD_DIR = "Torrent-like-network-application/Client_repos"  # Directory of client
TRACKER_IP = '192.168.130.147'  # Tracker IP address
TRACKER_PORT = 12340  # Tracker Port
PEER_PORT = 12344 # Peer port for download/upload
PEER_ID = "peer_4"  # Unique peer ID for this client
PIECE_LENGTH = 512 * 1024  # Default piece length (512 KB)
RETRY_COUNT = 3  # Number of retries for downloading a piece
TRACKER_ID = None
COMPACT_FLAGS = False
# Thread-safe set to keep track of downloaded pieces
downloaded_pieces = set()
download_lock = threading.Lock()
# Thread-safe to keep track of uploaded pieces
uploaded_pieces = set()
upload_lock = threading.Lock()


# Function to announce to tracker and get peer list
def announce_to_tracker(file_name = None, event="started"):
    global TRACKER_ID
    try:
        if not file_name:
            raise ValueError("File name missing or not available")
        tracker_ip = TRACKER_IP
        tracker_port = TRACKER_PORT

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tracker_socket:
            tracker_socket.connect((tracker_ip, int(tracker_port)))
            request = {
                "announce": "Peer to tracker",
                "file_name": file_name,
                "peer_id": PEER_ID,  # Use the global peer ID
                "port": PEER_PORT,
                "event": event,
                "tracker_id": None,
                "available_pieces": load_available_pieces() or [],  # Send available pieces to tracker
                "downloaded_pieces": load_downloaded_pieces() or [],
                "uploaded_pieces": load_uploaded_pieces() or [],
                "compact": COMPACT_FLAGS
            }

            # Include the tracker ID if available
            if TRACKER_ID is not None:
                request["tracker_id"] = TRACKER_ID

            # Convert the request to a JSON string
            json_data = json.dumps(request)

            # Compress the JSON string using zlib
            compressed_data = zlib.compress(json_data.encode("utf-8"))

            # tracker_socket.sendall(json.dumps(request).encode("utf-8"))
            tracker_socket.sendall(compressed_data)

            # Fix here:
            response_data_recv = tracker_socket.recv(4096)
            # Decompress the data
            decompressed_data = zlib.decompress(response_data_recv)
            #decode
            response_data = json.loads(decompressed_data.decode('utf-8'))

            # Save tracker ID if present
            if "tracker id" in response_data:
                TRACKER_ID = response_data["tracker id"]

            # Log warning message if present
            if "warning message" in response_data:
                print(f"Warning from tracker: {response_data['warning message']}")

            return response_data

    except Exception as e:
        print(f"Error announcing to tracker: {e}")
        return None

def load_available_pieces():
    # List to store available pieces
    all_available_pieces = []

    # Iterate through all directories in the PEER_DOWNLOAD_DIR
    for dir_name in os.listdir(PEER_DOWNLOAD_DIR):
        dir_path = os.path.join(PEER_DOWNLOAD_DIR, dir_name)

        # Check if the directory is a valid piece directory (should contain "_pieces" in its name)
        if os.path.isdir(dir_path) and dir_name.endswith('_pieces'):
            # Iterate through the files in the directory
            for piece_file in os.listdir(dir_path):
                piece_path = os.path.join(dir_path, piece_file)

                # Check if the file is a valid piece file (could be based on file extension or hash check)
                if os.path.isfile(piece_path):
                    all_available_pieces.append(piece_file)  # Add piece hash to available pieces list

    return all_available_pieces

def load_downloaded_pieces():
    return list(downloaded_pieces)
def load_uploaded_pieces():
    return list(uploaded_pieces)


# Extract metadata for a specific file in a multi-file torrent.
def get_file_metadata(metadata, file_name):
    for file_info in metadata["files"]:
        if file_info["path"] == file_name:
            return file_info
    return None

 # Calculate the range of pieces that contain the requested file.

def get_file_piece_indices(metadata, file_metadata):
    piece_length = metadata["piece_length"]
    start_offset = 0

    # Calculate the starting byte offset for the file
    for f in metadata["files"]:
        if f["path"] == file_metadata["path"]:
            break
        start_offset += f["length"]

    end_offset = start_offset + file_metadata["length"]

    # Calculate start and end piece indices
    start_piece = start_offset // piece_length
    end_piece = (end_offset + piece_length - 1) // piece_length  # Inclusive range

    return list(range(start_piece, end_piece))

def check_existing_pieces(metadata, pieces_dir):
    piece_length = metadata["piece_length"]
    num_pieces = len(metadata["pieces"])
    existing_pieces = []
    # print(metadata)
    for piece_index in range(num_pieces):
        piece_path = os.path.join(pieces_dir, metadata["pieces"][piece_index])
        # print(piece_path)
        if os.path.exists(piece_path):
            # Validate the size of the piece
            piece_size = os.path.getsize(piece_path)
            if piece_size == piece_length or (piece_index == num_pieces - 1 and piece_size <= piece_length):
                existing_pieces.append(piece_index)
            else:
                print(f"Invalid piece size for piece {piece_index}.")
    
    return existing_pieces

def merge_pieces_for_file(metadata, file_metadata, pieces_dir, output_file_name):
    # Combine pieces to reconstruct the requested file.
    piece_length = metadata["piece_length"]
    file_length = file_metadata["length"]
    start_offset = 0

    # Calculate the starting byte offset for the file
    for f in metadata["files"]:
        if f["path"] == file_metadata["path"]:
            break
        start_offset += f["length"]

    end_offset = start_offset + file_length
    start_piece = start_offset // piece_length
    end_piece = (end_offset + piece_length - 1) // piece_length

    # Ensure the output directory exists
    if not os.path.exists(PEER_DOWNLOAD_DIR):
        os.makedirs(PEER_DOWNLOAD_DIR)

    # Construct full output file path
    output_file = os.path.join(PEER_DOWNLOAD_DIR, output_file_name)

    with open(output_file, 'wb') as output:
        for piece_index in range(start_piece, end_piece):
            piece_path = os.path.join(pieces_dir, metadata["pieces"][piece_index])
            with open(piece_path, 'rb') as piece_file:
                piece_data = piece_file.read()

                # Calculate start and end bytes for this piece
                piece_start = max(0, start_offset - (piece_index * piece_length))
                piece_end = min(piece_length, end_offset - (piece_index * piece_length))

                # Write the relevant portion to the output file
                output.write(piece_data[piece_start:piece_end])

    print(f"File successfully reconstructed: {output_file}")

def download_piece(piece_index, peer, metadata, pieces_dir):
    try:
        # Retrieve peer IP and port
        peer_ip = peer["ip"]
        peer_port = peer["port"]
        
        # Define the piece length and the start byte for the piece
        piece_length = metadata["piece_length"]
        
        # Calculate the start and end byte for the requested piece
        start_byte = piece_index * piece_length
        end_byte = start_byte + piece_length
        
        # Create the file path to save the downloaded piece
        piece_filename = os.path.join(pieces_dir, f"{metadata["pieces"][piece_index]}")
        
        # Create a socket connection to the peer
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer_ip, peer_port))

            # Send a request to the peer to get the specific piece
            request = f"GET piece {piece_index} {start_byte} {end_byte}\n"
            s.send(request.encode())
            print(f"Requesting piece {piece_index} from {peer_ip}:{peer_port}")

            # Receive the piece data from the peer
            piece_data = b""
            while len(piece_data) < piece_length:
                data = s.recv(1024)
                if not data:
                    break
                piece_data += data

            # Ensure the piece data is the correct length
            if len(piece_data) != piece_length:
                print(f"Error: Incomplete piece received. Expected {piece_length} bytes, got {len(piece_data)} bytes.")
                return False

            # Write the downloaded piece data to a file
            with open(piece_filename, "wb") as f:
                f.write(piece_data)

        print(f"Piece {piece_index} successfully downloaded.")
        return True

    except Exception as e:
        print(f"Error downloading piece {piece_index} from {peer_ip}:{peer_port}: {e}")
        return False

def download_piece_threaded(piece_index, peer, metadata, pieces_dir):
    global downloaded_pieces
    if piece_index in downloaded_pieces:
        return  # No need to download if already downloaded

    # Try downloading from the peer
    if download_piece(piece_index, peer, metadata, pieces_dir):
        with download_lock:  # Ensure thread-safe access to shared downloaded_pieces set
            downloaded_pieces.add(metadata["pieces"][piece_index])

# Peer-side function to handle incoming requests for pieces
def handle_peer_connection(client_socket, pieces_dir, metadata):
    try:
        # Receive the request from the client
        request = client_socket.recv(1024).decode()
        print(f"Received request: {request}")
        
        # Parse the request (e.g., GET piece {index} {start_byte} {end_byte})
        if request.startswith("GET piece"):
            parts = request.split()
            piece_index = int(parts[2])
            start_byte = int(parts[3])
            end_byte = int(parts[4])
            
            # Validate the requested piece index
            pieces_dir = f"{PEER_DOWNLOAD_DIR}/{metadata['info_hash']}_pieces"
            os.makedirs(pieces_dir, exist_ok=True)

            piece_filename = os.path.join(pieces_dir, f'{metadata["pieces"][piece_index]}')
            if not os.path.exists(piece_filename):
                print(f"Error: Piece {piece_index} not available.")
                client_socket.send(b"ERROR: Piece not available\n")
                return
            
            # Read the requested piece from the file
            with open(piece_filename, "rb") as f:
                piece_data = f.read()
            
            # Send the piece data back to the client
            client_socket.send(piece_data)
            print(f"Sent piece {piece_index} to client.")

            # Add it to uploaded pieces
            with upload_lock:
                uploaded_pieces.add(metadata["pieces"][piece_index])
        
        else:
            client_socket.send(b"ERROR: Invalid request format\n")
    
    except Exception as e:
        print(f"Error handling request: {e}")
        client_socket.send(b"ERROR: Server error\n")
    
    finally:
        client_socket.close()

# Function to start the peer server (server listening for incoming connections)
def start_peer_server(peer_ip, peer_port, pieces_dir, metadata, stop_event):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((peer_ip, peer_port))
        s.listen(10)
        print(f"Peer server listening on {peer_ip}:{peer_port}...")

        while not stop_event.is_set():  # Keep running until stop_event is set
            try:
                # Check if stop_event is set before accepting connections
                if stop_event.is_set():
                    print("Stopping peer server...")
                    break
                
                # Accept incoming client connections
                client_socket, _ = s.accept()
                print(f"Connection established with client.")
                
                # Handle the client's request in a new thread
                client_thread = threading.Thread(
                    target=handle_peer_connection, 
                    args=(client_socket, pieces_dir, metadata)
                )
                client_thread.daemon = True  # Ensure threads exit when main program exits
                client_thread.start()
            except Exception as e:
                if not stop_event.is_set():  # If the server is shutting down, ignore errors
                    print(f"Error handling connection: {e}")

# Download the torrent
def download_from_torrent(file_name, response):
    if not response or "failure reason" in response:
        print(f"Failed to announce to tracker: {response.get('failure reason')}")
        return

    metadata = response["metadata"]
    peers = response["peers"]
    pieces_dir = f"{PEER_DOWNLOAD_DIR}/{metadata['info_hash']}_pieces"
    os.makedirs(pieces_dir, exist_ok=True)

    # Get metadata for the requested file
    file_metadata = get_file_metadata(metadata, file_name)
    # print(response)
    if not file_metadata:
        print(f"File '{file_name}' not found in torrent metadata.")
        return

    # Calculate piece indices for the requested file
    file_piece_indices = get_file_piece_indices(metadata, file_metadata)
    print(f"File '{file_name}' spans pieces: {file_piece_indices}")

    # Check existing pieces
    existing_pieces = check_existing_pieces(metadata, pieces_dir)
    relevant_existing_pieces = set(existing_pieces).intersection(file_piece_indices)
    print(f"Existing pieces for '{file_name}': {len(relevant_existing_pieces)}/{len(file_piece_indices)}")

    # If all pieces are available, merge the file
    if len(relevant_existing_pieces) == len(file_piece_indices):
        print(f"All pieces for '{file_name}' are already downloaded. Merging...")
        merge_pieces_for_file(metadata, file_metadata, pieces_dir, file_name)
        return

    # Identify missing pieces
    missing_pieces = list(set(file_piece_indices) - relevant_existing_pieces)
    print(f"Missing pieces for '{file_name}': {missing_pieces}")


    # Download missing pieces
    threads = []
    for piece_index in missing_pieces:
        for peer in peers:
            if metadata["pieces"][piece_index] in peer["available_pieces"] and piece_index not in relevant_existing_pieces:
                thread = threading.Thread(target=download_piece_threaded, args=(piece_index, peer, metadata, pieces_dir))
                threads.append(thread)
                thread.start()
                break
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Update relevant_existing_pieces after threads are done
    existing_pieces = check_existing_pieces(metadata, pieces_dir)
    relevant_existing_pieces = set(existing_pieces).intersection(file_piece_indices)

    # Merge the file if all pieces are downloaded
    if len(relevant_existing_pieces) == len(file_piece_indices):
        print(f"All pieces downloaded for '{file_name}'. Merging...")
        merge_pieces_for_file(metadata, file_metadata, pieces_dir, file_name)
    else:
        print(f"Download incomplete for '{file_name}'. Missing pieces remain.")

def choose_file():
    while True:
        print("Which file are you interested in:")
        print("1. random_2MB.txt")
        print("2. random_3MB.txt")
        print("3. random_4MB.txt")
        choice = input("Choose an option: ")
        if choice == "1":
            return "random_2MB.txt"   
        elif choice == "2":
            return "random_4MB.txt"
        elif choice == "3":
            return "random_8MB.txt"   
        else:
            print("Invalid option. Please choose 1, 2 or 3.")
            continue
    return ""

def choose_option():
    while True:
        print("What do you want to do")
        print("0. Just annouce tracker you are online")
        print("1. Download from others")
        print("2. Stop and exit from network")
        choice = input("Choose an option: ")
        if choice == "0":
            return "Announce"
        elif choice == "1":
            return "Download"  
        elif choice == "2":
            return "Exit"
        else:
            print("Invalid option. Please choose 0, 1 or 2.")
            continue
    return ""

def main():
    stop_event = threading.Event()  # Event to signal the peer server to stop
    connected = False
    Online = False
    while True:
        option = choose_option()
        
        if option != "Exit":
            file_name = choose_file()    
        if option == "Announce":
            response = announce_to_tracker(file_name, event = "started")
            # Start the peer server in a separate thread
            peer_thread = threading.Thread(target=start_peer_server, args=("0.0.0.0", PEER_PORT, PEER_DOWNLOAD_DIR, response["metadata"], stop_event))
            peer_thread.daemon = True
            peer_thread.start()
            connected = True
            Online = True
        if option == "Download":
            # First online
            if (Online == False):
                response = announce_to_tracker(file_name, event = "started")
                # Start the peer server in a separate thread
                peer_thread = threading.Thread(target=start_peer_server, args=("0.0.0.0", PEER_PORT, PEER_DOWNLOAD_DIR, response["metadata"], stop_event))
                peer_thread.daemon = True
                peer_thread.start()
                connected = True
                Online = True
                
            response = announce_to_tracker(file_name, event="download")           
            download_from_torrent(file_name, response)
            response = announce_to_tracker(file_name, event="completed")      
        elif option == "Exit":
            if connected:
                response = announce_to_tracker(file_name, event="stopped")
                # download_from_torrent(file_name, response)

            # Signal the peer server to stop and wait for it to exit
            stop_event.set()
            time.sleep(1)  # Ensure the server has time to shut down
            break

if __name__ == "__main__":
    main()


    
