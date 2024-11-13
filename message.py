from enum import Enum
import json
# Define message type
class Msg_Type(Enum):
    REQUEST = 0
    RESPONSE = 1
# Define header type
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

    #unpack message
    def __init__(self, header_type=None, msg_type=None, content=None, json_str=None):
        if json_str is not None:
            data = json.loads(json_str)
            header_type = Header_Type[data['Header']]
            msg_type = Msg_Type[data['MessageType']]
            content = data['Content']

        self.header_type = header_type
        self.msg_type = msg_type
        self.content = content


