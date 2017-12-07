ctypedef unsigned long long uint64
ctypedef unsigned int uint32
ctypedef unsigned short uint16
ctypedef unsigned char uint8

cdef class Mapper2:
    cdef int prgBanks, prgBank1, prgBank2
    cdef object cartridge
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

    cpdef uint8 Read(self, uint16 address):
        if address < 0x2000:
            return self.cartridge.CHR[address]
        elif address >= 0xC000:
            #index = self.prgBank2 * 0x4000 + ((address - 0xC000) & 0xFFFF)
            index = (self.prgBank2 << 14)+ ((address - 0xC000) & 0xFFFF)
            return self.cartridge.PRG[index]
        elif address >= 0x8000:
            #index = self.prgBank1 * 0x4000 + ((address - 0x8000) & 0xFFFF)
            index = (self.prgBank1 << 14) + ((address - 0x8000) & 0xFFFF)
            return self.cartridge.PRG[index]
        elif address >= 0x6000:
            return self.cartridge.SRAM[address - 0x6000]
        else:
            raise ("Unhandled Mapper2 read at address: 0x%04X" % address)

    cpdef Write(self, uint16 address, uint8 value):
        if address < 0x2000:
            self.cartridge.CHR[address] = value
        elif address >= 0x8000:
            self.prgBank1 = value % self.prgBanks
        elif address >= 0x6000:
            index = address - 0x6000
            self.cartridge.SRAM[index] = value
        else:
            raise ("Unhandled Mapper2 write at address: 0x%04X" % address)
