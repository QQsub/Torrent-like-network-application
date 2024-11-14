import bencodepy
import socket

max_retries = 3     # Number of retries
timeout= 2          # Timeout

def bencode(data):
    """ Encode data in Bencode format """
    return bencodepy.encode(data)

def decode_bencoded(data):
    """ Decode Bencoded data """
    return bencodepy.decode(data)

def create_socket():
    """ Create a TCP socket for peer-to-peer communication """
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
