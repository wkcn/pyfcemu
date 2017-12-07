from defines import *

cpdef modeAbsoluteFunc(cpu):
    cpu.address = cpu.Read16(cpu.PC + 1)

cpdef modeAbsoluteXFunc(cpu):
    cpu.address = (cpu.Read16((cpu.PC + 1)) + cpu.X)
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.X), cpu.address)

cpdef modeAbsoluteYFunc(cpu):
    cpu.address = (cpu.Read16((cpu.PC + 1)) + cpu.Y)
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.Y), cpu.address)

cpdef modeAccumulatorFunc(cpu):
    cpu.address = 0

cpdef modeImmediateFunc(cpu):
    cpu.address = (cpu.PC + 1)

cpdef modeImpliedFunc(cpu):
    cpu.address = 0

cpdef modeIndexedIndirectFunc(cpu):
    cpu.address = cpu.read16bug((cpu.Read((cpu.PC + 1)) + cpu.X))

cpdef modeIndirectFunc(cpu):
    cpu.address = cpu.read16bug(cpu.Read16((cpu.PC + 1)))

cpdef modeIndirectIndexedFunc(cpu):
    cpu.address = (cpu.read16bug(cpu.Read((cpu.PC + 1))) + cpu.Y)
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.Y), cpu.address)

cpdef modeRelativeFunc(cpu):
    offset = cpu.Read((cpu.PC + 1))
    if offset < 0x80:
        cpu.address = (cpu.PC + 2 + offset)
    else:
        cpu.address = (cpu.PC + 2 + offset - 0x100)

cpdef modeZeroPageFunc(cpu):
    cpu.address = cpu.Read((cpu.PC + 1))

cpdef modeZeroPageXFunc(cpu):
    cpu.address = (cpu.Read((cpu.PC + 1)) + cpu.X)

cpdef modeZeroPageYFunc(cpu):
    cpu.address = (cpu.Read((cpu.PC + 1)) + cpu.Y)
