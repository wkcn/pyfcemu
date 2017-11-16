import numpy as np
from memory import *
from palette import *

class PPU:
    def __init__(self, console):
        self.console = console
        self.Cycle = 0
        self.ScanLine = 0
        self.Frame = 0

        # storage variables 
        self.paletteData = [0 for _ in range(32)] 
        self.nameTableData = [0 for _ in range(2048)] 
        self.oamData = [0 for _ in range(256)] 

        # PPU registers
        self.v = 0
        self.t = 0
        self.x =0
        self.w = 0
        self.f = 0

        self.register = 0

        self.nmiOccurred = False
        self.nmiOutput = False
        self.nmiPrevious = False
        self.nmiDelay = 0

        self.nameTableByte = 0
        self.attributeTableByte = 0
        self.lowTileByte = 0
        self.highTileByte = 0
        self.tileData = 0

        self.spriteCount = 0
        self.spritePatterns = [0 for _ in range(8)] 
        self.spritePositions = [0 for _ in range(8)] 
        self.spritePriorities = [0 for _ in range(8)] 
        self.spriteIndexes = [0 for _ in range(8)] 

        self.flagNameTable = 0
        self.flagIncrement = 0
        self.flagSpriteTable = 0
        self.flagBackgroundTable = 0
        self.flagSpriteSize = 0
        self.flagMasterSlave = 0

        self.flagGrayscale = 0
        self.flagShowLeftBackground = 0
        self.flagShowLeftSprites = 0
        self.flagShowBackground = 0
        self.flagShowSprites = 0
        self.flagRedTint = 0
        self.flagGreenTint = 0
        self.flagBlueTint = 0

        self.flagSpriteZeroHit = 0
        self.flagSpriteOverflow = 0

        self.oamAddress = 0
        self.bufferedData = 0

        # width: 256
        # height: 240
        self.front = np.zeros((240, 256, 3), dtype = np.uint8)
        self.back = np.zeros((240, 256, 3), dtype = np.uint8)

        self.Reset()

    def Reset(self):
        self.Cycle = 340
        self.ScanLine = 240
        self.Frame = 0
        self.writeControl(0)
        self.writeMask(0)
        self.writeOAMAddress(0)

    def Read(self, address):
        address = address & 0x3FFF
        if address < 0x2000:
            return self.console.Mapper.Read(address)
        elif address < 0x3F00:
            mode = self.console.Cartridge.Mirror
            return self.console.PPU.nameTableData[MirrorAddress(mode, address) & 0x7FF]
        elif address < 0x4000:
            return self.console.PPU.readPalette(address & 0x1F)
        else:
            raise RuntimeError("Unhandled PPU Memory read at address: 0x%04X" % address)
        return 0

    def Write(self, address, value):
        address = address & 0x3FFF
        if address < 0x2000:
            self.console.Mapper.Write(address, value)
        elif address < 0x3F00:
            mode = self.console.Cartridge.Mirror
            self.console.PPU.nameTableData[MirrorAddress(mode, address) & 0x7FF] = value
        elif address < 0x4000:
            self.console.PPU.writePalette(address & 0x1F, value)
        else:
            raise RuntimeError("Unhandled PPU Memory write at address: 0x%04X" % address)

    def readPalette(self, address):
        if address >= 16 and address & 0x3 == 0:
            address -= 16
        return self.paletteData[address]

    def writePalette(self, address, value):
        if address >= 16 and address & 0x3 == 0:
            address -= 16
        self.paletteData[address] = value

    def readRegister(self, address):
        if address == 0x2002:
            return self.readStatus()
        elif address == 0x2004:
            return self.readOAMData()
        elif address == 0x2007:
            return self.readData()
        return 0

    def writeRegister(self, address, value):
        self.register = value
        ops = {
                0x2000: self.writeControl,
                0x2001: self.writeMask,
                0x2003: self.writeOAMAddress,
                0x2004: self.writeOAMData,
                0x2005: self.writeScroll,
                0x2006: self.writeAddress,
                0x2007: self.writeData,
                0x4014: self.writeDMA
        }
        ops[address](value)

    def writeControl(self, value):
        self.flagNameTable = (value >> 0) & 3
        self.flagIncrement = (value >> 2) & 1
        self.flagSpriteTable = (value >> 3) & 1
        self.flagBackgroundTable = (value >> 4) & 1
        self.flagSpriteSize = (value >> 5) & 1
        self.flagMasterSlave = (value >> 6) & 1
        self.nmiOutput = (((value >> 7) & 1) == 1)
        self.nmiChange()
        self.t = ((self.t & 0xF3FF) | (((value & 0x03) << 10) & 0xFFFF))

    def writeMask(self, value):
        self.flagGrayscale = (value >> 0) & 1
        self.flagShowLeftBackground = (value >> 1) & 1
        self.flagShowLeftSprites = (value >> 2) & 1
        self.flagShowBackground = (value >> 3) & 1
        self.flagShowSprites = (value >> 4) & 1
        self.flagRedTint = (value >> 5) & 1
        self.flagGreenTint = (value >> 6) & 1
        self.flagBlueTint = (value >> 7) & 1

    def readStatus(self):
        result = self.register & 0x1F
        result |= (self.flagSpriteOverflow << 5)
        result |= (self.flagSpriteZeroHit << 6)
        if self.nmiOccurred:
            result |= (1 << 7)
        self.nmiOccurred = False
        self.nmiChange()
        self.w = 0
        return result

    def writeOAMAddress(self, value):
        self.oamAddress = value

    def readOAMData(self):
        return self.oamData[self.oamAddress]

    def writeOAMData(self, value):
        self.oamData[self.oamAddress] = value
        self.oamAddress = (self.oamAddress + 1) & 0xFF 

    def writeScroll(self, value):
        if self.w == 0:
            self.t = (self.t & 0xFFE0) | (value >> 3) 
            self.x = value & 0x07
            self.w = 1
        else:
            self.t = (self.t & 0x8FFF) | (((value & 0x07) << 12) & 0xFFFF) 
            self.t = (self.t & 0xFC1F) | (((value & 0xF8) << 2) & 0xFFFF) 
            # self.t twice!
            self.w = 0

    def writeAddress(self, value):
        if self.w == 0:
            self.t = (self.t & 0x80FF) | (((value & 0x3F) << 8) & 0xFFFF)
            self.w = 1
        else:
            self.t = (self.t & 0xFF00) | value
            self.v = self.t
            self.w = 0

    def readData(self):
        value = self.Read(self.v)
        if self.v & 0x3FFF < 0x3F00:
            buffered = self.bufferedData
            self.bufferedData = value
            value = buffered
        else:
            self.bufferedData = self.Read((self.v - 0x1000) & 0xFFFF) 

        if self.flagIncrement == 0:
            self.v = (self.v + 1) & 0xFFFF
        else:
            self.v = (self.v + 32) & 0xFFFF
        return value

    def writeData(self, value):
        self.Write(self.v, value)
        if self.flagIncrement == 0:
            self.v = (self.v + 1) & 0xFFFF
        else:
            self.v = (self.v + 32) & 0xFFFF

    def writeDMA(self, value):
        cpu = self.console.CPU
        address = (value << 8) & 0xFFFF
        for i in range(256):
            self.oamData[self.oamAddress] = cpu.Read(address)
            self.oamAddress = (self.oamAddress + 1) & 0xFF  
            address = (address + 1) & 0xFFFF
        cpu.stall += 513
        if cpu.Cycles & 1 == 1:
            cpu.stall += 1

    def incrementX(self):
        if self.v & 0x001F == 31:
            self.v &= 0xFFE0
            self.v ^= 0x0400
        else:
            self.v = (self.v + 1) & 0xFFFF 

    def incrementY(self):
        if self.v & 0x7000 != 0x7000:
            self.v = (self.v + 0x1000) & 0xFFFF 
        else:
            self.v &= 0x8FFF
            y = (self.v & 0x03E0) >> 5
            if y == 29:
                y = 0
                self.v ^= 0x0800
            elif y == 31:
                y = 0
            else:
                y = (y + 1) & 0xFFFF
            self.v = (self.v & 0xFC1F) | ((y << 5) & 0xFFFF)

    def copyX(self):
        self.v = (self.v & 0xFBE0) | (self.t & 0x041F)

    def copyY(self):
        self.v = (self.v & 0x841F) | (self.t & 0x7BE0)

    def nmiChange(self):
        nmi = (self.nmiOutput and self.nmiOccurred)
        if nmi and not self.nmiPrevious:
            self.nmiDelay = 15
        self.nmiPrevious = nmi

    def setVerticalBlank(self):
        self.front, self.back = self.back, self.front
        self.nmiOccurred = True
        self.nmiChange()

    def clearVerticalBlank(self):
        self.nmiOccurred = False
        self.nmiChange()

    def fetchNameTableByte(self):
        v = self.v
        address = 0x2000 | (v & 0x0FFF)
        self.nameTableByte = self.Read(address)

    def fetchAttributeTableByte(self):
        v = self.v
        address = 0x23C0 | (v & 0x0C00) | ((v >> 4) & 0x38) | ((v >> 2) & 0x07) 
        shift = ((v >> 4) & 4) | (v & 2)
        self.attributeTableByte = (((self.Read(address) >> shift) & 3) << 2) & 0xFF

    def fetchLowTileByte(self):
        fineY = (self.v >> 12) & 7
        table = self.flagBackgroundTable
        tile = self.nameTableByte
        address = ((table << 12) + (tile << 4) + fineY) & 0xFFFF
        self.lowTileByte = self.Read(address)

    def fetchHighTileByte(self):
        fineY = (self.v >> 12) & 7
        table = self.flagBackgroundTable
        tile = self.nameTableByte
        address_8 = ((table << 12) + (tile << 4) + fineY + 8) & 0xFFFF
        self.highTileByte = self.Read(address_8)

    def storeTileData(self):
        data = 0
        a = self.attributeTableByte
        for i in range(8):
            p1 = (self.lowTileByte & 0x80) >> 7
            p2 = (self.highTileByte & 0x80) >> 6
            self.lowTileByte <<= 1 
            self.highTileByte <<= 1
            data <<= 4
            data |= (a | p1 | p2)
        self.lowTileByte &= 0xFF
        self.highTileByte &= 0xFF
        self.tileData |= data # uint64

    def backgroundPixel(self):
        if self.flagShowBackground == 0:
            return 0
        data = (self.tileData >> 32)  >> ((7 - self.x) << 2)
        return data & 0x0F

    def spritePixel(self): 
        if self.flagShowSprites == 0:
            return 0,0 
        for i in range(self.spriteCount):
            offset = (self.Cycle - 1) - self.spritePositions[i]
            if offset < 0 or offset > 7:
                continue
            offset = 7 - offset
            color = (self.spritePatterns[i] >> (offset << 2)) & 0x0F
            if color & 0x3 == 0:
                continue
            return i, color
        return 0,0 

    def renderPixel(self):
        x = self.Cycle - 1
        y = self.ScanLine
        background = self.backgroundPixel()
        i, sprite = self.spritePixel()
        if x < 8 and self.flagShowLeftBackground == 0:
            background = 0
        if x < 8 and self.flagShowLeftSprites == 0:
            sprite = 0
        b = (background & 0x3 != 0)
        s = (sprite & 0x3 != 0)
        color = 0
        if not b and not s:
            color = 0
        elif not b and s:
            color = sprite | 0x10
        elif b and not s:
            color = background
        else:
            if self.spriteIndexes[i] == 0 and x < 255:
                self.flagSpriteZeroHit = 1 
            if self.spritePriorities[i] == 0:
                color = sprite | 0x10
            else:
                color = background
        c = Palette[self.readPalette(color) & 0x3F]
        self.back[y,x] = c

    def fetchSpritePattern(self, i, row):
        k = (i << 2) + 1
        tile = self.oamData[k]
        attributes = self.oamData[k + 1]
        address = 0
        if self.flagSpriteSize == 0:
            if attributes&0x80 == 0x80:
                row = 7 - row
            table = self.flagSpriteTable
            address = ((table << 12) + (tile << 4) + row) & 0xFFFF
        else:
            if attributes & 0x80 == 0x80:
                row = 15 - row
            table = tile & 1
            tile &= 0xFE
            if row > 7:
                tile += 1
                row -= 8
            address = ((table << 12)+ (tile << 4) + row) & 0xFFFF
        a = (attributes & 3) << 2
        lowTileByte = self.Read(address)
        highTileByte = self.Read((address + 8) & 0xFFFF)
        data = 0
        for i in range(8):
            if attributes & 0x40 == 0x40:
                p1 = (lowTileByte & 1)
                p2 = ((highTileByte & 1) << 1) & 0xFF
                lowTileByte >>= 1
                highTileByte >>= 1
            else:
                p1 = (lowTileByte & 0x80) >> 7
                p2 = (highTileByte & 0x80) >> 6
                lowTileByte = lowTileByte << 1
                highTileByte = highTileByte << 1
            data <<= 4
            data |= (a | p1 | p2)
        return data

    def evaluateSprites(self):
        if self.flagSpriteSize == 0:
            h = 8
        else:
            h = 16
        count = 0
        for i in range(64):
            k = (i << 2)
            y = self.oamData[k]
            a = self.oamData[k + 2]
            x = self.oamData[k + 3]
            row = self.ScanLine - y
            if row < 0 or row >= h:
                continue
            if count < 8:
                self.spritePatterns[count] = self.fetchSpritePattern(i, row)
                self.spritePositions[count] = x
                self.spritePriorities[count] = (a >> 5) & 1
                self.spriteIndexes[count] = i
            count += 1
        if count > 8:
            count = 8
            self.flagSpriteOverflow = 1
        self.spriteCount = count

    def tick(self):
        if self.nmiDelay > 0:
            self.nmiDelay -= 1 
            if self.nmiDelay == 0 and self.nmiOutput and self.nmiOccurred:
                self.console.CPU.triggerNMI()

        if self.flagShowBackground != 0 or self.flagShowSprites != 0:
            if self.f == 1 and self.ScanLine == 261 and self.Cycle == 339:
                self.Cycle = 0
                self.ScanLine = 0
                self.Frame += 1
                self.f ^= 1
                return

        self.Cycle += 1
        if self.Cycle > 340:
            self.Cycle = 0
            self.ScanLine += 1
            if self.ScanLine > 261:
                self.ScanLine = 0
                self.Frame += 1
                self.f ^= 1

    def Step(self):
        self.tick()

        renderingEnabled = (self.flagShowBackground != 0) or (self.flagShowSprites != 0)
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
                self.tileData <<= 4
                c = self.Cycle & 0x7
                if c == 1:
                    self.fetchNameTableByte()
                elif c == 3:
                    self.fetchAttributeTableByte()
                elif c == 5:
                    self.fetchLowTileByte()
                elif c == 7:
                    self.fetchHighTileByte()
                elif c == 0:
                    self.storeTileData()

            if preLine and self.Cycle >= 280 and self.Cycle <= 304:
                self.copyY()
            if renderLine:
                if fetchCycle and self.Cycle & 0x7 == 0:
                    self.incrementX()
                if self.Cycle == 256:
                    self.incrementY()
                if self.Cycle == 257:
                    self.copyX()
        # sprite logic
        if renderingEnabled:
            if self.Cycle == 257:
                if visibleLine:
                    self.evaluateSprites()
                else:
                    self.spriteCount = 0

        # vblank logic
        if self.ScanLine == 241 and self.Cycle == 1:
            self.setVerticalBlank()
        if preLine and self.Cycle == 1:
            self.clearVerticalBlank()
            self.flagSpriteZeroHit = 0
            self.flagSpriteOverflow = 0 

