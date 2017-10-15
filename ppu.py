from numpy import *
from memory import *

class PPU:
    def __init__(self, console):
        self.console = console
        self.Cycle = 340
        self.ScanLine = 240
        self.Frame = 0
        self.t = uint16()
        self.front = zeros((256, 240, 3), dtype = uint8)
        self.back = zeros((256, 240, 3), dtype = uint8)
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

    def readOAMData(value):
        self.oamData[self.oamAddress] = value
        self.oamAddress += byte(1) 

    def writeScroll(value):
        if self.w == 0:
            self.t = (self.t & uint16(0xFFE0)) | (uint16(value) >> uint16(3)) 
            self.x = value & byte(0x07)
            self.w = byte(1) 
        else:
            self.t = (self.t & uint16(0x8FFF)) | ((uint16(value) & uint16(0x07)) << uint16(12)) 
            self.t = (self.t & uint16(0xFC1F)) | ((uint16(value) & uint16(0xF8)) << uint16(2)) 
            # ???
            self.w = byte(0)

    def writeAddress(self, value):
        if self.w == 0:
            self.t = (self.t & uint16(0x80FF)) | ((uint16(value) & uint16(0x3F)) << uint16(8))
            self.w = byte(1)
        else:
            self.t = (self.t & uint16(0xFF00)) | uint16(value)
            self.v = self.t
            self.w = byte(0)

    def readData(self):
        value = self.Read(self.v)
        if self.v % 0x4000 < 0x3F00:
            buffered = self.bufferedData
            self.bufferedData = value
            value = buffered
        else:
            self.bufferedData = self.Read(self.v - uint16(0x1000)) 

        if self.flagIncrement == 0:
            self.v += uint16(1)
        else:
            self.v += uint16(32)
        return value

    def writeData(self, value):
        self.Write(self.v, value)
        if self.flagIncrement == 0:
            self.v += uint16(1)
        else:
            self.v += uint16(32)

    def writeDMA(self, value):
        cpu = self.console.CPU
        address = uint16(value) << uint16(8)
        for i in range(256):
            self.oamData[self.oamAddress] = cpu.Read(address)
            self.oamAddress += byte(1) 
            address += uint16(1)
        cpu.stall += 513 
        if cpu.Cycles % 2 == 1:
            cpu.stall += 1

    def fetchNameTableByte(self):
        v = self.v
        address = uint16(0x2000) | (v & uint16(0x0FFF))
        self.nameTableByte = self.Read(address)

    def fetchAttributeTableByte(self):
        v = self.v
        address = uint16(0x23C0) | (v & uint16(0x0C00)) | ((v >> uint16(4)) & uint16(0x38)) | ((v >> uint16(2)) & uint16(0x07)) 
        shift = ((v >> uint16(4)) & uint16(4)) | (v & uint16(2))
        self.attributeTableByte = (((self.Read(address) >> byte(shift)) & byte(3)) << byte(2)) 

    def fetchLowTileByte(self):
        fineY = (self.v >> uint16(12)) & uint16(7)
        table = self.flagBackgroundTable
        tile = self.nameTableByte
        address = uint16(0x1000) * uint16(table) + uint16(tile) * uint16(16) + fineY
        self.lowTileByte = self.Read(address)

    def fetchHighTileByte(self):
        fineY = (self.v >> uint16(12)) & uint16(7)
        table = self.flagBackgroundTable
        tile = self.nameTableByte
        address = uint16(0x1000) * uint16(table) + uint16(tile) * uint16(16) + fineY
        self.highTileByte = self.Read(address + uint16(8))

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

