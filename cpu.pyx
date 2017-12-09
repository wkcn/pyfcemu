# cython: profile=True
from defines import *
from memory import *
include "cdefines.pyx" 

ctypedef void (*cpu_op_func)(CPU, stepInfo)   
cdef cpu_op_func cpu_op_table[256]
ctypedef void (*cpu_mode_func)(CPU)
cdef cpu_mode_func cpu_mode_table[14]

cdef class stepInfo:
    cdef uint16 address
    cdef uint16 pc
    cdef uint8 mode
    def __init__(self, address = None, pc = None, mode = None):
        self.address = address
        self.pc = pc
        self.mode = mode 

cdef class CPU:
    cdef object Memory
    cdef public uint64 Cycles
    cdef uint16 PC
    cdef uint8 SP, A, X, Y, C, Z, I, D, B, U, V, N, interrupt
    cdef public int stall
    cdef public uint16 address
    cdef public bool pageCrossed
    cdef object console
    def __init__(self, console):
        self.Memory = None # Memory Interface
        self.Cycles = 0 # Number of Cycles
        self.PC = 0 # Program Counter
        self.SP = 0 # Stack Pointer
        self.A = 0 # Accumulator
        self.X = 0 # X register
        self.Y = 0 # Y register
        self.C = 0 # Carry Flag
        self.Z = 0 # Zero Flag
        self.I = 0 # Interrupt Disable Flag 
        self.D = 0 # Decimal Mode Flag 
        self.B = 0 # Break Command Flag 
        self.U = 0 # Unused Flag 
        self.V = 0 # Overflow Flag 
        self.N = 0 # Negative Flag 
        self.interrupt = 0 # interrupt type to perform 
        self.stall = 0 # Number of Cycles to Stall
        self.address = 0
        self.pageCrossed = False 
        self.console = console

        self.Reset()

    cdef void PrintInstruction(cpu):
        opcode = cpu.Read(cpu.PC)
        _bytes = instructionSizes[opcode]
        name = instructionNames[opcode]
        w0 = ("%02X"% cpu.Read(cpu.PC+0))
        w1 = ("%02X"% cpu.Read(cpu.PC+1))
        w2 = ("%02X"% cpu.Read(cpu.PC+2))
        if _bytes < 2:
            w1 = "  "
        if _bytes < 3:
            w2 = "  "
        print(
            "%.4X  %s %s %s  %6s A:%02X X:%02X Y:%02X P:%02X SP:%02X CYC:%3d" % (cpu.PC, w0, w1, w2, name,
            cpu.A, cpu.X, cpu.Y, cpu.Flags(), cpu.SP, (cpu.Cycles*3)%341))


    cpdef void Reset(self):
        self.PC = self.Read16(0xFFFC)
        self.SP = 0xFD
        self.SetFlags(0x24)

    # pagesDiffer returns true if the two addresses reference different pages
    cdef bool pagesDiffer(self, uint16 a, uint16 b):
        return (a & 0xFF00) != (b & 0xFF00)

    # addBranchCycles adds a cycle for taking a branch and adds another cycle
    # if the branch jumps to a new page
    cdef void addBranchCycles(self, stepInfo info):
        self.Cycles += 1 
        if self.pagesDiffer(info.pc, info.address):
            self.Cycles += 1

    cdef void compare(self, uint8 a, uint8 b):
        self.setZN((a - b))
        self.C = 1 if a >= b else 0
    
    cpdef uint8 Read(self, uint16 address):
        if address < 0x2000:
            return self.console.RAM[address & 0x07FF]
        elif address < 0x4000:
            return self.console.PPU.readRegister(0x2000 | (address & 0x7))
        elif address == 0x4014:
            return self.console.PPU.readRegister(address)
        elif address == 0x4015:
            return self.console.APU.readRegister(address)
        elif address == 0x4016:
            return self.console.Controller1.Read()
        elif address == 0x4017:
            return self.console.Controller2.Read() 
        elif address < 0x6000:
            pass # [TODO] I/O registers
        elif address >= 0x6000:
            return self.console.Mapper.Read(address)
        return 0

    cdef void Write(self, uint16 address, uint8 value):
        if address < 0x2000:
            self.console.RAM[address & 0x07FF] = value
        elif address < 0x4000:
            self.console.PPU.writeRegister(0x2000 | (address & 0x7), value)
        elif address < 0x4014:
            self.console.APU.writeRegister(address, value)
        elif address == 0x4014:
            self.console.PPU.writeRegister(address, value)
        elif address == 0x4015:
            self.console.APU.writeRegister(address, value)
        elif address == 0x4016:
            self.console.Controller1.Write(value)
            self.console.Controller2.Write(value)
        elif address == 0x4017:
            self.console.APU.writeRegister(address, value)
        elif address < 0x6000:
            pass # [TODO] I/O registers
        elif address >= 0x6000:
            self.console.Mapper.Write(address, value)

    # Read16 reads two uint8s using Read to return a double-word value
    cdef uint16 Read16(self, uint16 address):
        lo = self.Read(address)
        hi = self.Read((address + 1))
        return (hi << 8) | lo

    # read16bug emulates a 6502 bug that caused the low uint8 to wrap without
    cdef uint16 read16bug(self, uint16 address):
        a = address
        b = (a & 0xFF00) | ((a + 1) & 0xFF)
        lo = self.Read(a)
        hi = self.Read(b)
        return (hi << 8) | lo

    # push pushes a uint8 onto the stack
    cdef void push(self, uint8 value):
        self.Write(0x100 | self.SP, value)
        self.SP = (self.SP - 1) & 0xFF 

    # pull pops a uint8 from the stack
    cdef uint8 pull(self):
        self.SP = (self.SP + 1) & 0xFF 
        return self.Read(0x100 | self.SP)

    # push16 pushes two uint8s onto the stack
    cdef void push16(self, uint16 value):
        cdef uint8 hi, lo
        hi = value >> 8
        lo = value & 0xFF
        self.push(hi)
        self.push(lo)

    # pull16 pops two uint8s from the stack
    cdef uint16 pull16(self):
        cdef uint16 lo, hi
        lo = self.pull()
        hi = self.pull()
        return (hi << 8) | lo

    cpdef uint64 Step(self):
        cdef uint64 cycles
        cdef uint8 opcode
        if self.stall > 0:
            self.stall -= 1
            return 1

        cycles = self.Cycles

        if self.interrupt == interruptNMI:
            self.nmi()
        elif self.interrupt == interruptIRQ:
            self.irq()

        self.interrupt = interruptNone

        '''
        print ("PC: %4x" % self.PC)
        print ("Memory: ")
        s = ""
        for i in range(16):
            s += "%.2X " % self.Read(self.PC + uint16(i))
        print (s)
        input()
        '''
        opcode = self.Read(self.PC)
        mode = instructionModes[opcode]

        cpu_mode_table[mode](self)

        #self.PrintInstruction()
        self.PC += instructionSizes[opcode]
        self.Cycles += instructionCycles[opcode]

        if self.pageCrossed:
            self.Cycles += instructionPageCycles[opcode]

        info = stepInfo(self.address, self.PC, mode)
        cpu_op_table[opcode](self, info)

        '''
        s = ""
        for i in range(16):
            s += "%.2X " % self.Read(self.PC + uint16(i))
        print (self.Cycles, cycles, "%.4X" % self.PC, "%.2X" % opcode, mode, s)
        '''
        return self.Cycles - cycles
    
    # NMI - Non-Maskable Interrupt
    cdef void nmi(self):
        self.push16(self.PC)
        php(self, None)
        self.PC = self.Read16(0xFFFA)
        self.I = 1
        self.Cycles += 7 

    # IRQ - IRQ Interrupt
    cdef void irq(self):
        self.push16(self.PC)
        php(self, None)
        self.PC = self.Read16(0xFFFE)
        self.I = 1
        self.Cycles += 7

    cdef uint8 Flags(self):
        flags = 0
        flags |= (self.C << 0)
        flags |= (self.Z << 1)
        flags |= (self.I << 2)
        flags |= (self.D << 3)
        flags |= (self.B << 4)
        flags |= (self.U << 5)
        flags |= (self.V << 6)
        flags |= (self.N << 7)

        return flags

    # SetFlags sets the processor status flags
    cdef void SetFlags(self, uint8 flags):
        self.C = (flags >> 0) & 1
        self.Z = (flags >> 1) & 1
        self.I = (flags >> 2) & 1
        self.D = (flags >> 3) & 1
        self.B = (flags >> 4) & 1
        self.U = (flags >> 5) & 1
        self.V = (flags >> 6) & 1
        self.N = (flags >> 7) & 1

    # setZ sets the zero flag if the argument is zero
    cdef void setZ(self, uint8 value):
        self.Z = 1 if value == 0 else 0

    # setN sets the negative flag if the argument is negative (high bit is set)
    cdef void setN(self, uint8 value):
        self.N = 1 if value & 0x80 != 0 else 0

    # setZN sets the zero flag and the negative flag
    cdef void setZN(self, uint8 value):
        self.setZ(value)
        self.setN(value)

    # triggerNMI causes a non-maskable interrupt to occur on the next cycle
    cpdef void triggerNMI(self):
        self.interrupt = interruptNMI

    # triggerIRQ causes an IRQ interrupt to occur on the next cycle
    cpdef void triggerIRQ(self):
        if self.I == 0:
            self.interrupt = interruptIRQ

