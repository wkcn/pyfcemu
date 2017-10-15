from numpy import *

MirrorHorizontal, MirrorVertical, MirrorSingle0, MirrorSingle1, MirrorFour = range(5)

MirrorLookup = array([[0,0,1,1],[0,1,0,1],[0,0,0,0],[1,1,1,1],[0,1,2,3]]).astype(uint16)

def MirrorAdress(mode, address):
    address = (address - uint16(0x2000)) % uint16(0x1000)
    table = address // uint16(0x0400)
    offset = address % uint16(0x0400)
    return uint16(0x2000) + MirrorLookup[mode][table] * uint16(0x0400) + offset

class Memory:
    def __init__(self, console):
        pass

class NewPPUMemory:
    def __init__(self, console):
        self.console = console
    def Read(self, address):
        address = address % uint16(0x4000)
        if address < 0x2000:
            return self.console.Mapper.Read(address)
        elif address < 0x3F00:
            mode = self.console.Cartridge.Mirror
            return self.console.PPU.nameTableData[MirrorAddress(mode, address) % uint16(2048)]
        elif address < 0x4000:
            return self.console.PPU.readPalette(address % uint16(32))
        else:
            raise RuntimeError("Unhandled PPU Memory read at address: 0x%04X" % address)

    def Write(self, address, value):
        address = address % uint16(0x4000)
        if address < 0x2000:
            self.console.Mapper.Write(address, value)
        elif address < 0x3F00:
            mode = self.console.Cartridge.Mirror
            self.console.PPU.nameTableData[MirrorAddress(mode, address) % uint16(2048)] = value
        elif address < 0x4000:
            self.console.PPU.writePalette(address % uint16(32), value)
        else:
            raise RuntimeError("Unhandled PPU Memory write at address: 0x%04X" % address)

