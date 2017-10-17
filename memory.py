from numpy import *

MirrorHorizontal, MirrorVertical, MirrorSingle0, MirrorSingle1, MirrorFour = range(5)

MirrorLookup = array([[0,0,1,1],[0,1,0,1],[0,0,0,0],[1,1,1,1],[0,1,2,3]], dtype = uint16)

def MirrorAddress(mode, address):
    address = (address - uint16(0x2000)) % uint16(0x1000)
    table = address // uint16(0x0400)
    offset = address % uint16(0x0400)
    return uint16(0x2000) + MirrorLookup[mode][table] * uint16(0x0400) + offset

class Memory:
    def __init__(self, console):
        pass
