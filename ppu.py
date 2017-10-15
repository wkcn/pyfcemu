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
        self.CYCLE_TO_DO = {
                1: self.fetchNameTableByte,
                3: self.fetchAttributeTableByte,
                5: self.fetchLowTileByte,
                7: self.fetchHighTileByte,
                0: self.storeTileData
        }

    def readPalette(self, address):
        if address >= 16 and address % 4 == 0:
            address -= uint16(16)
        return self.paletteData[address]

    def writePalette(self, address, value):
        if address >= 16 and address % 4 == 0:
            address -= uint16(16)
        self.paletteData[address] = value

    def writeControl(self, value):
        self.flagNameTable = (value >> byte(0)) & byte(3)
        self.flagIncrement = (value >> byte(2)) & byte(1)
        self.flagSpriteTable = (value >> byte(3)) & byte(1)
        self.flagBackgroundTable = (value >> byte(4)) & byte(1)
        self.flagSpriteSize = (value >> byte(5)) & byte(1)
        self.flagMasterSlave = (value >> byte(6)) & byte(1)
        self.nmiOutput = ((value >> byte(7)) & byte(1)) == 1
        self.t = (self.t & uint16(0xF3FF)) | ((uint16(value) & uint16(0x03)) << uint16(10)) 

    def writeMask(self, value):
        self.flagGrayscale = (value >> byte(0)) & byte(1)
        self.flagShowLeftBackground = (value >> byte(1)) & byte(1)
        self.flagShowLeftSprites = (value >> byte(2)) & byte(1)
        self.flagShowBackground = (value >> byte(3)) & byte(1)
        self.flagSHowSprites = (value >> byte(4)) & byte(1)
        self.flagRedTint = (value >> byte(5)) & byte(1)
        self.flagGreenTint = (value >> byte(6)) & byte(1)
        self.flagBlueTint = (value >> byte(7)) & byte(1)

    def writeOAMAddress(self, value):
        self.oamAddress = value

    def Step(self):
        self.tick()

        renderingEnabled = (self.flagShowBackground != 0) or (self.flagSHowSprites != 0)
        preLine = (self.ScanLine == 261)
        visibleLine = (self.ScanLine < 240)
        renderLine = preLine or visibleLine
        preFetchCycle = (self.Cycle >= 321) and (self.Cycle <= 336)
        visibleCycle = (self.Cycle >= 1) and (self.Cycle <= 256)
        fetchCycle = preFetchCycle or visibleCycle

        # background logic
        if renderingEnabled:
            if visibleLine and visibleCycle:
                self.renderPixel()
            if renderLine and fetchCycle:
                self.tileData <<= uint64(4)
                self.CYCLE_TO_DO[self.Cycle % 8]()

        ### TODO
