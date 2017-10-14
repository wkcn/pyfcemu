from numpy import *
from controller import *
from ines import *
from mapper import *
from cpu import *
from apu import *
from ppu import *

class Console:
    def __init__(self):
        self.CPU = None
        self.APU = None
        self.PPU = None
        self.Cartridge = None
        self.Controller1 = None
        self.Controller2 = None
        self.Mapper = None
        self.RAM = None

def NewConsole(path):
    cartridge, err = LoadNESFile(path)
    ram = zeros(2048).astype(byte) 
    controller1 = NewController()
    controller2 = NewController()

    console = Console()
    console.Cartridge = cartridge
    console.Controller1 = controller1
    console.Controller2 = controller2
    console.RAM = ram

    mapper, err = NewMapper(console)

    console.Mapper = mapper
    console.CPU = NewCPU(console)
    console.APU = NewAPU(console)
    console.PPU = NewPPU(console)
    
    return console, None
