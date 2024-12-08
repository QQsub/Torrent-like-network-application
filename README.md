# Simple Torrent-like Application (STA)

This project is a simplified torrent-like peer-to-peer (P2P) file sharing system developed as part of a university assignment. It demonstrates the fundamental concepts behind torrent technology—using a centralized tracker to coordinate peers and multithreaded clients to handle parallel uploads and downloads.

## Overview

The **Simple Torrent-like Application (STA)** breaks files into smaller pieces and distributes them across multiple peers. These peers coordinate with a central tracker that maintains metadata and peer information. By leveraging this setup, STA simulates fundamental torrent operations including:

- Retrieving file pieces from multiple peers.
- Reassembling the complete file from distributed segments.
- Managing concurrent transfers and ensuring data integrity.
## Usage Instructions

### Tracker
1. **Preconfigure:**

To activate the tracker, we need to make sure the tracker port is not in use. To do this, we can run the command to check in the command line:  

    `netstat −aon | findstr 12340`  

If the port is currently in used, we must manually kill the process that is running using:  

    `t askkill /PID <PID TO KILL> /F`

2. **Start the tracker:**  

   `python tracker.py`

3. **Update the tracker IP in the configuration.**

**Note**: To close the tracker server, we can just simply shut down the terminal and the tracker is shut down accordingly.

### Client
1. **Launch the client UI using Streamlit:**

    `streamlit run client_with_ui.py`
  
2. **Use the UI to:**

  Announce: Join a torrent.  
  Download: Fetch files from peers.  
  Stop: Exit the torrent and quit the network.

3. **Update the TRACKER IP in the client configuration.**  
## Contributors
**Doan Anh Quang** - Design and Implementation   
**Le Minh Trung** - Design and Implementation
