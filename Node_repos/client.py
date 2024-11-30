import socket
import json
import hashlib
import os
import threading
import time
import bencodepy
from urllib.parse import urlparse

# Configuration section
PEER_DOWNLOAD_DIR = "Torrent-like-network-application/Node_repos/client_downloads"  # Directory to store downloaded pieces and state
TRACKER_IP = '192.168.77.147'  # Tracker IP address
TRACKER_PORT = 12340  # Tracker Port
PEER_PORT = 12341 # Peer Port for downloading/uploading
PEER_ID = "peer_1"  # Unique peer ID for this client
PIECE_LENGTH = 512 * 1024  # Default piece length (512 KB)
RETRY_COUNT = 3  # Number of retries for downloading a piece
TRACKER_ID = None
#Node db directory
directory_path = r'C:\Users\Administrator\Desktop\Assignment\Torrent-like-network-application\Node_repos\ClientDB'
# Create directory to store downloaded pieces and state
os.makedirs(PEER_DOWNLOAD_DIR, exist_ok=True)

def parse_torrent_file(torrent_file_path):
    try:
        # Read and decode the torrent file using bencode
        with open(torrent_file_path, 'rb') as f:
            torrent_data = bencodepy.decode(f.read())

        # Compute the info hash by hashing the Bencoded "info" dictionary
        info_hash = hashlib.sha1(bencodepy.encode(torrent_data[b"info"])).hexdigest()

        # Initialize metainfo dictionary
        metainfo = {
            "tracker": torrent_data[b"announce"].decode(),  # Get the tracker URL
            "info_hash": info_hash,  # Info hash
            "piece_length": torrent_data[b"info"][b"piece length"],  # Piece length
            "pieces": [torrent_data[b"info"][b"pieces"][i:i + 20].hex() for i in range(0, len(torrent_data[b"info"][b"pieces"]), 20)],  # List of pieces
        }

        # Handle multiple or single files
        if b"files" in torrent_data[b"info"]:
            # Multiple files
            metainfo["files"] = [
                {
                    "path": "/".join([part.decode() for part in file[b"path"]]),  # Join path components
                    "length": file[b"length"]
                }
                for file in torrent_data[b"info"][b"files"]
            ]
        else:
            # Single file
            metainfo["files"] = [{
                "path": torrent_data[b"info"][b"path"].decode(),  # Single file path
                "length": torrent_data[b"info"][b"length"]
            }]

        return metainfo

    except Exception as e:
        print(f"Error parsing torrent file: {e}")
        return None


# Function to announce to tracker and get peer list
def announce_to_tracker(metainfo, event="started"):
    global TRACKER_ID
    try:
        tracker_url = metainfo.get("tracker", "")
        if not tracker_url:
            raise ValueError("Tracker URL is missing in the metainfo.")
        
        parsed_url = urlparse(tracker_url)        
        # Ensure that the URL contains a valid netloc (hostname and port)
        if not parsed_url.hostname or not parsed_url.port:
            raise ValueError(f"Invalid tracker URL format: {tracker_url}. Expected 'http://hostname:port'.")
        tracker_ip = parsed_url.hostname
        tracker_port = parsed_url.port

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tracker_socket:
            tracker_socket.connect((tracker_ip, int(tracker_port)))
            request = {
                "announce": "Peer to tracker",
                "info_hash": metainfo["info_hash"],
                "peer_id": PEER_ID,  # Use the global peer ID
                "port": PEER_PORT,
                "event": event,
                "tracker_id": None,
                "available_pieces": load_available_pieces(metainfo) or []  # Send available pieces to tracker
            }

            # Include the tracker ID if available
            if TRACKER_ID is not None:
                request["tracker_id"] = TRACKER_ID

            tracker_socket.sendall(json.dumps(request).encode("utf-8"))
            response = tracker_socket.recv(4096).decode("utf-8")
            print(response)
            print()
            response_data = json.loads(response)

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

# Function to load the available pieces from the local repository
import os

def load_available_pieces(metainfo): 
    # Get all file names in the directory
    try:
        files_in_directory = os.listdir(directory_path)
    except FileNotFoundError:
        print("Directory not found.")
        return []
    except PermissionError:
        print("Permission denied to access the directory.")
        return [] 
    # Extract pieces (infohashes) from metainfo
    infohashes = set(metainfo.get('pieces', []))
    # Compare file names with infohashes and collect matches
    available_pieces = [file for file in files_in_directory if file in infohashes]
    return available_pieces


# Function to download a piece from a peer
def download_piece(peer, info_hash, piece_index, piece_length, retries=RETRY_COUNT):
    for attempt in range(retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as peer_socket:
                peer_socket.connect((peer["ip"], peer["port"]))
                request = {
                    "type": "piece_request",
                    "info_hash": info_hash,
                    "piece_index": piece_index,
                }
                peer_socket.sendall(json.dumps(request).encode("utf-8"))
                response = peer_socket.recv(4096)
                data = json.loads(response.decode("utf-8"))
                if data["status"] == "success":
                    return data["data"]
        except Exception as e:
            print(f"Error downloading piece {piece_index} from {peer['ip']} (attempt {attempt + 1}): {e}")
        time.sleep(1)  # Retry delay
    print(f"Failed to download piece {piece_index} after {retries} retries.")
    return None

# Verify the hash of a piece
def verify_piece(data, expected_hash):
    actual_hash = hashlib.sha1(data).hexdigest()
    return actual_hash == expected_hash

# Save the state of downloaded pieces
def save_download_state(info_hash, downloaded_pieces):
    state_file = f"{PEER_DOWNLOAD_DIR}/{info_hash}_state.json"
    with open(state_file, "w") as f:
        json.dump({"downloaded_pieces": downloaded_pieces}, f)

# Load the state of downloaded pieces
def load_download_state(info_hash):
    state_file = f"{PEER_DOWNLOAD_DIR}/{info_hash}_state.json"
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f).get("downloaded_pieces", [])
    return []

