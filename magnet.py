import re

def create_magnet(info_hash, tracker_url=None):
    #Generate a magnet link from the info hash and optional tracker URL.
    magnet_link = f"magnet:?xt=urn:btih:{info_hash}"
    if tracker_url:
        magnet_link += f"&tr={tracker_url}"
    return magnet_link

def parse_magnet(link):
    #Parse a magnet link and extract the info hash.
    pattern = r'magnet:\?xt=urn:btih:([a-fA-F0-9]{20,40})'
    match = re.match(pattern, link)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid magnet link")
