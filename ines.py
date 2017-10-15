import struct
from numpy import *
from cartridge import *
iNESFileMagic = b'NES\x1a'

def LoadNESFile(path):
    print ("Loading %s" % path)
    fin = open(path, "rb")
    Magic, NumPRG, NumCHR, Control1, Control2, NumRAM, _ = struct.unpack("<4sccccc7s", fin.read(16))
    if Magic != iNESFileMagic:
        raise RuntimeError("Invalid .nes File")

    NumPRG = byte(ord(NumPRG))
    NumCHR = byte(ord(NumCHR))
    Control1 = byte(ord(Control1))
    Control2 = byte(ord(Control2))
    NumRAM = byte(ord(NumRAM))

    mapper1 = (Control1 >> byte(4))
    mapper2 = (Control2 >> byte(4))
    mapper = mapper1 | (mapper2 << byte(4))

    mirror1 = Control1 & byte(1) 
    mirror2 = (Control1 >> byte(3)) & byte(1)
    mirror = mirror1 | (mirror2 << byte(1))

    battery = (Control1 >> byte(1)) & byte(1)

	# read trainer if present (unused)
    if Control1 & byte(4) == byte(4):
        fin.read(512)

	# read prg-rom bank(s)
    prg = fromstring(fin.read(16384), byte)
	# read chr-rom bank(s)
    _chr = fromstring(fin.read(8192), byte)

    if NumCHR == 0:
        _chr = zeros(8192).astype(byte)
    return Cartridge(prg, _chr, mapper, mirror, battery), None