cdef void cpu_mode_empty(CPU cpu):
    pass

cdef void modeAbsoluteFunc(CPU cpu):
    cpu.address = cpu.Read16(cpu.PC + 1)

cdef void modeAbsoluteXFunc(CPU cpu):
    cpu.address = (cpu.Read16((cpu.PC + 1)) + cpu.X)
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.X), cpu.address)

cdef void modeAbsoluteYFunc(CPU cpu):
    cpu.address = (cpu.Read16((cpu.PC + 1)) + cpu.Y)
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.Y), cpu.address)

cdef void modeAccumulatorFunc(CPU cpu):
    cpu.address = 0

cdef void modeImmediateFunc(CPU cpu):
    cpu.address = (cpu.PC + 1)

cdef void modeImpliedFunc(CPU cpu):
    cpu.address = 0

cdef void modeIndexedIndirectFunc(CPU cpu):
    cpu.address = cpu.read16bug((cpu.Read((cpu.PC + 1)) + cpu.X))

cdef void modeIndirectFunc(CPU cpu):
    cpu.address = cpu.read16bug(cpu.Read16((cpu.PC + 1)))

cdef void modeIndirectIndexedFunc(CPU cpu):
    cpu.address = (cpu.read16bug(cpu.Read((cpu.PC + 1))) + cpu.Y)
    cpu.pageCrossed = cpu.pagesDiffer((cpu.address - cpu.Y), cpu.address)

