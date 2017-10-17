from numpy import *
from memory import *

MIRRORS = [
        MirrorSingle0,
        MirrorSingle1,
        MirrorVertical,
        MirrorHorizontal
]

class Mapper1:
    def __init__(self, cartridge):
        self.cartridge = cartridge
        self.shiftRegister = uint8(0x10)
        self.control = uint8()
        self.prgMode = uint8()
        self.chrMode = uint8()
        self.prgBank = uint8()
        self.chrBank0 = uint8()
        self.chrBank1 = uint8()
        self.prgOffsets = [0,0]
        self.chrOffsets = [0,0]
        self.prgOffsets[1] = m.prgBankOffset(-1)

    def Read(self, address):
        if address < 0x2000:
            bank = address // uint16(0x1000)
            offset = address % uint16(0x1000)
            return self.cartridge.CHR[self.chrOffsets[bank] + int(offset)]
        elif address >= 0x8000:
            address -= uint16(0x8000)
            bank = address // uint16(0x4000)
            offset = address % uint16(0x4000)
            return self.cartridge.PRG[self.prgOffsets[bank] + int(offset)]
        elif address >= 0x6000:
            return self.cartridge.SRAM[int(address) - 0x6000]
        else:
            raise RuntimeError("Unhandled Mapper1 read at address: 0x%4X" % address)

    def Write(self, address, value):
        if address < 0x2000:
            bank = address // uint16(0x1000)
            offset = address % uint16(0x1000)
            self.cartridge.CHR[self.chrOffsets[bank] + int(offset)] = value
        elif address >= 0x8000:
            self.loadRegister(address, value)
        elif address >= 0x6000:
            self.cartridge.SRAM[int(address) - 0x6000] = value
        else:
            raise RuntimeError("Unhandled Mapper1 write at address: 0x%4X" % address)

    def loadRegister(address, value):
        if value & 0x80 == 0x80:
            self.shiftRegister = uint8(0x10)
            self.writeControl(self.control | uint8(0x0C))
        else:
            complete = (self.shiftRegister & uint8(1)) == 1
            self.shiftRegister >>= uint8(1)
            self.shiftRegister |= (value & uint8(1)) << uint8(4)
            if complete:
                self.writeRegister(address, self.shiftRegister)
                self.shiftRegister = uint8(0x10)
    def writeRegister(self, address, value):
        if address <= 0x9FFF:
            self.writeControl(value)
        elif address <= 0xBFFF:
            self.writeCHRBank0(value)
        elif address <= 0xDFFF:
            self.writeCHRBank1(value)
        elif address <= 0xFFFF:
            self.writePRGBank(value)

    # Control (internal, $8000-$9FFF)
    def writeControl(self, value):
        self.control = value
        self.chrMode = (value >> uint8(4)) & uint8(1)
        self.prgMode = (value >> uint8(2)) & uint8(3)
        mirror = value & uint8(3)
        self.cartridge.Mirror = MIRRORS[mirror]
        self.updateOffsets()

    def writeCHRBank0(self, value):
        self.chrBank0 = value
        self.updateOffsets()

    def writeCHRBank1(self, value):
        self.chrBank1 = value
        self.updateOffsets()

    def writePRGBank(self, value):
        self.preBank = value & uint8(0x0F)
        self.updateOffsets()

    def preBankOffset(self, index):
        if index >= 0x80:
            index -= 0x100
        index %= len(self.cartridge.PRG) // 0x4000
        offset = index * 0x4000
        if offset < 0:
            offset += len(self.cartridge.PRG)
        return offset

    def chrBankOffset(self, index):
        if index >= 0x80:
            index -= 0x100
        index %= (len(self.cartridge.CHR) // 0x1000)
        offset = index * 0x1000
        if offset < 0:
            offset += len(self.cartridge.CHR)
        return offset

    def updateOffsets(self):
        if self.prgMode in [0, 1]:
            self.prgOffsets[0] = self.prgBankOffset(int(self.prgBank & uint8(0xFE)))
            self.prgOffsets[1] = self.prgBankOffset(int(self.prgBank & uint8(0x01)))
        elif self.prgMode == 2:
            self.prgOffsets[0] = 0
            self.prgOffsets[1] = self.preBankOffset(int(self.prgBank))
        elif self.prgMode == 3:
            self.prgOffsets[0] = self.prgBankOffset(int(self.prgBank))
            self.prgOffsets[1] = self.prgBankOffset(-1)

        if self.chrMode == 0:
            self.chrOffsets[0] = self.chrBankOffset(int(self.chrBank0 & uint8(0xFE)))
            self.chrOffsets[1] = self.chrBankOffset(int(self.chrBank1 & uint8(0x01)))
        elif self.chrMode == 1:
            self.chrOffsets[0] = self.chrBankOffset(int(self.chrBank0))
            self.chrOffsets[1] = self.chrBankOffset(int(self.chrBank1))

    def Step(self):
        pass
    def Save(self, encoder):
        pass
    def Load(self, decoder):
        pass

