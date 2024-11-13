import hashlib
import bencodepy

def parse_torrent_file(filename):
    """ Parse a .torrent file and return the data """
    try:
        with open(filename, 'rb') as f:
            data = bencodepy.decode(f.read())
        return data
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return None

def get_info_hash(torrent_data):
    """ Generate info hash from torrent data (for tracker communication) """
    torrent_info = torrent_data[b'info']
    info_bytes = bencodepy.encode(torrent_info)
    return hashlib.sha1(info_bytes).hexdigest()