cdef void modeRelativeFunc(CPU cpu):
    offset = cpu.Read((cpu.PC + 1))
    if offset < 0x80:
        cpu.address = (cpu.PC + 2 + offset)
    else:
        cpu.address = (cpu.PC + 2 + offset - 0x100)

cdef void modeZeroPageFunc(CPU cpu):
    cpu.address = cpu.Read((cpu.PC + 1))

cdef void modeZeroPageXFunc(CPU cpu):
    cpu.address = (cpu.Read((cpu.PC + 1)) + cpu.X)

cdef void modeZeroPageYFunc(CPU cpu):
    cpu.address = (cpu.Read((cpu.PC + 1)) + cpu.Y)

# CPU OP

# ADC - Add with Carry
cdef void adc(CPU self, stepInfo info):
    a = self.A
    b = self.Read(info.address)
    c = self.C
    self.A = (a + b + c) & 0xFF
    self.setZN(self.A)
    self.C = 1 if a + b + c > 0xFF else 0
    self.V = 1 if (a ^ b) & 0x80 == 0 and (a ^ self.A) & 0x80 != 0 else 0

# AND - Logical AND
cdef void _and(CPU self, stepInfo info):
    self.A = (self.A & self.Read(info.address))
    self.setZN(self.A)

# ASL - Arithmetic Shift Left
cdef void asl(CPU self, stepInfo info):
    if info.mode == modeAccumulator:
        self.C = (self.A >> 7) & 1
        self.A = (self.A << 1) & 0xFF 
        self.setZN(self.A)
    else:
        value = self.Read(info.address)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF 
        self.Write(info.address, value)
        self.setZN(value)

# BCC - Branch if Carry Clear
cdef void bcc(CPU self, stepInfo info):
    if self.C == 0:
        self.PC = info.address
        self.addBranchCycles(info)

