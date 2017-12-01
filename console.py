from controller import *
from ines import *
from mapper import *
from cpu import *
from apu import *
from ppu import *
import time

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

    def Reset(self):
        self.CPU.Reset()
    
    def Step(self):
        #ot = time.time()
        cpuCycles = self.CPU.Step()
        ppuCycles = cpuCycles * 3
        for i in range(ppuCycles):
            self.PPU.Step()
            self.Mapper.Step()
        #for i in range(cpuCycles):
        #    self.APU.Step()
        '''
        dt = time.time() - ot
        if dt > 0:
            f = cpuCycles * 1.0 / dt
            r = f / 17897.725
            print ("Hz: ", f, r, r > 100)
        '''
        return cpuCycles

    def StepFrame(self):
        cpuCycles = 0
        frame = self.PPU.Frame
        while frame == self.PPU.Frame:
            cpuCycles += self.Step()
        return cpuCycles

    def StepSeconds(self, seconds):
        cycles = int(CPUFrequency * seconds)
        while cycles > 0:
            cycles -= self.Step()

    def Buffer(self):
        return self.PPU.front 

    def BackgroundColor(self):
        return Palette[self.PPU.readPalette(0) & 0x3F]

    def SetAudioChannel(self, channel):
        self.APU.channel = channel

    def SetAudioSampleRate(self, sampleRate):
        # TODO
        self.APU.sampleRate = CPUFrequency / sampleRate

    def SetButtons1(self, buttons):
        self.Controller1.SetButtons(buttons)
    def SetButtons2(self, buttons):
        self.Controller2.SetButtons(buttons)



def NewConsole(path):
    cartridge, err = LoadNESFile(path)
    ram = [0 for _ in range(2048)] 
    controller1 = Controller()
    controller2 = Controller()

    console = Console()
    console.Cartridge = cartridge
    console.Controller1 = controller1
    console.Controller2 = controller2
    console.RAM = ram

    mapper, err = NewMapper(console)

    console.Mapper = mapper
    console.CPU = NewCPU(console)
    console.APU = APU(console)
    console.PPU = PPU(console)
    
    return console, None
