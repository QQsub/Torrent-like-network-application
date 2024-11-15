from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Tracker state
torrent_data = {}  # Tracks torrent info by info_hash
peers = {}         # Tracks peers for each torrent by info_hash

@app.route('/announce', methods=['GET'])
def announce():
    #Handle client requests to announce to the tracker.
    try:
        # Get client info
        info_hash = request.args.get('info_hash')
        peer_id = request.args.get('peer_id')
        ip = request.remote_addr
        port = int(request.args.get('port'))
        event = request.args.get('event', 'started')
        downloaded = int(request.args.get('downloaded', 0))
        uploaded = int(request.args.get('uploaded', 0))
        remaining = int(request.args.get('remaining', 0))

        # Check info_hash and peer_id exist
        if not info_hash or not peer_id or not port:
            return "Missing required parameters", 400

        # Handle events
        if info_hash not in peers:
            peers[info_hash] = []

        if event == 'started':
            # Add peer to the torrent
            peer_info = {'peer_id': peer_id, 'ip': ip, 'port': port}
            peers[info_hash].append(peer_info)
            torrent_data[info_hash] = torrent_data.get(info_hash, 0) + 1
        elif event == 'stopped':
            # Remove peer from the torrent
            peers[info_hash] = [p for p in peers[info_hash] if p['peer_id'] != peer_id]
        elif event == 'completed':
            # Maybe history/ logging function here????
            torrent_data[info_hash] = torrent_data.get(info_hash, 0)

        # Generate response to client
        response = {
            'interval': 1800,
            'tracker id': 'tracker1',
            'complete': len(peers.get(info_hash, [])),  # Total peer completed download
            'incomplete': 0,  # Current available leechers
            'peers': peers.get(info_hash, [])
        }
        return jsonify(response)
    
    except Exception as e:
        return {"failure reason": str(e)}, 500

@app.route('/scrape', methods=['GET'])
def scrape():
    try:
        info_hash = request.args.get('info_hash')
        if info_hash and info_hash in torrent_data:
            return jsonify({
                'info_hash': info_hash,
                'completed': torrent_data[info_hash],
                'peers': len(peers.get(info_hash, []))
            })
        else:
            return {"failure reason": "Torrent not found"}, 404
    except Exception as e:
        return {"failure reason": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)




# peers{"ahshjsds": [client1, client 3],  "anajksdji": [client2]}