# BCS - Branch if Carry Set
cdef void bcs(CPU self, stepInfo info):
    if self.C != 0:
        self.PC = info.address
        self.addBranchCycles(info)

# BEQ - Branch if Equal
cdef void beq(CPU self, stepInfo info):
    if self.Z != 0:
        self.PC = info.address
        self.addBranchCycles(info)

# BIT - Bit Test
cdef void bit(CPU self, stepInfo info):
    value = self.Read(info.address)
    self.V = (value >> 6) & 1
    self.setZ(value & self.A)
    self.setN(value)
    
# BMI - Branch if Minus
cdef void bmi(CPU self, stepInfo info):
    if self.N != 0:
        self.PC = info.address
        self.addBranchCycles(info)

# BNE - Branch if Not Equal
cdef void bne(CPU self, stepInfo info):
    if self.Z == 0:
        self.PC = info.address
        self.addBranchCycles(info)

# BPL - Branch if Positive
cdef void bpl(CPU self, stepInfo info):
    if self.N == 0:
        self.PC = info.address
        self.addBranchCycles(info)

# BRK - Force Interrupt
cdef void brk(CPU self, stepInfo info):
    self.push16(self.PC)
    php(self, info)
    sei(self, info)
    self.PC = self.Read16(0xFFFE)

# BVC - Branch if Overflow Clear
cdef void bvc(CPU self, stepInfo info):
    if self.V == 0:
        self.PC = info.address
        self.addBranchCycles(info)

# BVS - Branch if Overflow Set
cdef void bvs(CPU self, stepInfo info):
    if self.V != 0:
        self.PC = info.address
        self.addBranchCycles(info)

# CLC - Clear Carray Flag
cdef void clc(CPU self, stepInfo info):
    self.C = 0

# CLD - Clear Decimal Mode
cdef void cld(CPU self, stepInfo info):
    self.D = 0

# CLI - Clear Interrupt Disable
cdef void cli(CPU self, stepInfo info):
    self.I = 0

# CLV - Clear Overflow Flag
cdef void clv(CPU self, stepInfo info):
    self.V = 0

# CMP - Compare
cdef void _cmp(CPU self, stepInfo info):
    value = self.Read(info.address)
    self.compare(self.A, value)

# CPX - Compare X Register
cdef void cpx(CPU self, stepInfo info):
    value = self.Read(info.address)
    self.compare(self.X, value)

# CPY - Compare Y Register
cdef void cpy(CPU self, stepInfo info):
    value = self.Read(info.address)
    self.compare(self.Y, value)

# DEC - Decrement Memory
cdef void dec(CPU self, stepInfo info):
    value = (self.Read(info.address) - 1) & 0xFF 
    self.Write(info.address, value)
    self.setZN(value)

# DEX - Decrement X Register
cdef void dex(CPU self, stepInfo info):
    self.X = (self.X - 1) & 0xFF
    self.setZN(self.X)

# DEY - Decrement Y Register
cdef void dey(CPU self, stepInfo info):
    self.Y = (self.Y - 1) & 0xFF
    self.setZN(self.Y)

# EOR - Exclusive OR
cdef void eor(CPU self, stepInfo info):
    self.A = self.A ^ self.Read(info.address)
    self.setZN(self.A)

# INC - Increment Memory
cdef void inc(CPU self, stepInfo info):
    value = (self.Read(info.address) + 1) & 0xFF
    self.Write(info.address, value)
    self.setZN(value)

# INX - Increment X Register
cdef void inx(CPU self, stepInfo info):
    self.X = (self.X + 1) & 0xFF
    self.setZN(self.X)

# INY - Increment Y Register
cdef void iny(CPU self, stepInfo info):
    self.Y = (self.Y + 1) & 0xFF
    self.setZN(self.Y)

# JMP - Jump
cdef void jmp(CPU self, stepInfo info):
    self.PC = info.address

# JSR - Jump to Subroutine
cdef void jsr(CPU self, stepInfo info):
    self.push16((self.PC - 1))
    self.PC = info.address

# LDA - Load Accumulator
cdef void lda(CPU self, stepInfo info):
    self.A = self.Read(self.address)
    self.setZN(self.A)

# LDX - Load X Register
cdef void ldx(CPU self, stepInfo info):
    self.X = self.Read(self.address)
    self.setZN(self.X)

