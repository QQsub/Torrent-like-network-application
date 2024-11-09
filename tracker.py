#Define timeout
TIMEOUT = 2

#Tracker class
class Tracker:
    host = None
    port = None
    TrackerSocket = None
    TrackerDb = None
    TrackerOn = True

    def __init__(self, host = None, port = None, TrackerSocket = None, TrackerDb = None)