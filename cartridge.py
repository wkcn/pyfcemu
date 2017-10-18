import numpy as np

class Cartridge:
    def __init__(self, prg, _chr, mapper, mirror, battery):
        self.PRG = prg
        self.CHR = _chr
        self.SRAM = np.zeros(0x2000, dtype = np.uint8)
        self.Mapper = mapper
        self.Mirror = mirror
        self.Battery = battery

    def Save(self, encoder):
        encoder.Encode(self.SRAM)
        encoder.Encode(self.Mirror)

    def Load(self, decoder):
        decoder.Decode(self.SRAM)
        decoder.Decode(self.Mirror)
