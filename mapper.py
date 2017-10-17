class Mapper:
    def Read(self, address):
        pass
    def Write(self, address, value):
        pass
    def Step(self):
        pass
    def Save(self, encoder):
        pass
    def Load(self, decoder):
        pass

from mapper1 import *
from mapper2 import *
from mapper3 import *
from mapper4 import *
from mapper7 import *

Mappers = {
        0: Mapper2,
        1: Mapper1,
        2: Mapper2,
        3: Mapper3,
        4: Mapper4,
        7: Mapper7
}

def NewMapper(console):
    cartridge = console.Cartridge
    if cartridge.Mapper not in Mappers:
        raise RuntimeError("Unsupported Mapper: %d" % cartridge.Mapper)
    m = Mappers[cartridge.Mapper]
    if m == Mapper4:
        return m(console, cartridge), None
    return m(cartridge), None
