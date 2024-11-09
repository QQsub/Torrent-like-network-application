#Define timeout
TIMEOUT = 2

#Tracker class
class Tracker:
    host = None
    port = None
    socket = None
    ClientList = []       
    TrackerOn = False

    def __init__(self, host = None, port = None, socket = None, ClientList = []):
        #Turn on tracker
        TrackerOn = True
        
        #Initialize tracker data
        self.host = host
        self.port = port
        self.socket = socket
        self.ClientList = ClientList

    def addClient (self, clientID = None):
        if(clientID != None):
            self.ClientList.append(clientID)
        return f"Client {clientID} successfully joined the torrent network."

    def deleteClient(self, clientID):
        if clientID in self.ClientList:
            self.ClientList.remove(clientID)
            return f"Client {clientID} left the torrent network."
        else:
            return f"Client {clientID} not exist in the torrent network."


