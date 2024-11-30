import hashlib
import json
import os
import socket
import threading
import bencodepy

########## Configuration ##########
IPV4_ADDRESS = '192.168.77.147'            # Tracker host machine address
TRACKER_PORT = 12340                        # Default port for the tracker
TRACKER_ID = "center_tracker"               # Center tracker id
COMPACT_FLAG = False                        # Compact flag for compacted peer list response
CONNECTION_TIMEOUT = 10                     # Default timeout for server connections (seconds)
WARNING_MESSAGE = 'Some peers may be inactive.'
# Dictionary to hold torrent data and peers information
torrent_data = {}                           # Tracks all available torrents by info_hash
peers = {}                                  # Tracks peers for each torrent by info_hash
TORRENT_DIR = 'Torrent-like-network-application/Tracker_repos/torrents'    # Directory to store the .torrent files
########## End of Configuration ##########


# Create the torrent directory if it doesn't exist
if not os.path.exists(TORRENT_DIR):
    os.makedirs(TORRENT_DIR)

torrent_file_path = r"C:\Users\Administrator\Desktop\Assignment\Torrent-like-network-application\Sample\sample.torrent"
# Load and parse a .torrent file to extract metadata
def load_torrent_metadata(torrent_file_path):
    try:
        # Read the torrent file and decode it
        with open(torrent_file_path, 'rb') as f:
            data = bencodepy.decode(f.read())
        
        # Compute the info_hash
        info_hash = hashlib.sha1(bencodepy.encode(data[b'info'])).digest()

        # Handle single file or multiple files
        files = []
        if b'files' in data[b'info']:
            files = data[b'info'][b'files']
        else:
            # Single file, ensure it's in the same format (list)
            files = [{"length": data[b'info'][b'length'], "path": [data[b'info'][b'name']]}]

        # Generate the magnet link
        magnet_link = generate_magnet_link(info_hash)
        
        # Ensure TORRENT_DIR exists
        if not os.path.exists(TORRENT_DIR):
            os.makedirs(TORRENT_DIR)

        # Save the torrent file in the appropriate directory based on info_hash
        torrent_file_name = f"{info_hash.hex()}.torrent"
        torrent_file_path = os.path.join(TORRENT_DIR, torrent_file_name)
        with open(torrent_file_path, 'wb') as f_torrent:
            f_torrent.write(bencodepy.encode(data))
        
        # Update the torrent_data dictionary
        torrent_data[info_hash] = {
            'torrent_file_path': torrent_file_path,
            'magnet_link': magnet_link,
            'files': files,
            'downloaded_pieces': {},  # To track downloaded pieces for peers
        }
        
        print(f"Torrent file saved: {torrent_file_name}")
    except Exception as e:
        print(f"Error loading torrent file: {e}")

# Generate a magnet link from info_hash
def generate_magnet_link(info_hash):
    return f"magnet:?xt=urn:btih:{info_hash.hex()}&dn=torrent&tr=http://{IPV4_ADDRESS}:{TRACKER_PORT}"

