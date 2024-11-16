import requests
import random
import hashlib
from Metadata import torrent
from Metadata import magnet

class client:
    #initialize the client
    def __init__(self, torrent_file, peer_id, port):
        self.tracker_url = None
        self.torrent_file = torrent_file
        self.peer_id = peer_id
        self.port = port
        self.downloaded = 0
        self.uploaded = 0
        self.remaining = 0 
        self.info_hash = None
        self.pieces = {}
        self.peers = []
        self.files = []
        self.piece_length = 0
        self.piece_hashes = []
        self.parse_metadata()

    def parse_metadata(self):
        #Get torrent_data and tracker url
        torrent_data, announce_url = torrent.parse_torrent_file(self.torrent_file)
        #Check for important fields
        if not torrent_data or not announce_url:
            raise ValueError("Failed to parse torrent file or announce URL missing.")
        #Set torrent data and tracker url for client
        self.torrent_data = torrent_data
        self.tracker_url = announce_url
        #Generate client info hash
        self.info_hash = torrent.get_info_hash(torrent_data)
        # Parse metainfo details
        meta_info = torrent.parse_metainfo(torrent_data)
        self.piece_length = meta_info['piece_length']
        self.pieces = meta_info['pieces']
        self.files = meta_info['files']
        # Calculate remaining pieces
        self.piece_hashes = [
            self.pieces[i:i+20] for i in range(0, len(self.pieces), 20)
        ]
        self.remaining = len(self.piece_hashes)

    #Send signal to tracker
    def send_announce(tracker_url, info_hash, peer_id, port, event, downloaded=0, uploaded=0, remaining= 0):
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
    
    #Start download
    def start_download(self):
        response = self.send_announce(
            self.tracker_url,
            self.info_hash,
            self.peer_id,
            self.port,
            'started',
            self.downloaded,
            self.uploaded,
            self.remaining
        )
        #Check for tracker response
        if not response:
            print("Failed to get a response from the tracker.")
            return
        #Get peer in torrent from tracker
        self.peers = response.get('peers', [])
        print(f"Found {len(self.peers)} peers.")
        self.download()

    def download(self):
        #Step 1: get pieces that are missing in self

        #Step 2: Ask for available piece from peer

        #Step 3: 


  