# # Rank peers based on latency (or other metrics)
# def rank_peers(peers):
#     return sorted(peers, key=lambda peer: peer.get("latency", float("inf")))

# Find the rarest pieces
def find_rarest_pieces(peers, total_pieces):
    piece_counts = [0] * total_pieces
    for peer in peers:
        for piece in peer.get("available_pieces", []):
            piece_counts[piece] += 1
    return sorted(range(total_pieces), key=lambda x: piece_counts[x])

# Serve uploaded pieces to other peers
def serve_upload_requests(info_hash):
    def handle_peer_connection(conn):
        try:
            data = conn.recv(4096).decode("utf-8")
            request = json.loads(data)
            if request["type"] == "piece_request" and request["info_hash"] == info_hash:
                piece_index = request["piece_index"]
                piece_path = f"{PEER_DOWNLOAD_DIR}/{info_hash}_pieces/{piece_index}"
                if os.path.exists(piece_path):
                    with open(piece_path, "rb") as piece_file:
                        response = {"status": "success", "data": piece_file.read()}
                else:
                    response = {"status": "error", "message": "Piece not found"}
                conn.sendall(json.dumps(response).encode("utf-8"))
        except Exception as e:
            print(f"Error handling peer connection: {e}")
        finally:
            conn.close()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PEER_PORT))  # Bind to a local port
    server.listen(5)
    print("Peer-to-peer upload server started. Seeding...")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_peer_connection, args=(conn,)).start()
    except KeyboardInterrupt:
        print("Seeding stopped by user.")
    finally:
        server.close()

# Seeding Loop
def start_seeding(metainfo):
    print("Seeding started...")
    try:
        while True:
            response = announce_to_tracker(metainfo, event="completed")
            if response and "failure reason" not in response:
                print("Seeding in progress... Announced to tracker.")
            else:
                print("Tracker announce failed during seeding.")
            time.sleep(30)  # Re-announce to tracker every 30 seconds
    except KeyboardInterrupt:
        announce_to_tracker(metainfo, event="stopped")
        print("Seeding terminated by user.")


# Download the torrent
def download_torrent(metainfo):
    pieces_dir = f"{PEER_DOWNLOAD_DIR}/{metainfo['info_hash']}_pieces"
    os.makedirs(pieces_dir, exist_ok=True)

    response = announce_to_tracker(metainfo, event="download")
    if not response or "failure reason" in response:
        print("Failed to announce to tracker.")
        return

    print(response)
    peers = [peer for peer in response["peers"] if peer["peer_id"] != PEER_ID]
    pieces = metainfo["pieces"]
    downloaded_pieces = load_download_state(metainfo["info_hash"])
    available_pieces = load_available_pieces(metainfo)
    lock = threading.Lock()

    def download_piece_worker(piece_index):
        nonlocal downloaded_pieces
        for peer in peers:
            if piece_index in downloaded_pieces:
                return  # Skip if already downloaded
            if piece_index in available_pieces:
                return  # Skip if have in database
            piece_data = download_piece(peer, metainfo["info_hash"], piece_index, PIECE_LENGTH)
            if piece_data and verify_piece(piece_data, pieces[piece_index]):
                lock.acquire()
                downloaded_pieces.append(piece_index)
                lock.release()
                with open(f"{pieces_dir}/{piece_index}", "wb") as piece_file:
                    piece_file.write(piece_data)
                save_download_state(metainfo["info_hash"], downloaded_pieces)
                print(f"Piece {piece_index} downloaded and verified.")
                break

    # Find rarest pieces and start threads for each
    rarest_pieces = find_rarest_pieces(peers, len(pieces))
    threads = []
    for piece_index in rarest_pieces:
        if piece_index not in downloaded_pieces:
            thread = threading.Thread(target=download_piece_worker, args=(piece_index,))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    print("Download complete.")
    # Send 'completed' event to tracker after download
    announce_to_tracker(metainfo, event="completed")

    # Start seeding after download completes
    start_seeding(metainfo)


# Example usage
if __name__ == "__main__":
    # Get user input for the torrent file path
    torrent_file_path = input("Please enter the path to the torrent file: ")
    # Parse the torrent file
    metainfo = parse_torrent_file(torrent_file_path)
    if metainfo is None:
        print("Failed to parse torrent file.")
        exit(1)

    # Start the upload server in a separate thread
    upload_thread = threading.Thread(target=serve_upload_requests, args=(metainfo["info_hash"],))
    upload_thread.daemon = True
    upload_thread.start()

    response = announce_to_tracker(metainfo, event="started")
    if not response or "failure reason" in response:
        print("Failed to announce to tracker.")
        exit(1)

    while True:
        print("\nOptions:")
        print("1. Download Torrent")
        print("2. Stop Seeding and Exit")
        choice = input("Choose an option: ")
        if choice == "1":
            download_torrent(metainfo)        
        elif choice == "2":
            print("Stopping seeding and exiting...")
            break
        else:
            print("Invalid option. Please choose 1 or 2.")

    
