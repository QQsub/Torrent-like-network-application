from enum import Enum
import json
class Msg_Type(Enum):
    REQUEST = 0
    RESPONSE = 1

class Header_Type(Enum):
    LOGIN = 0
    LOGOUT = 1
    PING = 2
    ANNOUNCE = 3
    FETCH = 4
    
class message:
    HeaderType = None
    MsgType = None
    content = None

    def __init__(self, HeaderType = None, MsgType = None, content = None, JsonStr = None):
        if (JsonStr != None):
            string = loads(json_str)
            HeaderType = HeaderType(string['Header'])
            MsgType = Msg_Type(string['MessageType'])
            content = string['Content']
        
        self.HeaderType = HeaderType
        self.MsgType = MsgType
        self.content = content