# Parse the announce request data
def parse_announce_data(data):
    """ Parse the announce message to extract the required parameters """
    params = {}
    try:
        data_dict = json.loads(data)
        params['info_hash'] = data_dict.get('info_hash')
        params['peer_id'] = data_dict.get('peer_id')
        params['port'] = data_dict.get('port')
        params['ip'] = data_dict.get('ip')
        params['event'] = data_dict.get('event', 'started')
        params['downloaded'] = data_dict.get('downloaded', 0)
        params['uploaded'] = data_dict.get('uploaded', 0)
        params['compact'] = data_dict.get('compact', COMPACT_FLAG)
        params['downloaded_pieces'] = data_dict.get('downloaded_pieces', [])  # Pieces downloaded by the peer
        params['available_pieces'] = data_dict.get('available_pieces', [])    # ALready available pieces on peer
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
        conn.sendall(json.dumps(response).encode('utf-8'))
        return
    
    # Extract the parameters
    info_hash = params['info_hash']
    peer_id = params['peer_id']
    port = params['port']
    ip = addr[0]
    event = params['event']
    downloaded = params['downloaded']
    uploaded = params['uploaded']
    downloaded_pieces = params.get('downloaded_pieces', [])  # List of downloaded pieces
    tracker_id = params.get('tracker_id')  # Optional tracker ID
    available_pieces = params.get('available_pieces', [])   #List of available pieces
    # Log the tracker_id 
    if tracker_id:
        print(f"Received tracker_id from peer: {tracker_id}")
        
    # Handle different events
    if event == "started" or event == 'download':
        print(f"Peer {peer_id} started downloading {info_hash}.")
        if info_hash not in peers:
            peers[info_hash] = []

        # Add peer to the list
        peer_info = {
            "peer_id": peer_id,
            "ip": ip,
            "port": port,
            "downloaded_pieces": downloaded_pieces  # Store downloaded pieces
        }
        
        # Check if the peer already exists based on peer_id, ip, and port
        peer_exists = False
        for peer in peers[info_hash]:
            if peer["peer_id"] == peer_info["peer_id"] and peer["ip"] == peer_info["ip"] and peer["port"] == peer_info["port"]:
                peer["downloaded_pieces"] = peer_info["downloaded_pieces"]  # Update the downloaded_pieces
                peer_exists = True
                break

        # If peer doesn't exist, append the new peer
        if not peer_exists:
            peers[info_hash].append(peer_info)
    
    elif event == "stopped":
        print(f"Peer {peer_id} stopped downloading {info_hash}.")
        # Remove peer from the list
        peers[info_hash] = [peer for peer in peers[info_hash] if peer["peer_id"] != peer_id]
    
    elif event == "completed":
        print(f"Peer {peer_id} completed downloading {info_hash}.")
        # Mark peer as completed
        for peer in peers[info_hash]:
            if peer["peer_id"] == peer_id:
                peer["completed"] = True  # You can add a 'completed' flag

    # Respond with tracker information
    response = generate_announce_response(info_hash)
    conn.sendall(response.encode('utf-8'))

# Generate the tracker response
def generate_announce_response(info_hash):
    response_data = {}

    # If no peers for this info_hash, return an error
    if info_hash not in peers:
        response_data['failure reason'] = 'No peers found for this torrent.'
        return json.dumps(response_data)

    peer_list = peers[info_hash]

    # Optional Warning Message
    response_data['warning message'] = WARNING_MESSAGE

    # Add tracker_id
    response_data['tracker id'] = TRACKER_ID

    # Handle compact peer list
    if COMPACT_FLAG:
        compact_peers = []
        for peer in peer_list:
            ip = peer["ip"]
            port = peer["port"]
            peer_id = peer["peer_id"]
            compact_peers.append(f"{ip}:{port}:{peer_id}")  # Simplified representation
        response_data['peers'] = compact_peers
    else:
        response_data['peers'] = peer_list

    # Include multi-file torrent details
    if info_hash in torrent_data:
        torrent_info = torrent_data[info_hash]
        response_data['magnet_link'] = torrent_info['magnet_link']
        response_data['files'] = torrent_info['files']  # Multi-file information

    print(response_data)
    return json.dumps(response_data)

# Start the tracker server
def start_tracker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IPV4_ADDRESS, TRACKER_PORT))
    server.listen(10)
    print(f"Tracker server started on port {TRACKER_PORT}")

    while True:
        conn, addr = server.accept()
        print(f"Connection from {addr}")
        data = conn.recv(1024).decode('utf-8')
        if data:
            if "announce" in data:
                handle_announce(conn, data, addr)

        conn.close()

# Start the tracker server in a separate thread
server_thread = threading.Thread(target=start_tracker)
server_thread.start()
