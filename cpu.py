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
        c = self
        c.table = [
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
        if self.stall.value > 0:
            self.stall.value -= 1
            return 1

        cycles = self.Cycles

        if self.interrupt == interruptNMI:
            self.nmi()
        elif self.iterrupt == interruptIRQ:
            self.irq()
        self.interrupt = interruptNone

        opCode = self.Read(self.PC)
        mode = instructionModes[opcode]

        address = c_ushort()
        pageCrossed = False 

        if mode == modeAbsolute:
            address = self.Read16(self.PC.value + 1)
        elif mode == modeAbsoluteX:
            address = c_ushort(self.Read16(self.PC.value + 1).value + self.X.value)

        






def NewCPU(console):
    cpu = CPU(console)
    cpu.createTable()
    cpu.Reset()
    return cpu
