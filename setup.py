from distutils.core import setup
from Cython.Build import cythonize


setup(
    ext_modules = cythonize(["ppu.pyx", "cpu.pyx", "apu.pyx", "mapper1.pyx", "mapper2.pyx", "memory.pyx", "gameview.pyx", "view.pyx"],  compiler_directives={'profile': False})
)
