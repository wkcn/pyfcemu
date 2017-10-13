from defines import *
from ctypes import *
from memory import *

class stepInfo:
    def __init__(self):
        self.address = c_ushort()
        self.pc = c_ushort()
        self.mode = c_char()

class CPU:
    def __init__(self, console):
        self.Memory = Memory(console) # Memory Interface
        self.Cycles = c_ulonglong() # Number of Cycles
        self.PC = c_ushort() # Program Counter
        self.SP = c_char() # Stack Pointer
        self.A = c_char() # Accumulator
        self.X = c_char() # X register
        self.Y = c_char() # Y register
        self.C = c_char() # Carry Flag
        self.Z = c_char() # Zero Flag
        self.I = c_char() # Interrupt Disable Flag 
        self.D = c_char() # Decimal Mode Flag 
        self.B = c_char() # Break Command Flag 
        self.U = c_char() # Unused Flag 
        self.V = c_char() # Overflow Flag 
        self.N = c_char() # Negative Flag 
        self.interrupt = c_char() # interrupt type to perform 
        self.stall = c_int() # Number of Cycles to Stall
        self.table = [stepInfo() for _ in range(256)] 
    def createTable(self):
        pass
    def Reset(self):
        pass



def NewCPU(console):
    cpu = CPU(console)
    cpu.createTable()
    cpu.Reset()
    return cpu
