import bencodepy
# Define the torrent dictionary
torrent_data = {
    'announce': 'http://tracker1.example.com/announce',
    'info': {
        'piece length': 262144,
        'pieces': b'AAAAAAAAAAAAAAAAAAA',  # Example pieces data (20 bytes)
        'name': 'example_file1.txt',
        'length': 1234567
    }
}

# Encode the dictionary to bencoded data
encoded_data = bencodepy.encode(torrent_data)

# Save the bencoded data to a .torrent file
torrent_file = 'Sample/sample.torrent'
with open(torrent_file, 'wb') as f:
    f.write(encoded_data)

print(f'{torrent_file} created successfully!')
