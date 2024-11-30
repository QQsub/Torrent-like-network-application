import hashlib
import bencodepy
import os
from pathlib import Path

# Configuration
TRACKER_URL = "http://192.168.77.147:12340"  # Tracker URL
PIECE_LENGTH = 512 * 1024  # Size of each piece in bytes (512 KB)
OUTPUT_TORRENT_FILE = Path(__file__).parent / "sample1.torrent"  # Path to save the generated torrent file
root_directory = r"C:\Users\Administrator\Desktop\Assignment\Torrent-like-network-application\Sample"
FILE_PATHS = [  # List of absolute file paths to include in the torrent
    "random_2MB.txt",
    "random_4MB.txt",
    "random_8MB.txt",
]
full_paths = [os.path.join(root_directory, file) for file in FILE_PATHS]
# Directory for pieces
PIECES_DIRECTORY = Path(r"C:\Users\Administrator\Desktop\Assignment\Torrent-like-network-application\Sample\Pieces\Torrent1")

# Function to divide a file into pieces and return their SHA1 hashes
def divide_file(file_path, piece_size=PIECE_LENGTH):
    piece_hashes = []
    file_size = os.path.getsize(file_path)

    # Ensure the directory exists
    PIECES_DIRECTORY.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'rb') as f:
        piece_index = 0
        while True:
            piece_data = f.read(piece_size)
            if not piece_data:
                break  # End of file reached
            
            # Compute SHA1 hash of the piece
            piece_hash = hashlib.sha1(piece_data).digest()
            
            # Convert hash to hex and use it as the piece name
            piece_name = piece_hash.hex()
            
            # Save the piece in the specified directory with the hash as its name
            piece_file_path = PIECES_DIRECTORY / piece_name  # Combine directory and file name
            with open(piece_file_path, 'wb') as piece_f:
                piece_f.write(piece_data)
            
            piece_hashes.append(piece_hash)  # Append the hash for torrent creation
            piece_index += 1

    return piece_hashes  # Return list of SHA1 hashes of the pieces

# Function to create a torrent file
def create_torrent_file(output_path):
    try:
        # Prepare the "files" and "pieces" sections
        files = []
        all_pieces = b""
        for file_path in full_paths:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"File {file_path} does not exist. Skipping.")
                continue
            file_length = os.path.getsize(file_path)
            piece_hashes = divide_file(file_path, PIECE_LENGTH)
            
            # Append the hash of each piece to the all_pieces string
            all_pieces += b"".join(piece_hashes)
            
            files.append({
                b"path": [file_path.parent.name.encode(), file_path.name.encode()],
                b"length": file_length
            })

        # Define the "info" dictionary
        info = {
            b"piece length": PIECE_LENGTH,
            b"pieces": all_pieces,  # List of all piece hashes
            b"name": b"Torrent_Files",  # Name for the collection
            b"files": files  # List of files
        }

        # Define the top-level dictionary to be bencoded
        torrent_data = {
            b"announce": TRACKER_URL.encode(),  # Tracker URL
            b"info": info  # Info about the files
        }

        # Encode the data with bencodepy
        bencoded_data = bencodepy.encode(torrent_data)

        # Write the bencoded data to the output file in binary mode
        with open(output_path, 'wb') as torrent_file:
            torrent_file.write(bencoded_data)

        # Compute the info hash by hashing the "info" dictionary
        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()

        # Print the info hash as a hexadecimal string
        print(f"Info hash (SHA1): {info_hash.hex()}")

        print(f"Torrent file created at: {output_path}")
    except Exception as e:
        print(f"Error creating torrent file: {e}")

# Create the torrent file
create_torrent_file(OUTPUT_TORRENT_FILE)
