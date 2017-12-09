# cython: profile=True
from OpenGL.GL import *
from defines import *
import glfw
import ctypes
from controller import *
import array
from itertools import chain
include "view.pyx"

cdef class GameView(View):
    cdef object director, console, title, _hash, texture, record, frames
    def __init__(self, director, console, title, _hash):
        self.director = director
        self.console = console
        self.title = title
        self._hash = _hash
        self.texture = self.createTexture()
        self.record = False
        self.frames = None
    cpdef void Enter(self):
        glClearColor(0, 0, 0, 1)
        glEnable(GL_TEXTURE_2D)
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

    cpdef void Exit(self):
        pass

    cpdef void Update(self, t, dt):
        #if dt > 1:
        #    dt = 0
        dt = 0.01
        window = self.director.window
        console = self.console
        # Joystick and key and controller
        self.updateControllers(window, console)
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
        #shape = im.shape
        #glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, shape[1], shape[0], 0, GL_RGB, GL_UNSIGNED_BYTE, im)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 256, 240, 0, GL_RGB, GL_UNSIGNED_BYTE, bytes(im))

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

    def updateControllers(self, window, console):
        turbo = (console.PPU.Frame % 6) < 3
        k1 = self.readKeys(window, turbo)
        j1 = self.readJoystick(glfw.JOYSTICK_1, turbo)
        j2 = self.readJoystick(glfw.JOYSTICK_2, turbo)
        console.SetButtons1(self.combineButtons(k1, j1))
        console.SetButtons2(j2)

    def readKey(self, window, key):
        return glfw.get_key(window, key) == glfw.PRESS

    def readKeys(self, window, turbo):
        result = [False for _ in range(8)]
        result[ButtonA] = self.readKey(window, glfw.KEY_Z) or (turbo and self.readKey(window, glfw.KEY_A))
        result[ButtonB] = self.readKey(window, glfw.KEY_X) or (turbo and self.readKey(window, glfw.KEY_S))
        result[ButtonSelect] = self.readKey(window, glfw.KEY_RIGHT_SHIFT)
        result[ButtonStart] = self.readKey(window, glfw.KEY_ENTER)
        result[ButtonUp] = self.readKey(window, glfw.KEY_UP)
        result[ButtonDown] = self.readKey(window, glfw.KEY_DOWN)
        result[ButtonLeft] = self.readKey(window, glfw.KEY_LEFT)
        result[ButtonRight] = self.readKey(window, glfw.KEY_RIGHT)
        return result

    def readJoystick(self, joy, turbo):
        result = [False for _ in range(8)]
        return result

    def combineButtons(self, a, b):
        result = [False for _ in range(8)]
        for i in range(8):
            result[i] = a[i] or b[i]
        return result

