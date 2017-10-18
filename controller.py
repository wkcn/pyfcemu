class Controller:
    def __init__(self):
        self.buttons = [False for _ in range(8)] 
        self.index = 0 
        self.strobe = 0 

    def SetButtons(c, buttons):
        c.buttons = buttons

    def Read(c):
        value = 0
        if c.index < 8 and c.buttons[c.index]:
            value = 1
        c.index += 1
        if c.strobe&1 == 1:
            c.index = 0
        return value

    def Write(c, value):
        c.strobe = value
        if c.strobe&1 == 1:
            c.index = 0
