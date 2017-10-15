from OpenGL.GL import *
from view import *
import glfw

class GameView(View):
    def __init__(self, director, console, title, _hash):
        self.director = director
        self.console = console
        self.title = title
        self._hash = _hash
        self.texture = None
        self.record = False
        self.frames = None
    def Enter(self):
        glClearColor(0, 0, 0, 1)
        self.director.SetTitle(self.title)
        # self.console.SetAudioChannel(self.director.audio.channe)
        glfw.set_key_callback(self.director.window, self.onKey)
        #self.console.LoadState(savePath(self.hash))

        self.console.Reset()

        cartridge = self.console.Cartridge
        if cartridge.Battery != 0:
            sram = readSRAM(sramPath(self.hash))
            cartridge.SRAM = sram

    def Exit(self):
        pass

    def Update(self, t, dt):
        if dt > 1:
            dt = 0
        window = self.director.window
        console = self.console
        # Joystick and key and controller
        console.StepSeconds(dt)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        self.setTexture(console.Buffer())
        self.drawBuffer(window)
        glBindTexture(GL_TEXTURE_2D, 0)
        #if self.record:
        #    self.frames.append(self.frames, console.Buffer().copy())
    def onKey(self, window, key, scancode, action, mods):
        pass
