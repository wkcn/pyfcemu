from director import *
import glfw
from OpenGL.GL import *

def Run(paths):
    # TODO AUDIO INIT

    # Create Window

    if not glfw.init():
        raise RuntimeError("GLFW Init Error")

    title = "PYFCSim"
    width  = 256
    height = 240
    scale  = 3

    window = glfw.create_window(width * scale, height * scale, title, None, None)
    glfw.make_context_current(window)

    audio = None


    director = NewDirector(window, audio)
    director.Start(paths)
    glEnable(GL_TEXTURE_2D)
