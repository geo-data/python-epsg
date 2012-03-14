#!/usr/bin/env python

from distutils.core import setup
from epsg import __version__

setup(name='python-epsg',
      version=__version__,
      description='An interface to the EPSG projection database at http://www.epsg-registry.org',
      author='Homme Zwaagstra',
      author_email='hrz@geodata.soton.ac.uk',
      url='http://github.com/geo-data/python-epsg',
      license='BSD',
      packages=['epsg']
     )
