from defines import *
from memory import *
from numpy import *
import cpu_func as CPU_FUNC

class stepInfo:
    def __init__(self):
        self.address = uint16()
        self.pc = uint16()
        self.mode = byte()

class CPU:
    MODES_FUNC = {
            modeAbsolute: CPU_FUNC.modeAbsoluteFunc, 
            modeAbsoluteX: CPU_FUNC.modeAbsoluteXFunc, modeAbsoluteY: CPU_FUNC.modeAbsoluteYFunc, 
            modeAccumulator: CPU_FUNC.modeAccumulatorFunc,
            modeImmediate: CPU_FUNC.modeImmediateFunc,
            modeImplied: CPU_FUNC.modeImpliedFunc,
            modeIndexedIndirect: CPU_FUNC.modeIndexedIndirectFunc,
            modeIndirect: CPU_FUNC.modeIndirectFunc,
            modeIndirectIndexed: CPU_FUNC.modeIndirectIndexedFunc,
            modeRelative: CPU_FUNC.modeRelativeFunc,
            modeZeroPage: CPU_FUNC.modeZeroPageFunc,
            modeZeroPageX: CPU_FUNC.modeZeroPageX,
            modeZeroPageY: CPU_FUNC.modeZeroPageY
    }
    def __init__(self, console):
        self.Memory = Memory(console) # Memory Interface
        self.Cycles = uint64() # Number of Cycles
        self.PC = uint16() # Program Counter
        self.SP = byte() # Stack Pointer
        self.A = byte() # Accumulator
        self.X = byte() # X register
        self.Y = byte() # Y register
        self.C = byte() # Carry Flag
        self.Z = byte() # Zero Flag
        self.I = byte() # Interrupt Disable Flag 
        self.D = byte() # Decimal Mode Flag 
        self.B = byte() # Break Command Flag 
        self.U = byte() # Unused Flag 
        self.V = byte() # Overflow Flag 
        self.N = byte() # Negative Flag 
        self.interrupt = byte() # interrupt type to perform 
        self.stall = 0 # Number of Cycles to Stall
        self.table = [stepInfo() for _ in range(256)] 
        self.address = uint16()
        self.pageCrossed = False 
    def createTable(self):
        c = self
        self.table = [
		c.brk, c.ora, c.kil, c.slo, c.nop, c.ora, c.asl, c.slo,
		c.php, c.ora, c.asl, c.anc, c.nop, c.ora, c.asl, c.slo,
		c.bpl, c.ora, c.kil, c.slo, c.nop, c.ora, c.asl, c.slo,
		c.clc, c.ora, c.nop, c.slo, c.nop, c.ora, c.asl, c.slo,
		c.jsr, c._and, c.kil, c.rla, c.bit, c._and, c.rol, c.rla,
		c.plp, c._and, c.rol, c.anc, c.bit, c._and, c.rol, c.rla,
		c.bmi, c._and, c.kil, c.rla, c.nop, c._and, c.rol, c.rla,
		c.sec, c._and, c.nop, c.rla, c.nop, c._and, c.rol, c.rla,
		c.rti, c.eor, c.kil, c.sre, c.nop, c.eor, c.lsr, c.sre,
		c.pha, c.eor, c.lsr, c.alr, c.jmp, c.eor, c.lsr, c.sre,
		c.bvc, c.eor, c.kil, c.sre, c.nop, c.eor, c.lsr, c.sre,
		c.cli, c.eor, c.nop, c.sre, c.nop, c.eor, c.lsr, c.sre,
		c.rts, c.adc, c.kil, c.rra, c.nop, c.adc, c.ror, c.rra,
		c.pla, c.adc, c.ror, c.arr, c.jmp, c.adc, c.ror, c.rra,
		c.bvs, c.adc, c.kil, c.rra, c.nop, c.adc, c.ror, c.rra,
		c.sei, c.adc, c.nop, c.rra, c.nop, c.adc, c.ror, c.rra,
		c.nop, c.sta, c.nop, c.sax, c.sty, c.sta, c.stx, c.sax,
		c.dey, c.nop, c.txa, c.xaa, c.sty, c.sta, c.stx, c.sax,
		c.bcc, c.sta, c.kil, c.ahx, c.sty, c.sta, c.stx, c.sax,
		c.tya, c.sta, c.txs, c.tas, c.shy, c.sta, c.shx, c.ahx,
		c.ldy, c.lda, c.ldx, c.lax, c.ldy, c.lda, c.ldx, c.lax,
		c.tay, c.lda, c.tax, c.lax, c.ldy, c.lda, c.ldx, c.lax,
		c.bcs, c.lda, c.kil, c.lax, c.ldy, c.lda, c.ldx, c.lax,
		c.clv, c.lda, c.tsx, c.las, c.ldy, c.lda, c.ldx, c.lax,
		c.cpy, c.cmp, c.nop, c.dcp, c.cpy, c.cmp, c.dec, c.dcp,
		c.iny, c.cmp, c.dex, c.axs, c.cpy, c.cmp, c.dec, c.dcp,
		c.bne, c.cmp, c.kil, c.dcp, c.nop, c.cmp, c.dec, c.dcp,
		c.cld, c.cmp, c.nop, c.dcp, c.nop, c.cmp, c.dec, c.dcp,
		c.cpx, c.sbc, c.nop, c.isc, c.cpx, c.sbc, c.inc, c.isc,
		c.inx, c.sbc, c.nop, c.sbc, c.cpx, c.sbc, c.inc, c.isc,
		c.beq, c.sbc, c.kil, c.isc, c.nop, c.sbc, c.inc, c.isc,
		c.sed, c.sbc, c.nop, c.isc, c.nop, c.sbc, c.inc, c.isc,
	]
    def Reset(self):
        pass
    def Step(self):
        if self.stall > 0:
            self.stall -= 1
            return 1

        cycles = self.Cycles

        if self.interrupt == interruptNMI:
            self.nmi()
        elif self.iterrupt == interruptIRQ:
            self.irq()

        self.interrupt = interruptNone

        opcode = self.Read(self.PC)
        mode = instructionModes[opcode]

        MODES_FUNC[mode](self)

        self.PC += instructionSizes[opcode]
        self.Cycles += instructionCycles[opcode]

        if self.pageCrossed:
            self.Cycles += instructionPageCycles[opcode]

        info = stepInfo(address, self.PC, mode)
        self.table[opcode](info)

        return cpu.Cycles - cycles

    def Flags(self):
        flags = byte(0)
        flags |= (self.C << byte(0))
        flags |= (self.Z << byte(1))
        flags |= (self.I << byte(2))
        flags |= (self.D << byte(3))
        flags |= (self.B << byte(4))
        flags |= (self.U << byte(5))
        flags |= (self.V << byte(6))
        flags |= (self.N << byte(7))

        return flags

    def SetFlags(self, flags):
        self.C = (flags >> byte(0)) & byte(1)
        self.Z = (flags >> byte(1)) & byte(1)
        self.I = (flags >> byte(2)) & byte(1)
        self.D = (flags >> byte(3)) & byte(1)
        self.B = (flags >> byte(4)) & byte(1)
        self.U = (flags >> byte(5)) & byte(1)
        self.V = (flags >> byte(6)) & byte(1)
        self.N = (flags >> byte(7)) & byte(1)

    # ADC - Add with Carry
    def adc(self, info):
        a = self.A
        b = self.Read(info.address)
        c = self.C
        self.A = a + b + c
        self.setZN(self.A)
        if a + b + c > 0xFF:
            self.C = byte(1)
        else:
            self.C = byte(0)
        if (a ^ b) & 0x80 == 0 and (a ^ self.A) & 0x80 != 0:
            self.V = byte(1)
        else:
            self.V = byte(0)

    # AND - Logical AND
    def _and(self, info):
        self.A = (self.A & self.Read(info.address))
        self.setZN(self.A)

    # ASL - Arithmetic Shift Left
    def asl(self, info):
        if info.mode == modeAccumulator:
            self.C = (self.A >> byte(7)) & byte(1)
            self.A <<= byte(1)
            self.setZN(self.A)
        else:
            value = self.Read(info.address)
            self.C = (value >> byte(7)) & 1
            value <<= byte(1)
            self.Write(info.address, value)
            self.setZN(value)

    # BCC - Branch if Carry Clear
    def bcc(self, info):
        if self.C == 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # BCS - Branch if Carry Set
    def bcs(self, info):
        if self.C != 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # BEQ - Branch if Equal
    def beq(self, info):
        if self.Z == 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # BIT - Bit Test
    def bit(self, info):
        value = self.Read(info.address)
        self.V = (value >> byte(6)) & byte(1)
        self.setZ(value & self.A)
        self.setN(value)
        
    # BMI - Branch if Minus
    def bmi(self, info):
        if self.N != 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # BNE - Branch if Not Equal
    def bne(self, info):
        if self.Z == 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # BPL - Branch if Positive
    def bpl(self, info):
        if self.N == 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # BRK - Force Interrupt
    def brk(self, info):
        self.push16(self.PC)
        self.php(info)
        self.sei(info)
        self.PC = self.Read16(0xFFFE)
    
    # BVC - Branch if Overflow Clear
    def bvc(self, info):
        if self.V == 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # BVS - Branch if Overflow Set
    def bvs(self, info):
        if self.V != 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # CLC - Clear Carray Flag
    def clc(self, info):
        self.C = byte(0)

    # CLD - Clear Decimal Mode
    def cld(self, info):
        self.D = byte(0)

    # CLI - Clear Interrupt Disable
    def cli(self, info):
        self.I = byte(0)

    # CLV - Clear Overflow Flag
    def clv(self, info):
        self.V = byte(0)

    # CMP - Compare
    def cmp(self, info):
        value = self.Read(info.address)
        self.compare(self.A, value)

    # CPX - Compare X Register
    def cpx(self, info):
        value = self.Read(info.address)
        self.compare(self.X, value)

    # CPY - Compare Y Register
    def cpy(self, info):
        value = self.Read(info.address)
        self.compare(self.Y, value)

    # DEC - Decrement Memory
    def dec(self, info):
        value = self.Read(info.address) - byte(1)
        self.Write(info.address, value)
        self.setZN(value)

    # DEX - Decrement X Register
    def dex(self, info):
        self.X -= byte(1)
        self.setZN(self.X)

    # DEY - Decrement Y Register
    def dey(self, info):
        self.Y -= byte(1)
        self.setZN(self.Y)

    # EOR - Exclusive OR
    def eor(self, info):
        self.A = self.A & self.Read(info.address)
        self.setZN(self.A)

    # INC - Increment Memory
    def inc(self, info):
        value = self.Read(info.address) + byte(1)
        self.Write(info.address, value)
        self.setZN(value)

    # INX - Increment X Register
    def inx(self, info):
        self.X += byte(1)
        self.setZN(self.X)

    # INY - Increment Y Register
    def iny(self, info):
        self.Y += byte(1)
        self.setZN(self.Y)

    # JMP - Jump
    def jmp(self, info):
        self.PC = info.address

    # JSR - Jump to Subroutine
    def jsr(self, info):
        self.push16(self.PC - uint16(1))

    # LDA - Load Accumulator
    def lda(self, info):
        self.A = self.Read(self.address)
        self.setZN(self.A)

    # LDX - Load X Register
    def ldx(self, info):
        self.X = self.Read(self.address)
        self.setZN(self.X)

    # LDY - Load Y Register
    def ldy(self, info):
        self.Y = self.Read(self.address)
        self.setZN(self.Y)

    # LSR - Logical Shift Right
    def lsr(self, info):
        if info.mode == modeAccumulator:
            self.C = self.A & byte(1)
            self.A >>= byte(1)
            self.setZN(self.A)
        else:
            value = slef.Read(info.address)
            self.C = value & byte(1)
            value >>= byte(1)
            self.Write(info.address, value)
            self.setZN(value)

    # NOP - No Operation
    def nop(self, info):
        pass

    # ORA - Logical Inclusive OR
    def ora(self, info):
        self.A |= self.Read(info.address)
        self.setZN(self.A)

    # PHA - Push Accumulator
    def pha(self, info):
        self.push(self.A)

    # PHP - Push Processor Status
    def php(self, info):
        self.push(self.Flags() | 0x10)

    # PLA - Pull Accumulator
    def pla(self, info):
        self.A = self.pull()
        self.setZN(self.A)

    # PLP - Pull Processor Status
    def plp(self, info):
        self.SetFlags((self.pull() & 0xEF) | 0x20)

    # ROL - Rotate Left
    def rol(self, info):
        if info.mode == modeAccumulator:
            c = self.C
            self.C = (self.A >> byte(7)) & byte(1)
            self.A = (self.A << byte(1)) | c
            self.setZN(self.A)
        else:
            c = self.C
            value = self.Read(info.address)
            self.C = (value >> byte(7)) & byte(1)
            value = (value << byte(1)) | c
            self.Write(info.address, value)
            self.setZN(value)

    # ROR - Rotate Right
    def ror(self, info):
        if info.mode == modeAccumulator:
            c = self.C
            self.C = (self.A & byte(1))
            self.A = (self.A >> byte(1)) | (c << byte(7))
            self.setZN(self.A)
        else:
            c = self.C
            value = self.Read(info.address)
            self.C = value & byte(1)
            value = (value >> byte(1)) | (c << byte(7))
            self.Write(info.address, value)
            self.setZN(value)

def NewCPU(console):
    cpu = CPU(console)
    cpu.createTable()
    cpu.Reset()
    return cpu
