from numpy import *
from memory import *

class PPU:
    def __init__(self, console):
        self.console = console
        self.Cycle = 340
        self.ScanLine = 240
        self.Frame = 0

        # storage variables 
        self.paletteData = zeros(32, dtype = byte)
        self.nameTableData = zeros(2048, dtype = byte)
        self.oamData = zeros(256, dtype = byte) 

        # PPU registers
        self.v = uint16()
        self.t = uint16()
        self.x = byte()
        self.w = byte()
        self.f = byte()

        self.register = byte()

        self.nmiOccurred = False
        self.nmiOutput = False
        self.nmiPrevious = False
        self.nmiDelay = byte()

        self.nameTableByte = byte()
        self.attributeTableByte = byte()
        self.lowTileByte = byte()
        self.highTileByte = byte()
        self.tileData = uint64()

        self.spriteCount = 0
        self.spritePatterns = zeros(8, dtype = uint32)
        self.spritePositions = zeros(8, dtype = byte)
        self.spritePriorities = zeros(8, dtype = byte)
        self.spriteIndexes = zeros(8, dtype = byte)

        self.flagNameTable = byte()
        self.flagIncrement = byte()
        self.flagSpriteTable = byte()
        self.flagBackgroundTable = byte()
        self.flagSpriteSize = byte()
        self.flagMasterSlave = byte()

        self.flagGrayscale = byte()
        self.flagShowLeftBackground = byte()
        self.flagShowLeftSprites = byte()
        self.flagShowBackground = byte()
        self.flagShowSprites = byte()
        self.flagRedTint = byte()
        self.flagGreenTint = byte()
        self.flagBlueTint = byte()

        self.flagSpriteZeroHit = byte()
        self.flagSpriteOverflow = byte()

        self.oamAddress = byte()
        self.bufferedData = byte()

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

    def readRegister(self, address):
        if address == 0x2002:
            return self.readStatus()
        elif address == 0x2004:
            return self.readOAMData()
        elif address == 0x2007:
            return self.readData()
        return byte(0)

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
        self.flagShowSprites = (value >> byte(4)) & byte(1)
        self.flagRedTint = (value >> byte(5)) & byte(1)
        self.flagGreenTint = (value >> byte(6)) & byte(1)
        self.flagBlueTint = (value >> byte(7)) & byte(1)

    def readStatus(self):
        result = self.register & byte(0x1F)
        result |= (self.flagSpriteOverflow << byte(5))
        result |= (self.flagSpriteZeroHit << byte(6))
        if self.nmiOccurred:
            result |= (byte(1) << byte(7))
        self.nmiOccurred = False
        self.nmiChange()
        self.w = byte(0)
        return result


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

    def incrementX(self):
        if self.v & uint16(0x001F) == 31:
            self.v &= uint16(0xFFE0)
            self.v ^= uint16(0x0400)
        else:
            self.v += uint16(1)

    def incrementY(self):
        if self.v & 0x7000 != 0x7000:
            self.v += uint16(0x1000)
        else:
            self.v &= uint16(0x8FFF)
            y = (self.v & uint16(0x03E0)) >> uint16(5)
            if y == 29:
                y = uint16(0)
                self.v ^= uint16(0x0800)
            elif y == 31:
                y = uint16(0)
            else:
                y += uint16(1)
            self.v = (self.v & uint16(0xFC1F)) | (y << uint16(5))

    def copyX(self):
        self.v = (self.v & uint16(0xFBE0)) | (self.t & uint16(0x041F))

    def copyY(self):
        self.v = (self.v & uint16(0x841F)) | (self.t & uint16(0x7BE0))

    def nmiChange(self):
        nmi = (self.nmiOutput and self.nmiOccurred)
        if nmi and not self.nmiPrevious:
            self.nmiDelay = byte(15)
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

    def storeTileData(self):
        a = self.fetchAttributeTableByte
        data = uint32(0)
        for i in range(8):
            p1 = (self.lowTileByte & byte(0x80)) >> byte(7)
            p2 = (self.highTileByte & byte(0x80)) >> byte(6)
            self.lowTileByte <<= byte(1)
            self.highTileByte <<= byte(1)
            data <<= uint32(4)
            data |= uint32(a | p1 | p2)
        self.tileData |= uint64(data)

    def fetchTileData(self):
        return uint32(self.tileData >> uint64(32)) 

    def backgroundPixel(self):
        if self.flagShowBackground == 0:
            return byte(0)
        data = self.fetchTileData() >> ((uint32(7) - self.x) * uint32(4))
        return byte(data & byte(0x0F))

    def spritePixel(self): 
        if self.flagShowSprites == 0:
            return byte(0), byte(0)
        for i in range(self.spriteCount):
            offset = (self.Cycle - 1) - self.spritePositions[i]
            if offset < 0 or offset > 7:
                continue
            offset = 7 - offset
            color = byte((self.spritePatterns[i] >> byte(offset * 4)) & 0x0F)
            if color % 4 == 0:
                continue
            return byte(i), color
        return byte(0), byte(0)

    def renderPixel(self):
        x = self.Cycle - 1
        y = self.ScanLine
        background = self.backgroundPixel()
        i, sprite = self.spritePixel()
        if x < 8 and self.flagShowLeftBackground == 0:
            background = byte(0)
        if x < 8 and self.flagShowLeftSprites == 0:
            sprite = byte(0)
        b = (background % 4 != 0)
        s = (sprite % 4 != 0)
        color = byte(0)
        if not b and not s:
            color = byte(0)
        elif not b and s:
            color = sprite | byte(0x10)
        elif b and not s:
            color = background
        else:
            if self.spriteIndexes[i] == 0 and x < 255:
                self.flagSpriteZeroHit = byte(1) 
            if self.spritePriorities[i] == 0:
                color = sprite | byte(0x10)
            else:
                color = background
        c = Palette[self.readPalette(uint16(color)) % 64]
        self.back.SetRGBA(x, y, c)

        def fetchSpritePattern(self, i, row):
            tile = self.oamData[i * 4 + 1]
            attributes = self.oamData[i * 4 + 2]
            address = uint16(0)
            if self.flagSpriteSize == 0:
                if attributes&0x80 == 0x80:
                    row = 7 - row
                table = self.flagSpriteTable
                address = uint16(0x1000) * uint16(table) + uint16(tile) * uint16(16) + uint16(row)
            else:
                if attributes & 0x80 == 0x80:
                    row = 15 - row
                table = tile & byte(1)
                tile &= byte(0xFE)
                if row > 7:
                    tile += byte(1)
                    row -= 8
                address = uint16(0x1000) * uint16(table) + uint16(tile) * uint16(16) + uint16(row)
            a = (attributes & byte(3)) << byte(2)
            lowTileByte = self.Read(address)
            highTileByte = self.Read(address + uint16(8))
            data = uint32(0)
            for i in range(8):
                if attributes & 0x40 == 0x40:
                    p1 = (lowTileByte & byte(1))
                    p2 = (highTileByte & byte(1)) << byte(1)
                    lowTileByte >>= byte(1)
                    highTileByte >>= byte(1)
                else:
                    p1 = (lowTileByte & byte(0x80)) >> byte(7)
                    p2 = (highTileByte & byte(0x80)) >> byte(6)
                    lowTileByte <<= byte(1)
                    highTileByte <<= byte(1)
                data <<= uint32(4)
                data |= uint32(a | p1 | p2)
            return data
    
    def evaluateSprites(self):
        if self.flagSpriteSize == 0:
            h = 8
        else:
            h = 16
        count = 0
        for i in range(64):
            y = self.oamData[i * 4 + 0]
            a = self.oamData[i * 4 + 2]
            x = self.oamData[i * 4 + 3]
            row = self.ScanLine - int(y)
            if row < 0 or row >= h:
                continue
            if count < 0:
                self.spritePatterns[count] = self.fetchSpritePattern(i, row)
                self.spritePositions[count] = x
                self.spritePriorities[count] = (a >> byte(5)) & byte(1)
                self.spriteIndexes[count] = byte(i)
            count += 1
        if count > 8:
            count = 8
            self.flagSpriteOverflow = byte(1)
        self.spriteCount = count

    def tick(self):
        if self.nmiDelay > 0:
            self.nmiDelay -= byte(1)
            if self.nmiDelay == 0 and self.nmiOutput and self.nmiOccurred:
                self.console.CPU.triggerNMI()

        if self.flagShowBackground != 0 or self.flagShowSprites != 0:
            if self.f == 1 and self.ScanLine == 261 and self.Cycle == 339:
                self.Cycle = 0
                self.ScanLine = 0
                self.Frame += uint64(1)
                self.f ^= byte(1)
                return

        self.Cycle += 1
        if self.Cycle > 340:
            self.Cycle = 0
            self.ScanLine += 1
            if self.ScanLine > 261:
                self.ScanLine = 0
                self.Frame += uint64(1)
                self.f ^= byte(1)

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
                self.tileData <<= uint64(4)
                self.CYCLE_TO_DO[self.Cycle % 8]()

