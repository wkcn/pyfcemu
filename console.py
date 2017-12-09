# cython: profile=True
from controller import *
from ines import *
from mapper import *
from cpu import CPU
from apu import APU
from ppu import PPU

import time


class Console:
    '''
    cdef object Cartridge, Controller1, Controller2, Mapper, RAM 
    cdef CPU CPU
    cdef APU APU 
    cdef PPU PPU 
    '''
    def __init__(self, path):

        cartridge, err = LoadNESFile(path)
        ram = [0 for _ in range(2048)] 
        controller1 = Controller()
        controller2 = Controller()

        self.Cartridge = cartridge
        self.Controller1 = controller1
        self.Controller2 = controller2
        self.RAM = ram

        mapper, err = NewMapper(self)

        self.Mapper = mapper
        self.CPU = CPU(self)
        self.APU = APU(self)
        self.PPU = PPU(self)

    def Reset(self):
        self.CPU.Reset()
    
    def Step(self):
        '''
        cdef int i
        cdef int cpuCycles, ppuCycles
        '''
        #ot = time.time()
        cpuCycles = self.CPU.Step()
        ppuCycles = cpuCycles * 3
        for i in range(ppuCycles):
            self.PPU.Step()
            self.Mapper.Step()
        for i in range(cpuCycles):
            self.APU.Step()
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
