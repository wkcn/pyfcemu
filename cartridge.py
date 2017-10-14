from numpy import * 

class Cartridge:
    def __init__(self, prg, _chr, mapper, mirror, battery):
        self.PRG = prg
        self.CHR = _chr
        self.SRAM = zeros(0x2000).astype(byte)
        self.Mapper = mapper
        self.Mirror = mirror
        self.Battery = battery

    def Save(self, encoder):
        encoder.Encode(self.SRAM)
        encoder.Encode(self.Mirror)

    def Load(self, decoder):
        decoder.Decode(self.SRAM)
        decoder.Decode(self.Mirror)
