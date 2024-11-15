import requests

def send_announce(tracker_url, info_hash, peer_id, port, event, downloaded=0, uploaded=0, remaining=0):
    params = {
        'info_hash': info_hash,
        'peer_id': peer_id,
        'port': port,
        'event': event,
        'downloaded': downloaded,
        'uploaded': uploaded,
        'remaining': remaining
    }
    response = requests.get(tracker_url, params=params)
    return response.json()
