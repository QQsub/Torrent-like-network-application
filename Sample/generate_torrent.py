import bencodepy
torrent_data = {
    'announce': 'http://tracker1.example.com/announce',
    'info': {
        'piece length': 262144,
        'pieces': b'AAAAAAAAAAAAAAAAAAA' * 2,
        'name': 'example_folder',
        'files': [
            {
                'length': 1234567,
                'path': ['example_file1.txt'], 
            },
            {
                'length': 2345678,
                'path': ['example_file2.txt'],
            },
            {
                'length': 3456789,
                'path': ['example_file3.txt'],
            }
        ]
    }
}

encoded_data = bencodepy.encode(torrent_data)

# Save the bencoded data to a .torrent file
torrent_file = 'Sample/sample.torrent'
with open(torrent_file, 'wb') as f:
    f.write(encoded_data)

print(f'{torrent_file} created successfully!')