# LDY - Load Y Register
cdef void ldy(CPU self, stepInfo info):
    self.Y = self.Read(self.address)
    self.setZN(self.Y)

# LSR - Logical Shift Right
cdef void lsr(CPU self, stepInfo info):
    if info.mode == modeAccumulator:
        self.C = self.A & 1
        self.A >>= 1
        self.setZN(self.A)
    else:
        value = self.Read(info.address)
        self.C = value & 1
        value >>= 1
        self.Write(info.address, value)
        self.setZN(value)

# NOP - No Operation
cdef void nop(CPU self, stepInfo info):
    pass

# ORA - Logical Inclusive OR
cdef void ora(CPU self, stepInfo info):
    self.A |= self.Read(info.address)
    self.setZN(self.A)

# PHA - Push Accumulator
cdef void pha(CPU self, stepInfo info):
    self.push(self.A)

# PHP - Push Processor Status
cdef void php(CPU self, stepInfo info):
    self.push(self.Flags() | 0x10)

# PLA - Pull Accumulator
cdef void pla(CPU self, stepInfo info):
    self.A = self.pull()
    self.setZN(self.A)

# PLP - Pull Processor Status
cdef void plp(CPU self, stepInfo info):
    self.SetFlags((self.pull() & 0xEF) | 0x20)

# ROL - Rotate Left
cdef void rol(CPU self, stepInfo info):
    if info.mode == modeAccumulator:
        c = self.C
        self.C = (self.A >> 7) & 1
        self.A = ((self.A << 1) & 0xFF) | c
        self.setZN(self.A)
    else:
        c = self.C
        value = self.Read(info.address)
        self.C = (value >> 7) & 1
        value = ((value << 1) & 0xFF) | c
        self.Write(info.address, value)
        self.setZN(value)

# ROR - Rotate Right
cdef void ror(CPU self, stepInfo info):
    if info.mode == modeAccumulator:
        c = self.C
        self.C = (self.A & 1)
        self.A = (self.A >> 1) | ((c << 7) & 0xFF)
        self.setZN(self.A)
    else:
        c = self.C
        value = self.Read(info.address)
        self.C = value & 1
        value = (value >> 1) | ((c << 7) & 0xFF)
        self.Write(info.address, value)
        self.setZN(value)

# RTI - Return from Interrupt
cdef void rti(CPU self, stepInfo info):
    self.SetFlags((self.pull() & 0xEF) | 0x20)
    self.PC = self.pull16()

# RTS - Return from Subroutine
cdef void rts(CPU self, stepInfo info):
    self.PC = (self.pull16() + 1)

# SBC - Subtract with Carry
cdef void sbc(CPU self, stepInfo info):
    a = self.A
    b = self.Read(info.address)
    c = self.C
    d = a - b - (1 - c)
    self.A = d & 0xFF
    self.setZN(self.A)
    self.C = 1 if d >= 0 else 0
    self.V = 1 if (a ^ b) & 0x80 != 0 and (a * self.A) & 0x80 != 0 else 0

# SEC - Set Carry Flag
cdef void sec(CPU self, stepInfo info):
    self.C = 1

# SED - Set Decimal Flag
cdef void sed(CPU self, stepInfo info):
    self.D = 1

# SEI - Set Interrupt Disable
cdef void sei(CPU self, stepInfo info):
    self.I = 1
    
# STA - Store Accumulator
cdef void sta(CPU self, stepInfo info):
    self.Write(info.address, self.A)

# STX - Store X Register
cdef void stx(CPU self, stepInfo info):
    self.Write(info.address, self.X)

# STY - Store Y Register
cdef void sty(CPU self, stepInfo info):
    self.Write(info.address, self.Y)

# TAX - Transfer Accumulator to X
cdef void tax(CPU self, stepInfo info):
    self.X = self.A
    self.setZN(self.X)

# TAY - Transfer Accumulator to Y
cdef void tay(CPU self, stepInfo info):
    self.Y = self.A
    self.setZN(self.Y)

# TSX - Transfer Stack Pointer to X
cdef void tsx(CPU self, stepInfo info):
    self.X = self.SP
    self.setZN(self.X)

# TXA - Transfer X to Accumulator
cdef void txa(CPU self, stepInfo info):
    self.A = self.X
    self.setZN(self.A)

