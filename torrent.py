import hashlib
import bencodepy

def parse_torrent_file(filename):
    """ Parse a .torrent file and return the data """
    try:
        with open(filename, 'rb') as f:
            data = bencodepy.decode(f.read())
        
        # Check if the essential 'info' key is in the data
        if b'info' not in data:
            print("Invalid torrent file: missing 'info' key.")
            return None
        
        return data
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
    """ Generate info hash from torrent data (for tracker communication) """
    if torrent_data is None:
        print("Torrent data is None. Please check the file and try again.")
        return None

    if b'info' not in torrent_data:
        print("Invalid torrent data: missing 'info' key.")
        return None

    torrent_info = torrent_data[b'info']
    info_bytes = bencodepy.encode(torrent_info)
    return hashlib.sha1(info_bytes).hexdigest()
