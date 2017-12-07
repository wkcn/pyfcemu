from memory import *
include "palette.pyx"

ctypedef void (*FUNC)(object)
ctypedef void (*FUNC_b)(object, uint8)

cdef class PPU:
    cdef object console
    cdef int Cycle 
    cdef int ScanLine
    cdef public uint64 Frame
    cdef uint8 paletteData[32]
    cdef uint8 nameTableData[2048]
    cdef uint8 oamData[256]
    cdef uint16 v, t
    cdef uint8 x, w, f, register
    cdef bool nmiOccurred, nmiOutput, nmiPrevious
    cdef uint8 nmiDelay
    cdef uint8 nameTableByte, attributeTableByte, lowTileByte, highTileByte
    cdef uint64 tileData
    cdef int spriteCount
    cdef uint32 spritePatterns[8]
    cdef uint8 spritePositions[8]
    cdef uint8 spritePriorities[8]
    cdef uint8 spriteIndexes[8]
    cdef uint8 flagNameTable, flagIncrement, flagSpriteTable, flagBackgroundTable, flagSpriteSize, flagMasterSlave
    cdef uint8 flagGrayscale, flagShowLeftBackground, flagShowLeftSprites, flagShowBackground, flagShowSprites, flagRedTint, flagGreenTint, flagBlueTint
    cdef uint8 flagSpriteZeroHit, flagSpriteOverflow
    cdef uint8 oamAddress
    cdef uint8 bufferedData
    cdef public object front
    cdef public object back
    cdef FUNC step_func[8]
    cdef FUNC_b write_reg_ops[8]
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

        self.nameTableByte = 0 # byte
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
        self.flagBackgroundTable = 0 # bit
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
        #self.front = np.zeros((240, 256, 3), dtype = np.uint8)
        #self.back = np.zeros((240, 256, 3), dtype = np.uint8)
        self.front = [0 for _ in range(240 * 256 * 3)]
        self.back = [0 for _ in range(240 * 256 * 3)]

        self.Reset()

        '''
        self.step_func = [self.storeTileData, self.fetchNameTableByte, 
                          self.emptyFunc, self.fetchAttributeTableByte, 
                          self.emptyFunc, self.fetchLowTileByte,
                          self.emptyFunc, self.fetchHighTileByte ]

        self.write_reg_ops = [self.writeControl, self.writeMask, self.emptyFunc_b, self.writeOAMAddress, self.writeOAMData, self.writeScroll, self.writeAddress, self.writeData]
        '''
    cdef emptyFunc(self):
        pass
    cdef emptyFunc_b(self, uint8):
        pass
    cdef Reset(self):
        self.Cycle = 340
        self.ScanLine = 240
        self.Frame = 0
        self.writeControl(0)
        self.writeMask(0)
        self.writeOAMAddress(0)

    cdef uint8 Read(self, uint16 address):
        address = address & 0x3FFF
        if address < 0x2000:
            return self.console.Mapper.Read(address)
        elif address < 0x3F00:
            mode = self.console.Cartridge.Mirror
            return self.nameTableData[MirrorAddress(mode, address) & 0x7FF]
        elif address < 0x4000:
            return self.readPalette(address & 0x1F)
        raise RuntimeError("Unhandled PPU Memory read at address: 0x%04X" % address)

    cdef Write(self, uint16 address, uint8 value):
        address = address & 0x3FFF
        if address < 0x2000:
            self.console.Mapper.Write(address, value)
        elif address < 0x3F00:
            mode = self.console.Cartridge.Mirror
            self.nameTableData[MirrorAddress(mode, address) & 0x7FF] = value
        elif address < 0x4000:
            self.writePalette(address & 0x1F, value)
        else:
            raise RuntimeError("Unhandled PPU Memory write at address: 0x%04X" % address)

    cdef uint8 readPalette(self, uint16 address):
        if address >= 16 and address & 0x3 == 0:
            address -= 16
        return self.paletteData[address]

    cdef writePalette(self, uint16 address, uint8 value):
        if address >= 16 and address & 0x3 == 0:
            address -= 16
        self.paletteData[address] = value

    cpdef uint8 readRegister(self, uint16 address):
        if address == 0x2002:
            return self.readStatus()
        elif address == 0x2004:
            return self.readOAMData()
        elif address == 0x2007:
            return self.readData()
        return 0

    cpdef writeRegister(self, uint16 address, uint8 value):
        self.register = value
        if address == 0x4014:
            self.writeDMA(value)
        elif address == 0x2000:
            self.writeControl(value)
        elif address == 0x2001:
            self.writeMask(value)
        elif address == 0x2003:
            self.writeOAMAddress(value)
        elif address == 0x2004:
            self.writeOAMData(value)
        elif address == 0x2005:
            self.writeScroll(value)
        elif address == 0x2006:
            self.writeAddress(value)
        elif address == 0x2007:
            self.writeData(value)
            #self.write_reg_ops[address - 0x2000](value)
        '''
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
        '''

    cdef writeControl(self, uint8 value):
        self.flagNameTable = (value >> 0) & 3
        self.flagIncrement = (value >> 2) & 1
        self.flagSpriteTable = (value >> 3) & 1
        self.flagBackgroundTable = (value >> 4) & 1
        self.flagSpriteSize = (value >> 5) & 1
        self.flagMasterSlave = (value >> 6) & 1
        self.nmiOutput = (((value >> 7) & 1) == 1)
        self.nmiChange()
        self.t = ((self.t & 0xF3FF) | (((value & 0x03) << 10)))

    cdef writeMask(self, uint8 value):
        self.flagGrayscale = (value >> 0) & 1
        self.flagShowLeftBackground = (value >> 1) & 1
        self.flagShowLeftSprites = (value >> 2) & 1
        self.flagShowBackground = (value >> 3) & 1
        self.flagShowSprites = (value >> 4) & 1
        self.flagRedTint = (value >> 5) & 1
        self.flagGreenTint = (value >> 6) & 1
        self.flagBlueTint = (value >> 7) & 1

    cdef uint8 readStatus(self):
        result = self.register & 0x1F
        result |= (self.flagSpriteOverflow << 5)
        result |= (self.flagSpriteZeroHit << 6)
        if self.nmiOccurred:
            result |= (1 << 7)
        self.nmiOccurred = False
        self.nmiChange()
        self.w = 0
        return result

    cdef writeOAMAddress(self, uint8 value):
        self.oamAddress = value

    cdef uint8 readOAMData(self):
        return self.oamData[self.oamAddress]

    cdef writeOAMData(self, uint8 value):
        self.oamData[self.oamAddress] = value
        self.oamAddress = (self.oamAddress + 1) & 0xFF 

    cdef writeScroll(self, uint8 value):
        if self.w == 0:
            self.t = (self.t & 0xFFE0) | (value >> 3) 
            self.x = value & 0x07
            self.w = 1
        else:
            self.t = (self.t & 0x8FFF) | (((value & 0x07) << 12)) 
            self.t = (self.t & 0xFC1F) | (((value & 0xF8) << 2)) 
            # self.t twice!
            self.w = 0

    cdef writeAddress(self, uint8 value):
        if self.w == 0:
            self.t = (self.t & 0x80FF) | (((value & 0x3F) << 8))
            self.w = 1
        else:
            self.t = (self.t & 0xFF00) | value
            self.v = self.t
            self.w = 0

    cdef uint8 readData(self):
        cdef uint8 value = self.Read(self.v)
        cdef uint8 buffered
        if self.v & 0x3FFF < 0x3F00:
            buffered = self.bufferedData
            self.bufferedData = value
            value = buffered
        else:
            self.bufferedData = self.Read((self.v - 0x1000)) 

        if self.flagIncrement == 0:
            self.v = (self.v + 1)
        else:
            self.v = (self.v + 32)
        return value

    cdef writeData(self, uint8 value):
        self.Write(self.v, value)
        if self.flagIncrement == 0:
            self.v = (self.v + 1)
        else:
            self.v = (self.v + 32)

    cdef writeDMA(self, uint8 value):
        cpu = self.console.CPU
        cdef uint16 address = (value << 8)
        for _ in range(256):
            self.oamData[self.oamAddress] = cpu.Read(address)
            self.oamAddress = (self.oamAddress + 1)
            address = (address + 1)
        cpu.stall += 513
        if cpu.Cycles & 1 == 1:
            cpu.stall += 1

    cdef incrementX(self):
        if self.v & 0x001F == 31:
            self.v &= 0xFFE0
            self.v ^= 0x0400
        else:
            self.v = (self.v + 1)

    cdef incrementY(self):
        cdef uint16 y
        if self.v & 0x7000 != 0x7000:
            self.v = (self.v + 0x1000)
        else:
            self.v &= 0x8FFF
            y = (self.v & 0x03E0) >> 5
            if y == 29:
                y = 0
                self.v ^= 0x0800
            elif y == 31:
                y = 0
            else:
                y = (y + 1)
            self.v = (self.v & 0xFC1F) | (y << 5)

    cdef copyX(self):
        self.v = (self.v & 0xFBE0) | (self.t & 0x041F)

    cdef copyY(self):
        self.v = (self.v & 0x841F) | (self.t & 0x7BE0)

    cdef nmiChange(self):
        cdef bool nmi
        nmi = (self.nmiOutput and self.nmiOccurred)
        if nmi and not self.nmiPrevious:
            self.nmiDelay = 15
        self.nmiPrevious = nmi

    cdef setVerticalBlank(self):
        self.front, self.back = self.back, self.front
        self.nmiOccurred = True
        self.nmiChange()

    cdef clearVerticalBlank(self):
        self.nmiOccurred = False
        self.nmiChange()

    cdef fetchNameTableByte(self):
        cdef uint16 v
        v = self.v
        address = 0x2000 | (v & 0x0FFF)
        self.nameTableByte = self.Read(address)

    cdef fetchAttributeTableByte(self):
        cdef uint16 v
        v = self.v
        address = 0x23C0 | (v & 0x0C00) | ((v >> 4) & 0x38) | ((v >> 2) & 0x07) 
        shift = ((v >> 4) & 4) | (v & 2)
        self.attributeTableByte = (((self.Read(address) >> shift) & 3) << 2)

    cdef fetchLowTileByte(self):
        cdef uint8 fineY, table, tile
        cdef uint16 address
        fineY = (self.v >> 12) & 7
        table = self.flagBackgroundTable
        tile = self.nameTableByte
        address = (table << 12) + (tile << 4) + fineY
        self.lowTileByte = self.Read(address)

    cdef fetchHighTileByte(self):
        cdef uint8 fineY, table, tile
        cdef uint16 address_8
        fineY = (self.v >> 12) & 7
        table = self.flagBackgroundTable
        tile = self.nameTableByte
        address_8 = (table << 12) + (tile << 4) + fineY + 8
        self.highTileByte = self.Read(address_8)

    cdef storeTileData(self):
        cdef uint32 data
        cdef uint8 a, p1, p2
        data = 0
        a = self.attributeTableByte
        for i in range(8):
            p1 = (self.lowTileByte & 0x80) >> 7
            p2 = (self.highTileByte & 0x80) >> 6
            self.lowTileByte <<= 1 
            self.highTileByte <<= 1
            data <<= 4
            data |= (a | p1 | p2)
        self.tileData |= data # uint64

    cdef uint8 backgroundPixel(self):
        cdef uint8 data
        if self.flagShowBackground == 0:
            return 0
        data = (self.tileData >> 32)  >> ((7 - self.x) << 2)
        return data & 0x0F

    cdef spritePixel(self): 
        cdef int i
        cdef int offset
        cdef uint8 color
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

    cdef renderPixel(self):
        cdef int x,y
        cdef uint8 background, color
        cdef uint8 i, sprite 
        cdef bool b, s
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

        if not b:
            if not s:
                color = 0
            else:
                # not b and s
                color = sprite | 0x10
        else:
            if not s:
                # b and not s
                color = background
            else:
                # b and s
                if self.spriteIndexes[i] == 0 and x < 255:
                    self.flagSpriteZeroHit = 1 
                if self.spritePriorities[i] == 0:
                    color = sprite | 0x10
                else:
                    color = background

        cdef uint8* c = Palette[self.readPalette(color) & 0x3F]
        cdef int p = (y * 256 + x) * 3
        self.back[p + 0] = c[0]
        self.back[p + 1] = c[1]
        self.back[p + 2] = c[2]

    cdef uint32 fetchSpritePattern(self, int i, int row):
        cdef int k
        cdef uint8 tile, attributes, a
        cdef uint16 address 
        cdef uint8 table, lowTileByte, highTileByte
        cdef uint32 data
        cdef uint8 p1, p2
        k = (i << 2) + 1
        tile = self.oamData[k]
        attributes = self.oamData[k + 1]
        address = 0
        if self.flagSpriteSize == 0:
            if attributes & 0x80 == 0x80:
                row = 7 - row
            table = self.flagSpriteTable
            address = ((table << 12) + (tile << 4) + row)
        else:
            if attributes & 0x80 == 0x80:
                row = 15 - row
            table = tile & 1
            tile &= 0xFE
            if row > 7:
                tile += 1
                row -= 8
            address = ((table << 12)+ (tile << 4) + row)
        a = (attributes & 3) << 2
        lowTileByte = self.Read(address)
        highTileByte = self.Read((address + 8))
        data = 0
        for i in range(8):
            if attributes & 0x40 == 0x40:
                p1 = (lowTileByte & 1)
                p2 = (highTileByte & 1) << 1
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

    cdef evaluateSprites(self):
        cdef int h, count, i
        cdef uint8 y, a, x
        h = 8 if self.flagSpriteSize == 0 else 16
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

    cdef tick(self):
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

    cpdef Step(self):
        cdef bool renderingEnabled, preLine, visibleLine
        cdef bool preFetchCycle, visibleCycle, fetchCycle, renderLine
        cdef uint8 c
        self.tick()

        renderingEnabled = (self.flagShowBackground != 0) or (self.flagShowSprites != 0)
        preLine = (self.ScanLine == 261)
        visibleLine = (self.ScanLine < 240)

        # background logic
        if renderingEnabled:
            preFetchCycle = (self.Cycle >= 321) and (self.Cycle <= 336)
            visibleCycle = (self.Cycle >= 1) and (self.Cycle <= 256)
            fetchCycle = preFetchCycle or visibleCycle
            renderLine = preLine or visibleLine
            if visibleLine and visibleCycle:
                self.renderPixel()
            if renderLine and fetchCycle:
                self.tileData <<= 4
                c = self.Cycle & 0x7
                '''
                self.step_func = [self.storeTileData, self.fetchNameTableByte, 
                                  self.emptyFunc, self.fetchAttributeTableByte, 
                                  self.emptyFunc, self.fetchLowTileByte,
                                  self.emptyFunc, self.fetchHighTileByte ]
                '''
                if c == 0:
                    self.storeTileData()
                elif c == 1:
                    self.fetchNameTableByte()
                elif c == 3:
                    self.fetchAttributeTableByte()
                elif c == 5:
                    self.fetchLowTileByte()
                elif c == 7:
                    self.fetchHighTileByte()
                #self.step_func[c]()

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