# TXS - Transfer X to Stack Pointer
cdef void txs(CPU self, stepInfo info):
    self.SP = self.X

# TYA - Transfer Y to Accumulator
cdef void tya(CPU self, stepInfo info):
    self.A = self.Y
    self.setZN(self.A)

# illegal opcodes below
cdef void ahx(CPU self, stepInfo info):
    pass
cdef void alr(CPU self, stepInfo info):
    pass
cdef void anc(CPU self, stepInfo info):
    pass
cdef void arr(CPU self, stepInfo info):
    pass
cdef void axs(CPU self, stepInfo info):
    pass
cdef void dcp(CPU self, stepInfo info):
    pass
cdef void isc(CPU self, stepInfo info):
    pass
cdef void kil(CPU self, stepInfo info):
    pass
cdef void las(CPU self, stepInfo info):
    pass
cdef void lax(CPU self, stepInfo info):
    pass
cdef void rla(CPU self, stepInfo info):
    pass
cdef void rra(CPU self, stepInfo info):
    pass
cdef void sax(CPU self, stepInfo info):
    pass
cdef void shx(CPU self, stepInfo info):
    pass
cdef void shy(CPU self, stepInfo info):
    pass
cdef void slo(CPU self, stepInfo info):
    pass
cdef void sre(CPU self, stepInfo info):
    pass
cdef void tas(CPU self, stepInfo info):
    pass
cdef void xaa(CPU self, stepInfo info):
    pass

cpu_op_table = [
    brk, ora, kil, slo, nop, ora, asl, slo,
    php, ora, asl, anc, nop, ora, asl, slo,
    bpl, ora, kil, slo, nop, ora, asl, slo,
    clc, ora, nop, slo, nop, ora, asl, slo,
    jsr, _and, kil, rla, bit, _and, rol, rla,
    plp, _and, rol, anc, bit, _and, rol, rla,
    bmi, _and, kil, rla, nop, _and, rol, rla,
    sec, _and, nop, rla, nop, _and, rol, rla,
    rti, eor, kil, sre, nop, eor, lsr, sre,
    pha, eor, lsr, alr, jmp, eor, lsr, sre,
    bvc, eor, kil, sre, nop, eor, lsr, sre,
    cli, eor, nop, sre, nop, eor, lsr, sre,
    rts, adc, kil, rra, nop, adc, ror, rra,
    pla, adc, ror, arr, jmp, adc, ror, rra,
    bvs, adc, kil, rra, nop, adc, ror, rra,
    sei, adc, nop, rra, nop, adc, ror, rra,
    nop, sta, nop, sax, sty, sta, stx, sax,
    dey, nop, txa, xaa, sty, sta, stx, sax,
    bcc, sta, kil, ahx, sty, sta, stx, sax,
    tya, sta, txs, tas, shy, sta, shx, ahx,
    ldy, lda, ldx, lax, ldy, lda, ldx, lax,
    tay, lda, tax, lax, ldy, lda, ldx, lax,
    bcs, lda, kil, lax, ldy, lda, ldx, lax,
    clv, lda, tsx, las, ldy, lda, ldx, lax,
    cpy, _cmp, nop, dcp, cpy, _cmp, dec, dcp,
    iny, _cmp, dex, axs, cpy, _cmp, dec, dcp,
    bne, _cmp, kil, dcp, nop, _cmp, dec, dcp,
    cld, _cmp, nop, dcp, nop, _cmp, dec, dcp,
    cpx, sbc, nop, isc, cpx, sbc, inc, isc,
    inx, sbc, nop, sbc, cpx, sbc, inc, isc,
    beq, sbc, kil, isc, nop, sbc, inc, isc,
    sed, sbc, nop, isc, nop, sbc, inc, isc,
]

cpu_mode_table = [
        cpu_mode_empty,
        modeAbsoluteFunc,
        modeAbsoluteXFunc,
        modeAbsoluteYFunc,
        modeAccumulatorFunc,
        modeImmediateFunc,
        modeImpliedFunc,
        modeIndexedIndirectFunc,
        modeIndirectFunc,
        modeIndirectIndexedFunc,
        modeRelativeFunc,
        modeZeroPageFunc,
        modeZeroPageXFunc,
        modeZeroPageYFunc
]
