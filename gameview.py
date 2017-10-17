from OpenGL.GL import *
from numpy import *
from view import *
import glfw

class GameView(View):
    def __init__(self, director, console, title, _hash):
        self.director = director
        self.console = console
        self.title = title
        self._hash = _hash
        self.texture = self.createTexture()
        self.record = False
        self.frames = None
    def Enter(self):
        glClearColor(0, 0, 0, 1)
        self.director.SetTitle(self.title)
        #self.console.SetAudioChannel(self.director.audio.channel)
        # TODO
        self.console.SetAudioChannel(2)
        self.console.SetAudioSampleRate(44100)
        #self.console.SetAudioSampleRate(self.director.audio.sampleRate)
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

    def createTexture(self):
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture

    def setTexture(self, im):
        shape = im.shape
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, shape[0], shape[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, im)

    def drawBuffer(self, window):
        w, h = glfw.get_framebuffer_size(window)
        s1 = float(w) / 256
        s2 = float(h) / 240
        padding = 0.0
        f = 1.0 - padding
        if s1 >= s2:
            x = f * s2 / s1
            y = f
        else:
            x = f
            y = f * s1 / s2
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1)
        glVertex2f(-x, -y)
        glTexCoord2f(1, 1)
        glVertex2f(x, -y)
        glTexCoord2f(1, 0)
        glVertex2f(x, y)
        glTexCoord2f(0, 0)
        glVertex2f(-x, y)
        glEnd()
