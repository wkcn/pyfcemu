from util import *
from console import *
import time
from gameview import *

class View:
    def Enter(self):
        pass
    def Exit(self):
        pass
    def Update(self, t, dt):
        pass

class Director:
    def __init__(self):
        self.window = None
        self.audio = None
        self.view = View()
        self.menuView = View()
    def Start(self, paths):
        if len(paths) == 1:
            self.PlayGame(paths[0])
        else:
            # TODO
            pass
    def PlayGame(self, path):
        hash_code, err = hashFile(path)
        console, err = NewConsole(path)
        self.SetView(NewGameView(self, console, path, hash_code))
    def SetView(self, view):
        if view is not None:
            self.view.Exit()
        self.view = view
        if self.view is not None:
            self.view.Enter()
        self.timestamp = time.time()

def NewDirector(window, audio):
    director = Director()
    director.window = window
    director.audio = audio
    return director
