include "cdefines.pyx"

cdef public uint16 MirrorHorizontal, MirrorVertical, MirrorSingle0, MirrorSingle1, MirrorFour
MirrorHorizontal = 0
MirrorVertical = 1
MirrorSingle0 = 2
MirrorSingle1 = 3
MirrorFour = 4

cdef public uint16 MirrorLookup[5][4]
MirrorLookup = [[0,0,1,1],[0,1,0,1],[0,0,0,0],[1,1,1,1],[0,1,2,3]]

cpdef uint16 MirrorAddress(uint8 mode, uint16 address):
    address = ((address - 0x2000) & 0xFFFF) & 0x0FFF
    table = (address >> 10)#// 0x0400
    offset = address & 0x03FF#% 0x0400
    return (0x2000 + (MirrorLookup[mode][table] << 10) + offset) & 0xFFFF
