from director import *

def Run(paths):
    # TODO AUDIO INIT

    # Create Window

    window = None
    audio = None

    director = NewDirector(window, audio)
    director.Start(paths)
