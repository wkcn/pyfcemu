from numpy import *
from memory import *

class PPU:
    def __init__(self, console):
        self.Memory = NewPPUMemory(console)
        self.console = console
        self.Cycle = 340
        self.ScanLine = 240
        self.Frame = 0
        self.t = uint16()
        self.front = zeros((256, 240, 3)).astype(uint8)
        self.back = zeros((256, 240, 3)).astype(uint8)
        self.writeControl(0)
        self.writeMask(0)
        self.writeOAMAddress(0)

    def writeControl(self, value):
        self.flagNameTable = (value >> byte(0)) & byte(3)
        self.flagIncrement = (value >> byte(2)) & byte(1)
        self.flagSpriteTable = (value >> byte(3)) & byte(1)
        self.flagBackgroundTable = (value >> byte(4)) & byte(1)
        self.flagSpriteSize = (value >> byte(5)) & byte(1)
        self.flagMasterSlave = (value >> byte(6)) & byte(1)
        self.nmiOutput = ((value >> byte(7)) & byte(1)) == 1
        self.t = (self.t & uint16(0xF3FF)) | ((uint16(value) & uint16(0x03)) << uint16(10)) 
