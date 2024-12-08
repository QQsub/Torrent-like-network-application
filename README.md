# Simple Torrent-like Application (STA)

This project is a simplified torrent-like peer-to-peer (P2P) file sharing system developed as part of a university assignment. It demonstrates the fundamental concepts behind torrent technology—using a centralized tracker to coordinate peers and multithreaded clients to handle parallel uploads and downloads.

## Table of Contents

- [Overview](#overview)
- [Usage Instructions](#usage-instructions)
  - [Tracker](#tracker)
  - [Client](#client)
- [Contributors](#contributors)

## Overview

The Simple Torrent-like Application (STA) provides a mechanism for splitting files into smaller pieces and distributing them efficiently across multiple peers. By leveraging a tracker to maintain metadata and a set of clients to exchange file segments, STA aims to demonstrate basic torrent operations such as piece retrieval, file assembly, and handling multiple concurrent transfers.

## Usage Instructions

### Tracker
1. preconfigure:
To activate the tracker, we need to make sure the tracker port is not in use. To do this, we can run the command to check in the command line:
netstat −aon | findstr 12340
If the port is currently in used, we must manually kill the process that is running using:
t askkill /PID <PID TO KILL> /F
2. Start the tracker:
python tracker.py
3. Update the tracker IP in the configuration.
**Note: To close the tracker server, we can just simply shut down the terminal and the tracker is shut down accordingly.**
### Client
1. Launch the client UI using Streamlit:
  streamlit run client_with_ui.py
2. Use the UI to:
Announce: Join a torrent.
Download: Fetch files from peers.
Stop: Exit the torrent and quit the network.
3. Update the TRACKER IP in the client configuration.
   - Removed variables with weak correlations to the target variable to enhance model performance.

##Contributors
**Doan Anh Quang** - Design and Implementation
**Le Minh Trung** - Design and Implementation
