import hashlib
import json
import os
import socket
import threading
import bencodepy
import signal
import sys
import zlib

########## Configuration ##########
IPV4_ADDRESS = '192.168.130.147'            # Tracker host machine address
TRACKER_PORT = 12340                        # Default port for the tracker
TRACKER_ID = "center_tracker"               # Center tracker id
COMPACT_FLAG = False                        # Compact flag for compacted peer list response
CONNECTION_TIMEOUT = 10                     # Default timeout for server connections (seconds)
WARNING_MESSAGE = "Some peers may be inactive."
# File to torrent lookup
TORRENTS = {
    "random_2MB.txt": "TORRENT_1.torrent",
    "random_4MB.txt": "TORRENT_1.torrent",
    "random_8MB.txt": "TORRENT_2.torrent",
}
# Dictionary to hold torrent data and peers information
torrent_data = {}                           # Tracks all available torrents by info_hash
peers = {}                                  # Tracks peers for each torrent by info_hash
TORRENT_DIR = 'Torrent-like-network-application/Tracker_repos/torrents'    # Directory to store the .torrent files
########## End of Configuration ##########

# Create the torrent directory if it doesn't exist
if not os.path.exists(TORRENT_DIR):
    os.makedirs(TORRENT_DIR)

# Load and parse a .torrent file to extract metadata
def parse_torrent_file(torrent_file_path):
    try:
        # Read and decode the torrent file using bencode
        with open(torrent_file_path, 'rb') as f:
            torrent_data = bencodepy.decode(f.read())

        # Compute the info hash by hashing the Bencoded "info" dictionary
        info_hash = hashlib.sha1(bencodepy.encode(torrent_data[b"info"])).hexdigest()

        # Initialize metainfo dictionary
        metainfo = {
            # "tracker": torrent_data[b"announce"].decode(),  # Get the tracker URL
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

# Generate a magnet link from info_hash
def generate_magnet_link(info_hash):
    return f"magnet:?xt=urn:btih:{info_hash.hex()}&dn=torrent&tr=http://{IPV4_ADDRESS}:{TRACKER_PORT}"

# Parse the announce request data
def parse_announce_data(data):
    # arse the announce message to extract the required parameters
    params = {}
    try:
        data_dict = json.loads(data)
        params['file_name'] = data_dict.get('file_name')
        params['peer_id'] = data_dict.get('peer_id')
        params['port'] = data_dict.get('port')
        params['ip'] = data_dict.get('ip')
        params['event'] = data_dict.get('event', 'started')
        params['compact'] = data_dict.get('compact', COMPACT_FLAG)
        params['downloaded_pieces'] = data_dict.get('downloaded_pieces', [])  # Pieces downloaded by the peer
        params['uploaded_pieces'] = data_dict.get('uploaded_pieces', [])  # Pieces uploaded by the peer
        params['available_pieces'] = data_dict.get('available_pieces', [])    # Already available pieces on peer
        params['tracker_id'] = data_dict.get('tracker_id')  # Extract the tracker ID
        return params
    except Exception as e:
        print(f"Error parsing announce data: {e}")
        return None

# Handle peer announcement
def handle_announce(conn, data, addr):
    params = parse_announce_data(data)
    
    if not params:
        response = {
            'failure reason': 'Invalid JSON data in the request.'
        }
        compressed_response = zlib.compress(json.dumps(response).encode('utf-8'))
        conn.sendall(compressed_response)
        return
    
    # Extract the parameters
    file_name = params['file_name']
    peer_id = params['peer_id']
    port = params['port']
    ip = addr[0]
    event = params['event']
    downloaded_pieces = params.get('downloaded_pieces', [])  # List of downloaded pieces
    uploaded_pieces = params.get('uploaded_pieces', [])     # List of uploaded pieces
    tracker_id = params.get('tracker_id')  # Optional tracker ID
    available_pieces = params.get('available_pieces', [])   #List of available pieces

    # Log the tracker_id 
    if tracker_id:
        print(f"Received tracker_id from peer: {tracker_id}")

    #Get interested torrent from file_name
    torrent_joined = TORRENTS[file_name]

    # if torrent_joined  == None:
    #     print(1)
    
    # Handle different events
    if event == "started":
        print(f"Peer {peer_id} connected to tracker.")        
        if torrent_joined not in peers:
            peers[torrent_joined] = []
        # Add peer to the list
        peer_info = {
            "peer_id": peer_id,
            "ip": ip,
            "port": port,
            "available_pieces": available_pieces,   #Store available pieces
            "downloaded_pieces": downloaded_pieces,  # Store downloaded pieces
            "uploaded_pieces": uploaded_pieces      # Store uploaded pieces
        }
        
        # Check if the peer already exists based on peer_id, ip, and port
        peer_exists = False
        for peer in peers[torrent_joined]:
            if peer["peer_id"] == peer_info["peer_id"] and peer["ip"] == peer_info["ip"] and peer["port"] == peer_info["port"]:
                peer["downloaded_pieces"] = peer_info["downloaded_pieces"]  # Update the downloaded_pieces
                peer["uploaded_pieces"] = peer_info["uploaded_pieces"]  # Update the downloaded_pieces
                peer_exists = True
                break

        # If peer doesn't exist, append the new peer
        if not peer_exists:
            peers[torrent_joined].append(peer_info)

    elif event == "download":
        print(f"Peer {peer_id} start downloading {file_name}")
        if torrent_joined not in peers:
            peers[torrent_joined] = []

        peer_info = {
            "peer_id": peer_id,
            "ip": ip,
            "port": port,
            "available_pieces": available_pieces,   #Store available pieces
            "downloaded_pieces": downloaded_pieces,  # Store downloaded pieces
            "uploaded_pieces": uploaded_pieces      # Store uploaded pieces
        }
        
        # Check if the peer already exists based on peer_id, ip, and port
        peer_exists = False
        for peer in peers[torrent_joined]:
            if peer["peer_id"] == peer_info["peer_id"] and peer["ip"] == peer_info["ip"] and peer["port"] == peer_info["port"]:
                peer["downloaded_pieces"] = peer_info["downloaded_pieces"]  # Update the downloaded_pieces
                peer["uploaded_pieces"] = peer_info["uploaded_pieces"]  # Update the downloaded_pieces
                peer_exists = True
                break

        # If peer doesn't exist, append the new peer
        if not peer_exists:
            peers[torrent_joined].append(peer_info)

    elif event == "stopped":
        # Remove from all torrent
        for torrent in peers.keys():
            for i in peers[torrent]:
                if i["peer_id"] == peer_id:
                    print(f"Peer {peer_id} stopped and quit the torrent: {torrent}.")

            peers[torrent] = [peer for peer in peers[torrent] if peer["peer_id"] != peer_id]

        # print(f"Peer {peer_id} stopped and quit the torrent: {torrent_joined}.")
        # # Remove peer from the list
        # peers[torrent_joined] = [peer for peer in peers[torrent_joined] if peer["peer_id"] != peer_id]
    
    elif event == "completed":
        print(f"Peer {peer_id} completed downloading/uploading {file_name}.")

    # Respond with tracker information 
    response = generate_announce_response(torrent_joined, peer_id)
    
    compressed_response_2 = zlib.compress(response.encode('utf-8'))
    conn.sendall(compressed_response_2)

# Generate the tracker response
def generate_announce_response(torrent_joined, current_peer_id):
    response_data = {}

    # If no peers for this torrent, return an error
    if torrent_joined not in peers:
        response_data['failure reason'] = 'No peers found for this torrent.'
        return json.dumps(response_data)

    # Optional Warning Message
    response_data['warning message'] = WARNING_MESSAGE
    # Add tracker_id
    response_data['tracker id'] = TRACKER_ID

    # Handle compact peer list
    if COMPACT_FLAG:
        compact_peers = []
        for peer in peers[torrent_joined]:
            if peer["peer_id"] != current_peer_id:
                ip = peer["ip"]
                port = peer["port"]
                peer_id = peer["peer_id"]
                compact_peers.append(f"{ip}:{port}:{peer_id}")  # Simplified representation
        response_data['peers'] = compact_peers
    else:
        response_data['peers'] = [peer for peer in peers[torrent_joined] if peer["peer_id"] != current_peer_id]

    # Include metadata of the torrent if started event
    response_data['metadata'] = parse_torrent_file(os.path.join(TORRENT_DIR, torrent_joined))
    return json.dumps(response_data)

# Start the tracker server
def start_tracker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IPV4_ADDRESS, TRACKER_PORT))
    server.listen(10)
    print(f"Tracker server started on port {TRACKER_PORT}")

    #while True:
    while True: 
        conn, addr = server.accept()
        print(f"Connection from {addr}")
        data = conn.recv(1024)
        # Decompress the data
        decompressed_data = zlib.decompress(data)
        #decode
        decoded_data = decompressed_data.decode('utf-8')
        if decoded_data:
            if "announce" in decoded_data:
                handle_announce(conn, decoded_data, addr)

        conn.close()
       

# Start the tracker server in a separate thread
server_thread = threading.Thread(target=start_tracker)
server_thread.start()

