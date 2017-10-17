from numpy import *
class Controller:
    def __init__(self):
        self.buttons = zeros(8, dtype = bool) 
        self.index = 0 
        self.strobe = byte()

    def SetButtons(c, buttons):
        c.buttons = buttons

    def Read(c):
        value = byte(0)
        if c.index < 8 and c.buttons[c.index]:
            value = byte(1)
        c.index += 1
        if c.strobe&1 == 1:
            c.index = 0
        return value

    def Write(c, value):
        c.strobe = value
        if c.strobe&1 == 1:
            c.index = 0
