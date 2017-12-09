from util import *
from console import *
import glfw
from OpenGL.GL import *
from gameview import *

class Director:
    def __init__(self):
        self.window = None
        self.audio = None
        self.view = View() 
        self.menuView = View() 
    def Start(self, paths):
        if len(paths) == 1:
            self.PlayGame(paths[0])
            self.Run()
        else:
            # TODO
            print ("ERROR PATH")

    def Run(self):
        while not glfw.window_should_close(self.window):
            self.Step()
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        self.SetView(None)

    def PlayGame(self, path):
        hash_code, err = hashFile(path)
        console = Console(path) 
        self.SetView(GameView(self, console, path, hash_code))

    def SetView(self, view):
        if view is not None:
            self.view.Exit()
        self.view = view
        if self.view is not None:
            self.view.Enter()
        self.timestamp = glfw.get_time()

    def SetTitle(self, title):
        glfw.set_window_title(self.window, title)
    def Step(self):
        glClear(GL_COLOR_BUFFER_BIT)
        timestamp = glfw.get_time() 
        dt = timestamp - self.timestamp
        self.timestamp = timestamp
        if self.view is not None:
            self.view.Update(timestamp, dt)


def NewDirector(window, audio):
    director = Director()
    director.window = window
    director.audio = audio
    return director
