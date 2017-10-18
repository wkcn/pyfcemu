import struct
from cartridge import *
iNESFileMagic = b'NES\x1a'

uint8 = int
ordc = lambda c:c if type(c) ==int else ord(c)
fromstring = lambda x, dtype : [dtype(ordc(c)) for c in x]

def LoadNESFile(path):
    print ("Loading %s" % path)
    fin = open(path, "rb")
    Magic, NumPRG, NumCHR, Control1, Control2, NumRAM, _ = struct.unpack("<4sccccc7s", fin.read(16))
    if Magic != iNESFileMagic:
        raise RuntimeError("Invalid .nes File")

    NumPRG = uint8(ord(NumPRG))
    NumCHR = uint8(ord(NumCHR))
    Control1 = uint8(ord(Control1))
    Control2 = uint8(ord(Control2))
    NumRAM = uint8(ord(NumRAM))

    mapper1 = (Control1 >> uint8(4))
    mapper2 = (Control2 >> uint8(4))
    mapper = mapper1 | (mapper2 << uint8(4))

    mirror1 = Control1 & uint8(1) 
    mirror2 = (Control1 >> uint8(3)) & uint8(1)
    mirror = mirror1 | (mirror2 << uint8(1))

    battery = (Control1 >> uint8(1)) & uint8(1)

	# read trainer if present (unused)
    if Control1 & uint8(4) == uint8(4):
        fin.read(512)

	# read prg-rom bank(s)
    prg = fromstring(fin.read(16384 * NumPRG), uint8)
	# read chr-rom bank(s)
    _chr = fromstring(fin.read(8192 * NumCHR), uint8)

    if NumCHR == 0:
        _chr = [0 for _ in range(8192)]
    return Cartridge(prg, _chr, mapper, mirror, battery), None
