from defines import *

def modeAbsoluteFunc(cpu):
    cpu.address = cpu.Read16((cpu.PC + 1) & 0xFFFF)

def modeAbsoluteXFunc(cpu):
    cpu.address = (cpu.Read16((cpu.PC + 1) & 0xFFFF) + cpu.X) & 0xFFFF
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.X) & 0xFFFF, cpu.address)

def modeAbsoluteYFunc(cpu):
    cpu.address = (cpu.Read16((cpu.PC + 1) & 0xFFFF) + cpu.Y) & 0xFFFF
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.Y) & 0xFFFF, cpu.address)

def modeAccumulatorFunc(cpu):
    cpu.address = 0

def modeImmediateFunc(cpu):
    cpu.address = (cpu.PC + 1) & 0xFFFF

def modeImpliedFunc(cpu):
    cpu.address = 0

def modeIndexedIndirectFunc(cpu):
    cpu.address = cpu.read16bug((cpu.Read((cpu.PC + 1) & 0xFFFF) + cpu.X) & 0xFFFF)

def modeIndirectFunc(cpu):
    cpu.address = cpu.read16bug(cpu.Read16((cpu.PC + 1) & 0xFFFF))

def modeIndirectIndexedFunc(cpu):
    cpu.address = (cpu.read16bug(cpu.Read((cpu.PC + 1) & 0xFFFF)) + cpu.Y) & 0xFFFF
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.Y) & 0xFFFF, cpu.address)

def modeRelativeFunc(cpu):
    offset = cpu.Read((cpu.PC + 1) & 0xFFFF)
    if offset < 0x80:
        cpu.address = (cpu.PC + 2 + offset) & 0xFFFF
    else:
        cpu.address = (cpu.PC + 2 + offset - 0x100) & 0xFFFF

def modeZeroPageFunc(cpu):
    cpu.address = cpu.Read((cpu.PC + 1) & 0xFFFF)

def modeZeroPageX(cpu):
    cpu.address = (cpu.Read((cpu.PC + 1) & 0xFFFF) + cpu.X) & 0xFFFF

def modeZeroPageY(cpu):
    cpu.address = (cpu.Read((cpu.PC + 1) & 0xFFFF) + cpu.Y) & 0xFFFF
