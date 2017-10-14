from numpy import *

def modeAbsoluteFunc(cpu):
    cpu.address = cpu.Read16(cpu.PC + uint16(1))

def modeAbsoluteXFunc(cpu):
    cpu.address = cpu.Read16(cpu.PC + uint16(1)) + cpu.X
    cpu.pageCrossed = cpu.pagesDiffer(cpu.address - cpu.X, cpu.address)

def modeAbsoluteYFunc(cpu):
    cpu.address = cpu.Read16(cpu.PC + uint16(1)) + cpu.Y   
    cpu.pageCrossed = cpu.pagesDiffer(cpu.address - cpu.Y, cpu.address)

def modeAccumulatorFunc(cpu):
    cpu.address = uint16(0)

def modeImmediateFunc(cpu):
    cpu.address = cpu.PC + uint16(1)

def modeImpliedFunc(cpu):
    cpu.address = uint16(0)

def modeIndexedIndirectFunc(cpu):
    cpu.address = cpu.read16bug(uint16(cpu.Read(cpu.PC + uint16(1))) + cpu.X)

def modeIndirectFunc(cpu):
    cpu.address = cpu.read16bug(cpu.Read16(cpu.PC + uint16(1)))

def modeIndirectIndexedFunc(cpu):
    cpu.address = cpu.read16bug(uint16(cpu.Read(cpu.PC + uint16(1))) + uint16(cpu.Y))
    cpu.pageCrossed = cpu.pagesDiffer(cpu.address - uint16(cpu.Y), cpu.address)

def modeRelativeFunc(cpu):
    offset = uint16(cpu.Read(cpu.PC + uint16(1)))
    if offset < 0x80:
        cpu.address = cpu.PC + uint16(2) + offset
    else:
        cpu.address = cpu.PC + uint16(2) + offset - uint16(0x100)

def modeZeroPageFunc(cpu):
    cpu.address = uint16(cpu.Read(cpu.PC + uint16(1)))

def modeZeroPageX(cpu):
    cpu.address = uint16(cpu.Read(cpu.PC + uint16(1)) + cpu.X)

def modeZeroPageY(cpu):
    cpu.address = uint16(cpu.Read(cpu.PC + uint16(1)) + cpu.Y)
