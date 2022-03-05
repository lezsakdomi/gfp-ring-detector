from setuptools import setup, Extension
import numpy
from Cython.Build import cythonize

custom_algo = Extension(
    'custom_algo',
    sources=['custom_algo.pyx'],
    include_dirs=[numpy.get_include()]
)

setup(
    name='gfp-ring-detector',
    version='2.0.3',
    ext_modules=cythonize([custom_algo], language_level=3, annotate=True, gdb_debug=True),
    url='https://github.com/lezsakdomi/gfp-ring-detector',
    author='Domonkos Lezsák',
    author_email='lezsakdomi@student.elte.hu',
    description='Fluorescent microscopy image analyzer'
)

