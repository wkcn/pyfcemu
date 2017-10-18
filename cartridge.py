class Cartridge:
    def __init__(self, prg, _chr, mapper, mirror, battery):
        self.PRG = prg
        self.CHR = _chr
        self.SRAM = [0 for _ in range(0x2000)] 
        self.Mapper = mapper
        self.Mirror = mirror
        self.Battery = battery

    def Save(self, encoder):
        encoder.Encode(self.SRAM)
        encoder.Encode(self.Mirror)

    def Load(self, decoder):
        decoder.Decode(self.SRAM)
        decoder.Decode(self.Mirror)
