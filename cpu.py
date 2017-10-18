from defines import *
from memory import *
import cpu_func as CPU_FUNC

class stepInfo:
    def __init__(self, address = None, pc = None, mode = None):
        self.address = address
        self.pc = pc
        self.mode = mode 

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
        self.table = [stepInfo() for _ in range(256)] 
        self.address = 0
        self.pageCrossed = False 
        self.console = console

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

    def PrintInstruction(cpu):
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


    def Reset(self):
        self.PC = self.Read16(0xFFFC)
        self.SP = 0xFD
        self.SetFlags(0x24)

    # pagesDiffer returns true if the two addresses reference different pages
    def pagesDiffer(self, a, b):
        return (a & 0xFF00) != (b & 0xFF00)

    # addBranchCycles adds a cycle for taking a branch and adds another cycle
    # if the branch jumps to a new page
    def addBranchCycles(self, info):
        self.Cycles += 1 
        if self.pagesDiffer(info.pc, info.address):
            self.Cycles += 1

    def compare(self, a, b):
        self.setZN((a - b) & 0xFF)
        self.C = 1 if a >= b else 0
    
    def Read(self, address):
        if address < 0x2000:
            return self.console.RAM[address % 0x0800]
        elif address < 0x4000:
            return self.console.PPU.readRegister((0x2000 + address % 8) & 0xFFFF)
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

    def Write(self, address, value):
        if address < 0x2000:
            self.console.RAM[address % 0x0800] = value
        elif address < 0x4000:
            self.console.PPU.writeRegister((0x2000 + address % 8) & 0xFFFF, value)
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
    def Read16(self, address):
        lo = self.Read(address)
        hi = self.Read((address + 1) & 0xFFFF)
        return (hi << 8) | lo

    # read16bug emulates a 6502 bug that caused the low uint8 to wrap without
    def read16bug(self, address):
        a = address
        b = (a & 0xFF00) | ((a + 1) & 0xFF)
        lo = self.Read(a)
        hi = self.Read(b)
        return (hi << 8) | lo

    # push pushes a uint8 onto the stack
    def push(self, value):
        self.Write(0x100 | self.SP, value)
        self.SP = (self.SP - 1) & 0xFF 

    # pull pops a uint8 from the stack
    def pull(self):
        self.SP = (self.SP + 1) & 0xFF 
        return self.Read(0x100 | self.SP)

    # push16 pushes two uint8s onto the stack
    def push16(self, value):
        hi = value >> 8
        lo = value & 0xFF
        self.push(hi)
        self.push(lo)

    # pull16 pops two uint8s from the stack
    def pull16(self):
        lo = self.pull()
        hi = self.pull()
        return (hi << 8) | lo

    def Step(self):
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

        CPU.MODES_FUNC[mode](self)

        self.PrintInstruction()
        self.PC += instructionSizes[opcode]
        self.Cycles += instructionCycles[opcode]

        if self.pageCrossed:
            self.Cycles += instructionPageCycles[opcode]

        info = stepInfo(self.address, self.PC, mode)
        self.table[opcode](info)

        '''
        s = ""
        for i in range(16):
            s += "%.2X " % self.Read(self.PC + uint16(i))
        print (self.Cycles, cycles, "%.4X" % self.PC, "%.2X" % opcode, mode, s)
        '''
        return self.Cycles - cycles
    
    # NMI - Non-Maskable Interrupt
    def nmi(self):
        self.push16(self.PC)
        self.php(None)
        self.PC = self.Read16(0xFFFA)
        self.I = 1
        self.Cycles += 7 

    # IRQ - IRQ Interrupt
    def irq(self):
        self.push16(self.PC)
        self.php(None)
        self.PC = self.Read16(0xFFFE)
        self.I = 1
        self.Cycles += 7

    def Flags(self):
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
    def SetFlags(self, flags):
        self.C = (flags >> 0) & 1
        self.Z = (flags >> 1) & 1
        self.I = (flags >> 2) & 1
        self.D = (flags >> 3) & 1
        self.B = (flags >> 4) & 1
        self.U = (flags >> 5) & 1
        self.V = (flags >> 6) & 1
        self.N = (flags >> 7) & 1

    # setZ sets the zero flag if the argument is zero
    def setZ(self, value):
        self.Z = 1 if value == 0 else 0

    # setN sets the negative flag if the argument is negative (high bit is set)
    def setN(self, value):
        self.N = 1 if value & 0x80 != 0 else 0

    # setZN sets the zero flag and the negative flag
    def setZN(self, value):
        self.setZ(value)
        self.setN(value)

    # triggerNMI causes a non-maskable interrupt to occur on the next cycle
    def triggerNMI(self):
        self.interrupt = interruptNMI

    # triggerIRQ causes an IRQ interrupt to occur on the next cycle
    def triggerIRQ(self):
        if self.I == 0:
            self.interrupt = interruptIRQ

    # ADC - Add with Carry
    def adc(self, info):
        a = self.A
        b = self.Read(info.address)
        c = self.C
        self.A = (a + b + c) & 0xFF
        self.setZN(self.A)
        self.C = 1 if a + b + c > 0xFF else 0
        self.V = 1 if (a ^ b) & 0x80 == 0 and (a ^ self.A) & 0x80 != 0 else 0

    # AND - Logical AND
    def _and(self, info):
        self.A = (self.A & self.Read(info.address))
        self.setZN(self.A)

    # ASL - Arithmetic Shift Left
    def asl(self, info):
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
        if self.Z != 0:
            self.PC = info.address
            self.addBranchCycles(info)

    # BIT - Bit Test
    def bit(self, info):
        value = self.Read(info.address)
        self.V = (value >> 6) & 1
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
        self.C = 0

    # CLD - Clear Decimal Mode
    def cld(self, info):
        self.D = 0

    # CLI - Clear Interrupt Disable
    def cli(self, info):
        self.I = 0

    # CLV - Clear Overflow Flag
    def clv(self, info):
        self.V = 0

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
        value = (self.Read(info.address) - 1) & 0xFF 
        self.Write(info.address, value)
        self.setZN(value)

    # DEX - Decrement X Register
    def dex(self, info):
        self.X = (self.X - 1) & 0xFF
        self.setZN(self.X)

    # DEY - Decrement Y Register
    def dey(self, info):
        self.Y = (self.Y - 1) & 0xFF
        self.setZN(self.Y)

    # EOR - Exclusive OR
    def eor(self, info):
        self.A = self.A ^ self.Read(info.address)
        self.setZN(self.A)

    # INC - Increment Memory
    def inc(self, info):
        value = (self.Read(info.address) + 1) & 0xFF
        self.Write(info.address, value)
        self.setZN(value)

    # INX - Increment X Register
    def inx(self, info):
        self.X = (self.X + 1) & 0xFF
        self.setZN(self.X)

    # INY - Increment Y Register
    def iny(self, info):
        self.Y = (self.Y + 1) & 0xFF
        self.setZN(self.Y)

    # JMP - Jump
    def jmp(self, info):
        self.PC = info.address

    # JSR - Jump to Subroutine
    def jsr(self, info):
        self.push16((self.PC - 1) & 0xFFFF)
        self.PC = info.address

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
            self.C = self.A & 1
            self.A >>= 1
            self.setZN(self.A)
        else:
            value = slef.Read(info.address)
            self.C = value & 1
            value >>= 1
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
    def ror(self, info):
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
    def rti(self, info):
        self.SetFlags((self.pull() & 0xEF) | 0x20)
        self.PC = self.pull16()

    # RTS - Return from Subroutine
    def rts(self, info):
        self.PC = (self.pull16() + 1) & 0xFFFF

    # SBC - Subtract with Carry
    def sbc(self, info):
        a = self.A
        b = self.Read(info.address)
        c = self.C
        d = a - b - (1 - c)
        self.A = d & 0xFF
        self.setZN(self.A)
        self.C = 1 if d >= 0 else 0
        self.V = 1 if (a ^ b) & 0x80 != 0 and (a * self.A) & 0x80 != 0 else 0

    # SEC - Set Carry Flag
    def sec(self, info):
        self.C = 1

    # SED - Set Decimal Flag
    def sed(self, info):
        self.D = 1

    # SEI - Set Interrupt Disable
    def sei(self, info):
        self.I = 1
        
    # STA - Store Accumulator
    def sta(self, info):
        self.Write(info.address, self.A)

    # STX - Store X Register
    def stx(self, info):
        self.Write(info.address, self.X)

    # STY - Store Y Register
    def sty(self, info):
        self.Write(info.address, self.Y)

    # TAX - Transfer Accumulator to X
    def tax(self, info):
        self.X = self.A
        self.setZN(self.X)

    # TAY - Transfer Accumulator to Y
    def tay(self, info):
        self.Y = self.A
        self.setZN(self.Y)

    # TSX - Transfer Stack Pointer to X
    def tsx(self, info):
        self.X = self.SP
        self.setZN(self.X)

    # TXA - Transfer X to Accumulator
    def txa(self, info):
        self.A = self.X
        self.setZN(self.A)

    # TXS - Transfer X to Stack Pointer
    def txs(self, info):
        self.SP = self.X

    # TYA - Transfer Y to Accumulator
    def tya(self, info):
        self.A = self.Y
        self.setZN(self.A)

    # illegal opcodes below
    def ahx(self, info):
        pass
    def alr(self, info):
        pass
    def anc(self, info):
        pass
    def arr(self, info):
        pass
    def axs(self, info):
        pass
    def dcp(self, info):
        pass
    def isc(self, info):
        pass
    def kil(self, info):
        pass
    def las(self, info):
        pass
    def lax(self, info):
        pass
    def rla(self, info):
        pass
    def rra(self, info):
        pass
    def sax(self, info):
        pass
    def shx(self, info):
        pass
    def shy(self, info):
        pass
    def slo(self, info):
        pass
    def sre(self, info):
        pass
    def tas(self, info):
        pass
    def xaa(self, info):
        pass


def NewCPU(console):
    cpu = CPU(console)
    cpu.createTable()
    cpu.Reset()
    return cpu

