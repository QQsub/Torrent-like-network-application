import bencodepy
import socket

max_retries = 3     # Number of retries
timeout= 2          # Timeout

def bencode(data):
    return bencodepy.encode(data)

def decode_bencoded(data):
    return bencodepy.decode(data)

