from distutils.core import setup
from Cython.Build import cythonize


setup(
    ext_modules = cythonize(["ppu.pyx", "cpu.pyx", "cpu_func.pyx", "apu.pyx", "console.pyx", "mapper1.pyx", "mapper2.pyx", "memory.pyx"])
)
