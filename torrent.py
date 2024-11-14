import hashlib
import bencodepy
import requests

max_retries = 3     # Number of retries
timeout= 2          # Timeout
def parse_torrent_file(filename):
    #Parse a .torrent file and return the data.
    try:
        with open(filename, 'rb') as f:
            data = bencodepy.decode(f.read())        
        if b'info' not in data:
            raise ValueError("Invalid torrent file: missing 'info' key.")
        
         # Get announce URL (the tracker URL)
        announce_url = data.get(b'announce', None)
        if announce_url:
            announce_url = announce_url.decode('utf-8')
        else:
            print("No announce URL found in the torrent file.")

        return data, announce_url
        
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    except bencodepy.BencodeDecodeError:
        print(f"Error decoding torrent file: {filename}")
        return None
    except Exception as e:
        print(f"Unexpected error reading file {filename}: {e}")
        return None

def get_info_hash(torrent_data):
    # Generate info hash (SHA1) from torrent data.
    if torrent_data is None:
        raise ValueError("Torrent data is None. Please check the file and try again.")   
    if b'info' not in torrent_data:
        raise ValueError("Invalid torrent data: missing 'info' key.")
    
    torrent_info = torrent_data[b'info']
    info_bytes = bencodepy.encode(torrent_info)
    return hashlib.sha1(info_bytes).hexdigest()

def fetch_torrent_file(info_hash, tracker_url):
    # Fetch the .torrent file using the info_hash and tracker URL.
    params = {'info_hash': info_hash.encode('latin1')}
    headers = {
        'User-Agent': 'Torrent Client'
    }   
    for attempt in range(max_retries):
        try:
            response = requests.get(tracker_url, params=params, headers=headers, timeout=timeout)
            if response.status_code == 200:
                print("Successfully fetched torrent file from tracker.")
                return response.content  # Return torrent data as bytes
            else:
                print(f"Attempt {attempt + 1}: Received status code {response.status_code}")
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
    raise Exception("Failed to fetch torrent file after multiple attempts")

def parse_metainfo(torrent_data):
    # Parse .torrent data and retrieve metainfo details like piece length, pieces, and file details.
    if b'info' not in torrent_data:
        raise ValueError("Invalid torrent data: missing 'info' key.")
    
    info = torrent_data[b'info']
    piece_length = info.get(b'piece length', None)
    pieces = info.get(b'pieces', None)
    files = []

    if b'files' in info:
        # Multi-file torrent
        for file in info[b'files']:
            path = [component.decode('utf-8') for component in file[b'path']]
            length = file[b'length']
            files.append({'path': path, 'length': length})
    else:
        # Single-file torrent
        name = info.get(b'name', b'Unnamed File').decode('utf-8')
        length = info.get(b'length', 0)
        files.append({'path': [name], 'length': length})

    return {
        'piece_length': piece_length,
        'pieces': pieces,
        'files': files
    }
