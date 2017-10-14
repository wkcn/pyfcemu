from numpy import *

class Mapper2:
    def __init__(self, cartridge):
        self.prgBanks = len(cartridge.PRG) // 0x4000
        self.prgBank1 = 0
        self.prgBank2 = self.prgBanks - 1 
        self.cartridge = cartridge

    def Save(self, encoder):
        encoder.Encode(self.prgBanks)
        encoder.Encode(self.prgBanks)
        encoder.Encode(self.prgBank2)

    def Load(self, decoder):
        decoder.Decode(self.prgBanks)
        decoder.Decode(self.prgBank1)
        decoder.Decode(self.prgBank2)

    def Step(self):
        pass

    def Read(self, address):
        if address < 0x2000:
            return self.cartridge.CHR[address]
        elif address >= 0xC000:
            index = self.prgBank2 * 0x4000 + int(address - uint16(0xC000))
            return self.cartridge.PRG[index]
        elif address >= 0x8000:
            index = self.prgBank1 * 0x4000 + int(address - uint16(0x8000))
            return self.cartridge.PRG[index]
        elif address >= 0x6000:
            return self.cartridge.SRAM[int(address) - 0x6000]
        else:
            raise ("Unhandled Mapper2 read at address: 0x%04X" % address)

    def Write(self, address, value):
        if address < 0x2000:
            self.cartridge.CHR[address] = value
        elif address >= 0x8000:
            self.prgBank1 = int(value) % self.prgBanks
        elif address >= 0x6000:
            index = int(address) - 0x6000
            self.cartridge.SRAM[index] = value
        else:
            raise ("Unhandled Mapper2 write at address: 0x%04X" % address)
